import time
import os
import shutil
import random
from azure.ai.inference.models import SystemMessage

# ==============================================================================
# BONUS A: STRATEGIC REASONING & PLANNING
# ==============================================================================
BONUS_A_SYSTEM_PROMPT = """
### SOTA REASONING PROTOCOL (Bonus A: Strategic Planning)
For every turn, you MUST follow this internal cycle before calling tools:
1. STRATEGIC BREAKDOWN: Decompose the user's query into logical sub-tasks.
2. PLAN: Write a 1-3 sentence justification for your NEXT tool choice. Explain WHY you are using it and WHAT you expect to find.
3. THOUGHT: Internal logic processing.

### GROUNDING & SYNTHESIS RULES
- **COHESIVE SYNTHESIS**: In your final [AGENT RESPONSE], provide a single, direct, and well-grounded answer. Do not fragment the answer into sections.
- **FLEXIBLE FALLBACK**: If a direct query returns no results, try broader SQL (LIKE) or broader web keywords.
"""

# ==============================================================================
# BONUS B: PER-TOOL TELEMETRY
# ==============================================================================
class TelemetryTracker:
    def __init__(self):
        self.tool_stats = {} # {tool_name: {"calls": 0, "total_tokens": 0, "total_latency": 0}}

    def record_call(self, tool_name, latency, usage):
        if tool_name not in self.tool_stats:
            self.tool_stats[tool_name] = {"calls": 0, "total_tokens": 0, "total_latency": 0}
        
        self.tool_stats[tool_name]["calls"] += 1
        self.tool_stats[tool_name]["total_latency"] += latency
        if usage:
            self.tool_stats[tool_name]["total_tokens"] += usage.total_tokens

    def get_summary(self):
        return self.tool_stats

# ==============================================================================
# BONUS C: REFLECTION STEP
# ==============================================================================
def reflect_on_answer(client, model_name, question, final_answer, context_summary):
    """
    Post-processing reflection turn (Bonus C). 
    Critiques the final answer for citation accuracy and grounding.
    """
    reflection_prompt = f"""
    You are a meticulous fact-checker. Analyze the following answer given to a user.
    
    QUESTION: {question}
    KNOWLEDGE BASE SO FAR: {context_summary}
    PROPOSED ANSWER: {final_answer}
    
    TASK:
    1. Does the answer actually address the user's question?
    2. Are all claims supported by the KNOWLEDGE BASE provided?
    3. Are the citations valid (not hallucinated)?
    
    If everything is correct, respond ONLY with '[PASS]'.
    If there is an error or missing information, respond with '[FAIL]' followed by a brief critique and the name of the tool you need to fix it.
    """
    
    try:
        response = client.complete(
            messages=[SystemMessage(content=reflection_prompt)],
            model=model_name
        )
        critique = response.choices[0].message.content.strip()
        return critique
    except:
        return "[PASS]" # Default to pass on reflection failures to avoid loops

# ==============================================================================
# BONUS D: DEGRADATION UTILITIES
# ==============================================================================
def toggle_degradation(corpus_path, enable=True):
    """
    Bonus D: Halves the corpus by moving 50% of files to a backup.
    """
    backup_path = corpus_path + "_backup"
    
    if enable:
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
        
        files = [f for f in os.listdir(corpus_path) if f.endswith('.txt')]
        random.seed(42) # Deterministic halving
        files_to_move = random.sample(files, len(files) // 2)
        
        for f in files_to_move:
            shutil.move(os.path.join(corpus_path, f), os.path.join(backup_path, f))
        return f"Degraded corpus: Moved {len(files_to_move)} files to backup."
    else:
        if os.path.exists(backup_path):
            files = os.listdir(backup_path)
            for f in files:
                shutil.move(os.path.join(backup_path, f), os.path.join(corpus_path, f))
            os.rmdir(backup_path)
            return f"Restored corpus: Returned {len(files)} files to original store."
        return "Corpus was not degraded."
