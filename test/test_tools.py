import os
import sys

# Ensure imports work from the root dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.search_docs import search_docs
from tools.query_data import query_data
from tools.web_search import web_search

def run_tests():
    print("=" * 60)
    print("TESTING PHASE: TASK A (Standalone Tools Validation)")
    print("=" * 60)
    
    # ---------------------------------------------------------
    # 1. Unstructured Data Search (search_docs) - 5 Queries
    # ---------------------------------------------------------
    print("\n\n" + "-" * 40)
    print("1. SEARCH_DOCS (Semantic / Unstructured)")
    print("-" * 40)
    print("Testing relevance, extraction accuracy, and source/page citations.\n")
    
    doc_queries = [
        "What does the review say about Inception?",
        "What are the main themes of the movie Titanic?",
        "Are there any mentions of emotional impact or resonant blockbuster moments in Avengers?",
        "What is the review opinion on the CGI and visual spectacle of Jurassic World?",
        "How is the acting or performance described in the Joker review?"
    ]
    
    for i, q in enumerate(doc_queries, 1):
        print(f"\n[Doc Query {i}]: {q}")
        print("RESULT:")
        print(search_docs(q))
        print("..." * 15)

    # ---------------------------------------------------------
    # 2. Structured Data Query (query_data) - 3 Queries
    # ---------------------------------------------------------
    print("\n\n" + "-" * 40)
    print("2. QUERY_DATA (SQLite / Structured DB)")
    print("-" * 40)
    print("Testing tabular output, accurate SQL execution, and aggregate comparisons.\n")

    sql_queries = [
        # Lookup specific movie stats
        "SELECT title, budget, opening_weekend, worldwide_gross, rotten_tomatoes_score FROM movies WHERE title='Inception';",
        
        # Aggregation: highest grossing movie
        "SELECT title, worldwide_gross FROM movies ORDER BY worldwide_gross DESC LIMIT 1;",
        
        # Aggregation: compare
        "SELECT title, rotten_tomatoes_score FROM movies WHERE rotten_tomatoes_score > 95 ORDER BY rotten_tomatoes_score DESC LIMIT 3;"
    ]

    for i, q in enumerate(sql_queries, 1):
        print(f"\n[SQL Query {i}]: {q}")
        print("RESULT:")
        print(query_data(q))
        print("..." * 15)
        
    # ---------------------------------------------------------
    # 3. Web Search (web_search) - 3 Queries
    # ---------------------------------------------------------
    print("\n\n" + "-" * 40)
    print("3. WEB_SEARCH (Tavily API / Real-time info)")
    print("-" * 40)
    print("Testing snippet extraction, URL sourcing, and live retrieval format.\n")

    web_queries = [
        "Inception awards",
        "Recent Oscars winners 2026 best picture",
        "Christopher Nolan upcoming movie release date"
    ]

    for i, q in enumerate(web_queries, 1):
        print(f"\n[Web Query {i}]: {q}")
        print("RESULT:")
        print(web_search(q))
        print("..." * 15)


if __name__ == "__main__":
    run_tests()
    print("\n\n" + "=" * 60)
    print("ALL TESTS INITIATED. Please manually verify:")
    print("1. Did search_docs return actual filenames/pages?")
    print("2. Did query_data return completely accurate numerical values in markdown tables?")
    print("3. Did web_search return URLs and accurate snippets?")
    print("=" * 60)
