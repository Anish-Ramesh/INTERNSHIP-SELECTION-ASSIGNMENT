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
            "refused": False,
            "telemetry": {}
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

    def set_telemetry(self, telemetry_data: dict):
        if self.current_trace:
            self.current_trace["telemetry"] = telemetry_data

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
            
        def print_box(content, title=None, width=100, border_char="═"):
            top = "╔" + border_char * (width - 2) + "╗"
            bottom = "╚" + border_char * (width - 2) + "╝"
            side = "║"
            
            print(top)
            if title:
                print(f"{side} {title.center(width - 4)} {side}")
                print("╟" + "─" * (width - 2) + "╢")
            
            for line in content.split("\n"):
                # Handle long lines by wrapping
                while len(line) > (width - 4):
                    print(f"{side} {line[:width - 4]} {side}")
                    line = line[width - 4:]
                print(f"{side} {line.ljust(width - 4)} {side}")
            print(bottom)

        print("\n")
        print_box(self.current_trace['question'], title="AGENT QUERY RECEIVED", border_char="━")
        
        for step in self.current_trace["steps"]:
            # Truncate output slightly for terminal readability
            out_str = step['output']
            if len(out_str) > 1200:
                out_str = out_str[:1200] + "\n... [TRUNCATED FOR READABILITY]"
            
            step_title = f"STEP {step['step_number']}: {step['tool_name']}"
            step_content = ""
            if step.get('rationale'):
                step_content += f"THOUGHT: {step['rationale'].strip()}\n"
                step_content += "─" * 40 + "\n"
            step_content += f"INPUT: {step['input']}\n"
            step_content += "─" * 40 + "\n"
            step_content += f"OUTPUT:\n{out_str}"
            
            print_box(step_content, title=step_title, width=100, border_char="─")
            
        final_answer = self.current_trace['final_answer'] or "No response generated."
        citations = ", ".join(self.current_trace.get("citations", [])) or "None"
        
        status = "REFUSED (BUDGET EXCEEDED)" if self.current_trace.get('refused') else "SUCCESS"
        footer_content = f"STATUS: {status}\n"
        footer_content += f"CITATIONS: {citations}\n"
        footer_content += f"STEP COUNT: {self.current_trace['number_of_steps']} / 8 max\n\n"
        footer_content += "FINAL RESPONSE:\n" + "═" * 20 + "\n"
        footer_content += final_answer
        
        print_box(footer_content, title="FINAL AGENT RESPONSE", width=100, border_char="━")
        print("\n")

