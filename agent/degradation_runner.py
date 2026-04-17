import os
import sys
import json
import time

# Add root directory to path so we can import agent logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent_loop import run_agent
from agent.bonus_features import toggle_degradation

# Configuration
CORPUS_PATH = "dataset/unstructured_reviews"
OUTPUT_LOG = "evaluation/degradation_comparison.json"

QUESTIONS = [
    {"id": 2, "q": "Which movie in the dataset had the lowest production budget and what was its value?"},
    {"id": 5, "q": "Who directed the film 'Oppenheimer' and what is their most recent known project?"},
    {"id": 7, "q": "Find the movie with the highest opening weekend revenue in the dataset and summarize its critical themes from the review documents."},
    {"id": 11, "q": "Compare total worldwide gross of all Marvel movies in the dataset with their critical reception in reviews, and explain any pattern you observe."},
    {"id": 20, "q": "Analyze the thematic meaning of the film 'The Host' and ensure correct version is selected."}
]

def run_suite(label):
    print(f"\n>>> STARTING PHASE: {label}")
    results = []
    for item in QUESTIONS:
        print(f"\n  [Q{item['id']}] {item['q']}")
        start_time = time.time()
        answer = run_agent(item['q'])
        duration = round(time.time() - start_time, 2)
        
        results.append({
            "id": item['id'],
            "phase": label,
            "answer": answer,
            "duration": duration
        })
        time.sleep(2) # API safety
    return results

def main():
    print("\n" + "█" * 80)
    print(" DUAL-PHASE DEGRADATION AUDIT RUNNER ".center(80, "█"))
    print("█" * 80 + "\n")

    full_results = {}

    try:
        # Phase 1: Normal
        full_results["NORMAL"] = run_suite("NORMAL_CORPUS (100%)")

        # Phase 2: Degraded
        print("\n>>> HALVING CORPUS FOR DEGRADATION TEST...")
        msg = toggle_degradation(CORPUS_PATH, enable=True)
        print(msg)
        
        full_results["DEGRADED"] = run_suite("DEGRADED_CORPUS (50%)")

    finally:
        # Restoration
        msg = toggle_degradation(CORPUS_PATH, enable=False)
        print(f"\n>>> {msg}")

    # Save comparison data
    os.makedirs("evaluation", exist_ok=True)
    with open(OUTPUT_LOG, "w") as f:
        json.dump(full_results, f, indent=4)
    
    print("\n" + "=" * 80)
    print(" AUDIT COMPLETE ".center(80, "="))
    print(f"Comparison log saved to {OUTPUT_LOG}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
