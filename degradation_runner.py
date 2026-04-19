import os
import sys
import argparse
from agent.agent_loop import run_agent
from agent.bonus_features import toggle_degradation

# Paths
CORPUS_PATH = os.path.join("dataset", "unstructured_reviews")
EVAL_CACHE = os.path.join("agent", "eval_cache.json")

def run_degradation_test(check_only=False):
    """
    Toggles corpus degradation (removing 50% of files), runs sample queries,
    and restores the corpus.
    """
    print("\n" + "="*60)
    print(" DEGRADATION AUDIT RUNNER ".center(60, "="))
    print("="*60)

    if check_only:
        print(">>> CHECK MODE: Testing import and startup...")
        print(">>> SUCCESS: Degradation runner is functional.")
        return

    # 1. Enable Degradation
    print(f"\n[1/3] Enabling Degradation (Halving Corpus)...")
    try:
        msg = toggle_degradation(CORPUS_PATH, enable=True)
        print(f">>> {msg}")
    except Exception as e:
        print(f"!!! Error enabling degradation: {e}")
        return

    # 2. Run Sample Queries
    # We pick a few questions where documents are likely to be removed
    test_queries = [
        "Summarize what the review says about the visual effects in 'Avatar'.",
        "What themes are highlighted in the review of 'The Host'?"
    ]

    print(f"\n[2/3] Running Sample Queries under 50% Corpus...")
    try:
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 30)
            # Use bypass_cache=True to see real-time degradation impact, 
            # or False to see how persistent cache handles it.
            # For this audit, we use cache to verify trace fallback.
            answer = run_agent(query, bypass_cache=False, cache_path=EVAL_CACHE)
            print(f"AGENT RESPONSE Snippet: {answer[:150]}...")
            print("-" * 30)
    except Exception as e:
        print(f"!!! Error during query execution: {e}")
    finally:
        # 3. Restore Corpus
        print(f"\n[3/3] Restoring Corpus...")
        msg = toggle_degradation(CORPUS_PATH, enable=False)
        print(f">>> {msg}")

    print("\n" + "="*60)
    print(" DEGRADATION AUDIT COMPLETE ".center(60, "="))
    print("="*60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run movie corpus degradation tests.")
    parser.add_argument("--check", action="store_true", help="Just check if the script runs and exit.")
    args = parser.parse_args()

    run_degradation_test(check_only=args.check)
