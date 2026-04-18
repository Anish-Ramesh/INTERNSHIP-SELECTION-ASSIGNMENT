import os
import json
import re
import time
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage, 
    UserMessage, 
    AssistantMessage, 
    ToolMessage,
    CompletionsFinishReason,
    ChatCompletionsToolDefinition, 
    FunctionDefinition
)
from azure.core.credentials import AzureKeyCredential

from tools.search_docs import search_docs, tokenize
from tools.query_data import query_data
from tools.web_search import web_search
from utils.logger import TraceLogger
from agent.bonus_features import BONUS_A_SYSTEM_PROMPT, TelemetryTracker, reflect_on_answer

load_dotenv()

# Setup client
token = os.getenv("GITHUB_TOKEN")
if not token:
    raise ValueError("GITHUB_TOKEN missing in .env")

client = ChatCompletionsClient(
    endpoint="https://models.github.ai/inference",
    credential=AzureKeyCredential(token),
)
MODEL_NAME = "openai/gpt-4.1-mini" # or whatever you have mapped via proxy

# Strict Tool Definitions reflecting exactly our guardrails from Phase 1
TOOLS = [
     ChatCompletionsToolDefinition(
         function=FunctionDefinition(
             name="search_docs",
             description="Semantic search over unstructured documents (movie reviews). Use this for subjective opinions, themes, explanations, or questions about the plot. DO NOT Use for numerical data.",
             parameters={
                 "type": "object",
                 "properties": {
                     "query": {
                         "type": "string",
                         "description": "Natural language query string."
                     }
                 },
                 "required": ["query"]
             }
         )
     ),
     ChatCompletionsToolDefinition(
         function=FunctionDefinition(
             name="query_data",
             description="Query the structured financial / stats table for movies. The table contains the following columns: [title, year, genre, budget, opening_weekend, worldwide_gross, rotten_tomatoes_score]. Use this for numbers, rankings, or comparisons of these fields.",
             parameters={
                 "type": "object",
                 "properties": {
                     "sql_query": {
                         "type": "string",
                         "description": "A valid read-only SQLite query to run against the 'movies' table."
                     }
                 },
                 "required": ["sql_query"]
             }
         )
     ),
     ChatCompletionsToolDefinition(
         function=FunctionDefinition(
             name="web_search",
             description="Search the live web for recent information (e.g. recent awards news, director updates).",
             parameters={
                 "type": "object",
                 "properties": {
                     "query": {
                         "type": "string",
                         "description": "A short search query string (under 10 words)."
                     }
                 },
                 "required": ["query"]
             }
         )
     )
]

TOOL_MAP = {
    "search_docs": search_docs,
    "query_data": query_data,
    "web_search": web_search
}

CACHE_FILE = os.path.join(os.path.dirname(__file__), "response_cache.json")

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=4)
    except:
        pass

SYSTEM_PROMPT = """You are a SOTA Movie Reasoning Agent.
Your goal is to provide high-accuracy, grounded, and synthesized answers using movie data.

[DATABASE SCHEMA]
- title, year, genre, budget, opening_weekend, worldwide_gross, rotten_tomatoes_score.

[OUTPUT FORMAT]
[AGENT RESPONSE]
(A direct, cohesive, and grounded answer to the question. BE CONCISE. Avoid conversational filler.)

[CONFIDENCE]
- (Level: High/Medium/Low)

NEVER leak internal reasoning blocks (THOUGHT, PLAN) to the user.
""" + BONUS_A_SYSTEM_PROMPT

# SOTA Deduplication Stop Words
AGENT_STOP_WORDS = {
    "movie", "movies", "film", "films", "search", "find", "get", "show", "series", "info", 
    "information", "details", "data", "list", "identify", "tell", "check", "looking"
}

