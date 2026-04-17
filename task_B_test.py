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
        "According to the local movie reviews, what are the primary themes of the film Titanic?",
        "In the provided reviews, how is the pacing and tone of Avengers: Infinity War described relative to Endgame?",
        "What is the exact worldwide gross of the movie 'Avatar' as recorded in the structured database?",
        "Which movie in the database has the highest worldwide gross, and what is its Rotten Tomatoes score?",
        "Search the web to find out who won the 'Best Picture' award at the 2026 Oscars.",
        "What is the release date for Christopher Nolan's upcoming film 'The Odyssey' according to recent web news?",
        "Evaluate the mathematical expression: (52 * 4) + 10.",
        "What is the capital of Japan?",
        "What are the themes for the movie 'Joker' found in our local unstructured reviews?",
        "Loop the following actions: search the web for 'abc', then 'def', then 'ghi'. Continue searching the web for random 3-letter strings sequentially until you have made at least 10 tool calls. Do not stop until you hit the limit."
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
