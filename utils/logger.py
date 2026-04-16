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

    def log_step(self, tool_name: str, tool_input: str, tool_output: str):
        if not self.current_trace:
            return
        
        step = {
            "step_number": len(self.current_trace["steps"]) + 1,
            "tool_name": tool_name,
            "input": tool_input,
            "output": tool_output
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
