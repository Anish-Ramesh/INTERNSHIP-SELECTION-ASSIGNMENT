import sys
import os
# Add project root to sys.path for direct script execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    CompletionsFinishReason
)
from azure.core.credentials import AzureKeyCredential

from utils.logger import TraceLogger
from agent.bonus_features import BONUS_A_SYSTEM_PROMPT, TelemetryTracker, reflect_on_answer

# New Modular Imports
from agent.tools_config import TOOLS, TOOL_MAP
from agent.agent_utils import (
    clean_final_answer, 
    normalize_output, 
    extract_citations, 
    AGENT_STOP_WORDS,
    tokenize,
    load_cache,
    save_cache,
    RESPONSE_CACHE_PATH
)
from agent.prompts import SYSTEM_PROMPT

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

# (Cache logic moved to agent/cache/__init__.py)
CACHE_FILE = RESPONSE_CACHE_PATH

# (Utility functions and AGENT_STOP_WORDS moved to agent/agent_utils.py)

def get_safety_refusal_reason(query: str) -> str:
    """Detects prompt injection or high-risk off-topic queries (Medical, Financial)."""
    query_lower = query.lower()
    
    # 1. Jailbreak / Injection Detection
    jailbreak_keywords = [
        "ignore all previous instructions", "system prompt", "you are now", 
        "jailbreak", "dan ", "override", "secret command"
    ]
    for kw in jailbreak_keywords:
        if kw in query_lower:
            return "I'm sorry, but I cannot assist with that request as it appears to involve prompt injection attempts or system guideline violations."
            
    # 2. Medical / Health Refusal (High Risk)
    medical_keywords = [
        "stroke", "symptom", "doctor", "medicine", "hospital", "cure", "treatment", 
        "pain", "health advice", "medication", "first aid", "emergency"
    ]
    # Check for medical keywords only if they don't seem movie-related (basic heuristic)
    if any(mw in query_lower for mw in medical_keywords) and "movie" not in query_lower:
        return "I am an Advanced Movie Reasoning Agent and I'm sorry, but I cannot answer queries related to medical or health-related topics. Please consult a qualified medical professional for any health concerns."
        
    # 3. Financial / Investment Refusal (High Risk)
    financial_keywords = [
        "invest", "stock", "trading", "profit", "money", "wealth", "crypto", "bitcoin", 
        "financial advice", "which company", "buy share"
    ]
    if any(fw in query_lower for fw in financial_keywords) and "movie" not in query_lower:
        return "I am an Advanced Movie Reasoning Agent and I'm sorry, but I cannot provide financial or investment advice. I can only assist with movie-related data analysis."
        
    return None

