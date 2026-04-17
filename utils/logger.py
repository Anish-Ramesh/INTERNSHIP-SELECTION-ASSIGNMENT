import json
import os
import datetime

class TraceLogger:
    def __init__(self, log_dir="evaluation/logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.current_trace = {}

    def start_trace(self, question: str):
        self.current_trace = {
            "timestamp": datetime.datetime.now().isoformat(),
            "question": question,
            "steps": [],
            "final_answer": None,
            "citations": [],
            "number_of_steps": 0,
            "refused": False
        }

    def log_step(self, tool_name: str, tool_input: str, tool_output: str, rationale: str = None):
        if not self.current_trace:
            return
        
        step = {
            "step_number": len(self.current_trace["steps"]) + 1,
            "tool_name": tool_name,
            "input": tool_input,
            "output": tool_output,
            "rationale": rationale
        }
        self.current_trace["steps"].append(step)
        self.current_trace["number_of_steps"] += 1

    def finish_trace(self, final_answer: str, citations: list, refused: bool = False):
        if not self.current_trace:
            return
            
        self.current_trace["final_answer"] = final_answer
        self.current_trace["citations"] = citations
        self.current_trace["refused"] = refused
        
        # Save to file
        filename = f"trace_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.log_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.current_trace, f, indent=4)
            
        return filepath

    def print_terminal_trace(self):
        if not self.current_trace:
            return
            
        print("\n" + "█"*80)
        print(f" QUESTION: {self.current_trace['question']}")
        print("█"*80)
        
        for step in self.current_trace["steps"]:
            # Truncate output slightly for terminal readability, but keep it generous 
            out_str = step['output']
            if len(out_str) > 1200:
                out_str = out_str[:1200] + "\n... [TRUNCATED FOR READABILITY]"
            
            print(f"\n[STEP {step['step_number']}] TOOL: {step['tool_name']}")
            if step.get('rationale'):
                print(f"RATIONALE: {step['rationale'].strip()}")
            print(f"INPUT: {step['input']}")
            print(f"RESULT:\n{out_str}")
            print("-" * 60)
            
        print(f"\n" + "▼ " * 20 + " FINAL AGENT RESPONSE " + "▼ " * 20)
        print(f"{self.current_trace['final_answer']}")
        print("▲ " * 20 + " END OF RESPONSE " + "▲ " * 20)
        
        # Format citations simply as a comma separated list
        citations = ", ".join(self.current_trace.get("citations", [])) or "None"
        print(f"\nCITATIONS: {citations}")
        print(f"STEP COUNT: {self.current_trace['number_of_steps']} / 8 max")
        print("█"*80 + "\n")

