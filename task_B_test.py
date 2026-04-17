import os
import sys
from agent.agent_loop import run_agent

def run_task_b():
    print("TASK B FINAL VERIFICATION (10 TEST QUESTIONS)")
    print("=" * 80)
    print("This test verifies routing, direct answers, tracing, and the 8-call hard cap.")
    print("-" * 80)
    print()

    questions = [
        "What was the worldwide gross revenue of 'Avatar' according to the dataset?",
        "Which movie in the dataset had the lowest production budget and what was its value?",
        "Summarize what the review says about the visual effects and underwater cinematography in 'Avatar'.",
        "What themes are highlighted in the critical review of 'Inception' in the document corpus?",
        "Who directed the film 'Oppenheimer' and what is their most recent known project?",
        "What is the official release year and date of 'Avatar: The Way of Water'?",
        "Find the movie that won the 'Super Golden Globe Award of 2026' and describe its visual style.",
        "What were the box office earnings of 'Gone with the Wind' adjusted to current dataset format?",
        "What was the production budget of the 2009 film 'Avatar' and how does it compare to modern CGI films?",
        "Analyze the thematic meaning of the film 'The Host' and ensure correct version is selected."
    ]

    for i, q in enumerate(questions, 1):
        print(f"[QUESTION {i}/10]: {q}")
        # run_agent internally prints the AGENT TRACE LOG
        ans = run_agent(q)
        print(f">>> FINAL AGENT RESPONSE:")
        print(ans)
        print()
        print("-" * 80)
        print()

    print("Verification Complete. Traces for all runs are saved in 'evaluation/logs/'.")

if __name__ == "__main__":
    run_task_b()