def run_agent(question: str, bypass_cache: bool = False, cache_path: str = None) -> str:
    # 0. Safety & Topic Gating (Programmatic Refusal)
    refusal_reason = get_safety_refusal_reason(question)
    if refusal_reason:
        logger = TraceLogger()
        logger.start_trace(question)
        logger.finish_trace(final_answer=refusal_reason, citations=[], refused=True)
        # We use the logger's new boxed printer for consistency
        logger.print_terminal_trace()
        return refusal_reason

    # 1. Check Cache
    active_cache_path = cache_path or CACHE_FILE
    is_default_cache = (active_cache_path == CACHE_FILE)

    cache = load_cache(active_cache_path)
    if not bypass_cache:
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
    
    # Context Layer
    context_state = {
        "structured": [],
        "unstructured": [],
        "web": [],
        "query_attempts": {}, # Format: (tool_name, frozenset_keywords) -> count
        "failed_sql_queries": set(),
        "web_calls_count": 0
    }
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        UserMessage(content=question)
    ]
    
    step_count = 0  # Tracks individual TOOL CALLS
    turn_count = 0  # Tracks total LLM interactions
    max_steps = 8   # Max tool calls allowed
    max_turns = 15  # Safety cap for total interactions
    
    while turn_count < max_turns:
        turn_count += 1
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
            refusal_msg = f"Execution interrupted: {str(e)}\n[FATAL ERROR]: Please fix the environment or connection issues before retrying."
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
            # Increased context window to 5000 to handle large SQL tables without triggering false 'hallucination' flags in reflection
            reflection = reflect_on_answer(client, MODEL_NAME, question, final_answer, curated_knowledge[:5000])
            
            if "[FAIL]" in reflection and not context_state.get("has_reflected", False):
                # If reflection fails, we add one emergency turn (Bonus C)
                # We do NOT increment step_count here as this is a thinking turn, not a tool call
                context_state["has_reflected"] = True
                reflection_msg = f"[SELF-REFLECTION CRITIQUE]: {reflection}\n\nPlease use your tools to address these missing points or corrections before providing a FINAL answer."
                messages.append(UserMessage(content=reflection_msg))
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
            
            # 2. Update Cache (Store full trace for replay) - ONLY if not refused or errored
            if not logger.current_trace.get("refused", False):
                cache[question] = logger.current_trace
                save_cache(cache, cache_path=active_cache_path, enable_rollover=is_default_cache)
            
            return final_answer
            
        elif choice.finish_reason == CompletionsFinishReason.TOOL_CALLS:
            messages.append(choice.message)
            
            start_time = time.time()
            for tool_call in choice.message.tool_calls:
                # Check hard cap BEFORE executing the tool
                if step_count >= max_steps:
                    # Budget exceeded - force immediate structured refusal
                    break
                    
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except:
                    args = {}
                
                input_str = args.get("sql_query") if tool_name == "query_data" else args.get("query", "")
                
                # KEYWORD DEDUPLICATION LOGIC (Three-Strike Policy)
                raw_keywords = tokenize(input_str)
                query_keywords = frozenset([w for w in raw_keywords if w not in AGENT_STOP_WORDS])
                
                attempts = context_state["query_attempts"].get((tool_name, query_keywords), 0)
                
                is_redundant = False
                apply_penalty_warning = False
                
                if attempts == 1:
                    # Strike 2: Block and warn about redundancy
                    is_redundant = True
                    # Increment attempt so the 3rd time it passes
                    context_state["query_attempts"][(tool_name, query_keywords)] = 2
                elif attempts >= 2:
                    # Strike 3+: Allow but with a clear step penalty warning
                    is_redundant = False
                    apply_penalty_warning = True
                
                if is_redundant and len(query_keywords) > 0:
                    result = f"Error: Redundant call. Your existing knowledge already covers keywords {list(query_keywords)}. This is your 2nd attempt. One more repeat will incur a step penalty."
                else:
                    try:
                        raw_result = TOOL_MAP[tool_name](input_str)
                        result = normalize_output(raw_result)
                        
                        # Check for Tool-Level Errors (e.g. SQL Syntax)
                        if str(result).startswith("Error"):
                            # If it's a tool error, we do NOT increment the deduplication count 
                            # because the agent didn't successfully get any data.
                            # We also feed the error back to the LLM to let it try to fix it.
                            pass 
                        else:
                            # Successful Tool Call (or "No results found" which is valid)
                            # Increment the successful attempt count for deduplication
                            context_state["query_attempts"][(tool_name, query_keywords)] = attempts + 1
                            
                            if tool_name == "query_data":
                                context_state["structured"].append(result)
                            elif tool_name == "search_docs":
                                context_state["unstructured"].append(result)
                            else:
                                context_state["web"].append(result)
                                context_state["web_calls_count"] += 1

                            if apply_penalty_warning:
                                result = f"[STEP PENALTY WARNING]: This is your 3rd attempt for these keywords. You have bypassed the deduplication wall, but note that this turn has consumed a reasoning step. Please use the results below effectively to avoid further redundancy.\n\n{result}"
                        
                    except Exception as e:
                        # SYSTEM EXCEPTION: This is a fatal code/environment error
                        error_msg = f"FATAL SYSTEM EXCEPTION in {tool_name}: {str(e)}\n[ACTION]: The system environment is broken. Please fix the Python code or API configuration."
                        logger.log_step(tool_input=input_str, tool_name=tool_name, tool_output=error_msg, rationale="Python exception occurred.")
                        logger.finish_trace(final_answer=error_msg, citations=[], refused=True)
                        logger.print_terminal_trace()
                        return error_msg
                    
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
            # Check again after processing all tool calls from this turn
            if step_count >= max_steps:
                break
        else:
            break
            
    # Final fallback for any reason the loop terminated without a STOPPED choice
    # If step_count hit the limit, we provide the structured refusal
    refusal_msg = (
        "╔════════════════════════════════════════════════════════════════════════════════╗\n"
        "║                     STRICT REFUSAL: BUDGET EXCEEDED                            ║\n"
        "╠════════════════════════════════════════════════════════════════════════════════╣\n"
        "║ The agent has reached its hard limit of 8 tool calls. To ensure system         ║\n"
        "║ stability and prevent infinite loops, execution has been terminated.           ║\n"
        "║                                                                                ║\n"
        "║ SYSTEM AUDIT:                                                                  ║\n"
        "║ - Total Steps: 8/8                                                             ║\n"
        "║ - Reason: Token/Reasoning Budget Exhausted                                     ║\n"
        "║ - Status: Structured Termination Triggered                                     ║\n"
        "╚════════════════════════════════════════════════════════════════════════════════╝"
    )
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
        # Trace saved to evaluation/logs/ (printed inside run_agent)
    else:
        print("\n" + "="*50)
        print(" MOVIE REASONING AGENT: INTERACTIVE MODE ".center(50, "="))
        print("="*50)
        print("Type 'exit' or 'quit' to end the session.\n")
        
        while True:
            try:
                query = input("[USER]: ").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit", "bye"]:
                    print("Ending session. Goodbye!")
                    break
                
                print("\n[AGENT]: Thinking...")
                run_agent(query)
                print("-" * 50)
            except (KeyboardInterrupt, EOFError):
                print("\nEnding session. Goodbye!")
                break