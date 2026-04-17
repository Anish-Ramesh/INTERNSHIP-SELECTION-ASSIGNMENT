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
        "Find the movie with the highest opening weekend revenue in the dataset and summarize its critical themes from the review documents.",
        "Compare the Rotten Tomatoes score of 'Avatar' and 'Avengers: Infinity War' and identify which film is described more positively in the review corpus.",
        "Retrieve the budget of any James Cameron film from the dataset and find recent news about his upcoming projects using web search.",
        "Identify the movie with the lowest Rotten Tomatoes score in the dataset and check online if its director has received any recent awards.",
        "Compare total worldwide gross of all Marvel movies in the dataset with their critical reception in reviews, and explain any pattern you observe.",
        "Find a high-budget film from the dataset and check whether its director has any announced upcoming films in recent news."
    ]

    for i, q in enumerate(questions, 1):
        print(f"[QUESTION {i}/6]: {q}")
        ans = run_agent(q)
        print(f">>> FINAL AGENT RESPONSE:")
        print(ans)
        print()
        print("-" * 80)
        print()

    print("Verification Complete. Traces for all runs are saved in 'evaluation/logs/'.")

if __name__ == "__main__":
    run_task_c()
