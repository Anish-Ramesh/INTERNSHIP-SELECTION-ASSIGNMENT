import os
import json
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

from tools.search_docs import search_docs
from tools.query_data import query_data
from tools.web_search import web_search
from utils.logger import TraceLogger

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

SYSTEM_PROMPT = """You are an intelligent reasoning agent tasked with answering questions about movies.
You have three tools available:
1. `search_docs`: to retrieve qualitative movie reviews.
2. `query_data`: to execute SQL queries on a database with movie financials & ratings. (table: movies, schema: title, year, genre, budget, opening_weekend, worldwide_gross, rotten_tomatoes_score)
3. `web_search`: to search the live web for current events.

Guidelines:
- If a question doesn't require tools (e.g. arithmetic, simple greetings), answer directly.
- ALWAYS cite your sources using the exact format returned by the tools (e.g., [Source: Inception.txt, Page: 1] or [Web Source 1] or Table rows).
- You may call multiple tools step-by-step if the question requires joining information.
- If you hit a roadblock, the tools return empty data, or you cannot confidently answer after checking all sources, output a clear refusal describing what is missing. Do NOT guess or hallucinate.
- Do not call the same tool with the exact same input if it has already failed.
"""

def run_agent(question: str) -> str:
    logger = TraceLogger()
    logger.start_trace(question)
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        UserMessage(content=question)
    ]
    
    step_count = 0
    max_steps = 8
    
    # Core loop (must be under 100 lines)
    while step_count < max_steps:
        try:
            response = client.complete(
                messages=messages,
                tools=TOOLS,
                model=MODEL_NAME
            )
        except Exception as e:
            refusal_msg = f"Execution interrupted due to API constraint (likely token limit from too many iterative traces): {str(e)}"
            logger.finish_trace(final_answer=refusal_msg, citations=[], refused=True)
            logger.print_terminal_trace()
            return refusal_msg

        choice = response.choices[0]
        # DEBUG: print(f"DEBUG: finish_reason={choice.finish_reason}")
        
        # Some models use STOPPED, others might return None with non-empty content
        if choice.finish_reason == CompletionsFinishReason.STOPPED or (choice.message.content and not choice.message.tool_calls):
            # Valid Answer Complete
            final_answer = choice.message.content
            invoked = list(set([step["tool_name"] for step in logger.current_trace["steps"]]))
            logger.finish_trace(final_answer=final_answer, citations=invoked)
            logger.print_terminal_trace()
            return final_answer
            
        elif choice.finish_reason == CompletionsFinishReason.TOOL_CALLS:
            # Add LM's request to the messages frame
            messages.append(choice.message)
            
            for tool_call in choice.message.tool_calls:
                # Check if we've already hit or exceeded limit before processing this call
                if step_count >= max_steps:
                    break
                    
                tool_name = tool_call.function.name
                
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                
                # Safely execute
                try:
                    if tool_name == "search_docs":
                        input_str = args.get("query", "")
                        result = TOOL_MAP[tool_name](input_str)
                    elif tool_name == "query_data":
                        input_str = args.get("sql_query", "")
                        result = TOOL_MAP[tool_name](input_str)
                    elif tool_name == "web_search":
                        input_str = args.get("query", "")
                        result = TOOL_MAP[tool_name](input_str)
                    else:
                        input_str = str(args)
                        result = f"Error: Tool '{tool_name}' not found."
                except Exception as e:
                    result = f"Error computing tool {tool_name}: {str(e)}"
                    
                # Log step iteratively
                logger.log_step(tool_name=tool_name, tool_input=input_str, tool_output=str(result))
                
                # Mount Context
                messages.append(ToolMessage(content=str(result), tool_call_id=tool_call.id))
                
                step_count += 1
            
            # If we hit the cap mid-turn or after turn, the main while loop will exit.
        else:
            break

            
    # Hard cap edge case
    refusal_msg = "I'm sorry, but I was unable to find the correct answer within the allowed maximum number of steps (8 calls). Halting execution to prevent infinite loops."
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
