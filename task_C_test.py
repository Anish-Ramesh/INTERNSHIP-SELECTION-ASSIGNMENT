import os
import sys
from agent.agent_loop import run_agent

def run_task_c():
    print("TASK C FINAL VERIFICATION (5 MULTI-TOOL QUESTIONS)")
    print("=" * 80)
    print("This test verifies multi-tool reasoning, sequential orchestration, and granular citations.")
    print("-" * 80)
    print()

    questions = [
        "Identify the primary themes of the movie with the highest opening weekend in our dataset.",
        "Compare the Rotten Tomatoes score of 'Avatar' with the critical consensus of 'Avengers: Infinity War'. Which one is described more as an 'unqualified triumph'?",
        "Search the web for any upcoming project by James Cameron and compare its projected release date with the budget of 'Avatar' found in our database.",
        "Compare the total worldwide gross of all 'Avengers' movies in our database with the combined opening weekends of all 'Frozen' movies. Then, identify which 'Avengers' film is described in our reviews as a 'burdened sequel' and summarize its specific 'Ultron Enigma'.",
        "Find the movie with the lowest Rotten Tomatoes score in our database, then search the web to find its director and any recent awards they have won."
    ]

    for i, q in enumerate(questions, 1):
        print(f"[QUESTION {i}/5]: {q}")
        ans = run_agent(q)
        print(f">>> FINAL AGENT RESPONSE:")
        print(ans)
        print()
        print("-" * 80)
        print()

    print("Verification Complete. Traces for all runs are saved in 'evaluation/logs/'.")

if __name__ == "__main__":
    run_task_c()