def clean_final_answer(text: str) -> str:
    """Strip internal reasoning blocks (STRATEGIC BREAKDOWN, THOUGHT, PLAN, etc.) from the final response."""
    # Remove STRATEGIC BREAKDOWN:, THOUGHT:, PLAN:
    text = re.sub(r"(?i)STRATEGIC BREAKDOWN:.*?(?=THOUGHT:|PLAN:|\[AGENT RESPONSE\]|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"(?i)THOUGHT:.*?(?=PLAN:|\[AGENT RESPONSE\]|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"(?i)PLAN:.*?(?=\[AGENT RESPONSE\]|$)", "", text, flags=re.DOTALL)
    return text.strip()

def normalize_output(result: any, max_len: int = 2000) -> str:
    """Clean and truncate tool outputs for the context layer."""
    clean = str(result).strip()
    if len(clean) > max_len:
        return clean[:max_len] + "\n...[truncated for context]"
    return clean

def extract_citations(text: str) -> list:
    """Extract granular citation identifiers from the final answer text."""
    patterns = [
        r"\[Source: [^\]]+, Page: \d+\]",
        r"\[Web Source \d+\]",
        r"\[Table: movies, Row: [^\]]+\]"
    ]
    citations = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        citations.extend(matches)
    # Deduplicate while preserving order if possible (set is fine here)
    return list(set(citations))

def run_agent(question: str) -> str:
    # 1. Check Cache
    cache = load_cache()
    if question in cache:
        cache_data = cache[question]
        if isinstance(cache_data, dict) and "final_answer" in cache_data:
            # Reconstruct logger for terminal output
            logger = TraceLogger()
            logger.current_trace = cache_data
            logger.print_terminal_trace()
            return cache_data["final_answer"]
        return cache_data # Legacy string support

    logger = TraceLogger()
    telemetry = TelemetryTracker()
    logger.start_trace(question)
    
    # SOTA Context Layer
    context_state = {
        "structured": [],
        "unstructured": [],
        "web": [],
        "used_normalized_queries": set(), # Format: (tool_name, frozenset_keywords)
        "failed_sql_queries": set(),
        "web_calls_count": 0
    }
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        UserMessage(content=question)
    ]
    
    step_count = 0
    max_steps = 8
    
    while step_count < max_steps:
        # Step Budget Awareness & Knowledge Consolidation
        remaining = max_steps - step_count
        
        # Consolidation: Merge findings into a clean perspective
        merged_structured = " | ".join(list(set(context_state["structured"])))
        merged_unstructured = "\n---\n".join(list(set(context_state["unstructured"])))
        merged_web = "\n".join(list(set(context_state["web"])))
        
        curated_context = (
            f"REMAINING TOOL CALLS: {remaining}\n"
            f"WEB SEARCHES PERFORMED: {context_state['web_calls_count']}/2\n"
            f"FAILED SQL ATTEMPTS: {list(context_state['failed_sql_queries']) if context_state['failed_sql_queries'] else 'None'}\n"
            f"KNOWLEDGE BASE SO FAR:\n"
            f"DATABASE FACTS: {merged_structured if merged_structured else 'None'}\n"
            f"REVIEW THEMES: {merged_unstructured[:1000] if merged_unstructured else 'None'}\n"
            f"WEB NEWS: {merged_web[:500] if merged_web else 'None'}\n"
            f"IMPORTANT: If the themes/facts you need are already listed above, DO NOT call the tools again. If WEB searches == 2, STOP searching and conclude with available data."
        )
        
        # Inject curated context
        temp_messages = messages + [SystemMessage(content=curated_context)]
        
        try:
            response = client.complete(
                messages=temp_messages,
                tools=TOOLS,
                model=MODEL_NAME
            )
        except Exception as e:
            refusal_msg = f"Execution interrupted: {str(e)}"
            logger.set_telemetry(telemetry.get_summary())
            logger.finish_trace(final_answer=refusal_msg, citations=[], refused=True)
            logger.print_terminal_trace()
            return refusal_msg

        choice = response.choices[0]
        
        if choice.finish_reason == CompletionsFinishReason.STOPPED or (choice.message.content and not choice.message.tool_calls):
            # Clean reasoning blocks before logging and returning
            final_answer = clean_final_answer(choice.message.content)
            
            # --- Bonus C: Reflection Step (Post-Processing) ---
            curated_knowledge = (
                " | ".join(list(set(context_state["structured"]))) + "\n" +
                "\n".join(list(set(context_state["unstructured"]))) + "\n" +
                "\n".join(list(set(context_state["web"])))
            )
            reflection = reflect_on_answer(client, MODEL_NAME, question, final_answer, curated_knowledge[:2000])
            
            if "[FAIL]" in reflection and not context_state.get("has_reflected", False):
                # If reflection fails, we add one emergency turn (Bonus C)
                context_state["has_reflected"] = True
                reflection_msg = f"[SELF-REFLECTION CRITIQUE]: {reflection}\n\nPlease use your tools to address these missing points or corrections before providing a FINAL answer."
                messages.append(UserMessage(content=reflection_msg))
                step_count += 1
                continue # Trigger one more loop attempt
            
            if "[FAIL]" in reflection:
                # If it still fails after reflection, we just append the notice and finish
                final_answer += f"\n\n[SELF-REFLECTION CRITIQUE]: {reflection}"

            granular_citations = extract_citations(final_answer)
            if not granular_citations:
                granular_citations = list(set([step["tool_name"] for step in logger.current_trace["steps"]]))
            
            logger.set_telemetry(telemetry.get_summary())
            logger.finish_trace(final_answer=final_answer, citations=granular_citations)
            logger.print_terminal_trace()
            
            # 2. Update Cache (Store full trace for replay)
            cache[question] = logger.current_trace
            save_cache(cache)
            
            return final_answer
            
        elif choice.finish_reason == CompletionsFinishReason.TOOL_CALLS:
            messages.append(choice.message)
            
            start_time = time.time()
            for tool_call in choice.message.tool_calls:
                if step_count >= max_steps:
                    break
                    
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except:
                    args = {}
                
                input_str = args.get("sql_query") if tool_name == "query_data" else args.get("query", "")
                
                # KEYWORD DEDUPLICATION (SOTA logic)
                raw_keywords = tokenize(input_str)
                query_keywords = frozenset([w for w in raw_keywords if w not in AGENT_STOP_WORDS])
                
                # Check for exact keyword set match OR if the new query is a subset of a broader previous successful query
                is_redundant = False
                for prev_tool, prev_keywords in context_state["used_normalized_queries"]:
                    if tool_name == prev_tool:
                        # If the keywords are the same, or the new query is just a subset of keywords we already searched
                        if query_keywords == prev_keywords or (query_keywords and query_keywords.issubset(prev_keywords)):
                            is_redundant = True
                            break
                
                if is_redundant and len(query_keywords) > 0:
                    result = f"Error: Redundant call. Your existing knowledge already covers keywords {list(query_keywords)}. Please use your KNOWLEDGE BASE SO FAR."
                else:
                    try:
                        raw_result = TOOL_MAP[tool_name](input_str)
                        result = normalize_output(raw_result)
                        
                        if tool_name == "query_data":
                            if "Error" in str(raw_result):
                                context_state["failed_sql_queries"].add(input_str)
                            else:
                                context_state["structured"].append(result)
                        elif tool_name == "search_docs":
                            context_state["unstructured"].append(result)
                        else:
                            context_state["web"].append(result)
                            context_state["web_calls_count"] += 1
                        
                        context_state["used_normalized_queries"].add((tool_name, query_keywords))
                    except Exception as e:
                        result = f"Error computing tool {tool_name}: {str(e)}"
                    
                # --- Bonus B: Telemetry (Silent logging) ---
                latency = time.time() - start_time
                telemetry.record_call(tool_name, latency, response.usage)
                
                logger.log_step(
                    tool_name=tool_name, 
                    tool_input=input_str, 
                    tool_output=str(result),
                    rationale=choice.message.content
                )
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call.id))
                step_count += 1
        else:
            break
            
    refusal_msg = "Could not find answer within 8 steps."
    logger.set_telemetry(telemetry.get_summary())
    logger.finish_trace(final_answer=refusal_msg, citations=[], refused=True)
    logger.print_terminal_trace()
    return refusal_msg

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Question: {query}")
        ans = run_agent(query)
        print(f"\nFinal Answer:\n{ans}")
        print("\n(Trace saved to evaluation/logs/)")