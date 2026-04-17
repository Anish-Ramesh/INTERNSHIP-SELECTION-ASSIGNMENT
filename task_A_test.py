import os
import sys
from tools.search_docs import search_docs
from tools.query_data import query_data
from tools.web_search import web_search

def run_task_a():
    print("=" * 60)
    print("TESTING PHASE: TASK A (Standalone Tools Validation)")
    print("=" * 60)
    print()

    # 1. SEARCH_DOCS
    print("-" * 40)
    print("1. SEARCH_DOCS (Semantic / Unstructured)")
    print("-" * 40)
    print("Testing relevance, extraction accuracy, and source/page citations.")
    print()

    queries_docs = [
        "What does the review say about Inception?",
        "What are the main themes of the movie Titanic?",
        "Are there any mentions of emotional impact or resonant blockbuster moments in Avengers?",
        "What is the review opinion on the CGI and visual spectacle of Jurassic World?",
        "How is the acting or performance described in the Joker review?"
    ]

    for i, q in enumerate(queries_docs, 1):
        print(f"[Doc Query {i}]: {q}")
        print("RESULT:")
        print(search_docs(q))
        print("." * 45)
        print()

    # 2. QUERY_DATA
    print("-" * 40)
    print("2. QUERY_DATA (SQLite / Structured DB)")
    print("-" * 40)
    print("Testing tabular output, accurate SQL execution, and aggregate comparisons.")
    print()

    queries_sql = [
        "SELECT title, budget, opening_weekend, worldwide_gross, rotten_tomatoes_score FROM movies WHERE title='Inception';",
        "SELECT title, worldwide_gross FROM movies ORDER BY worldwide_gross DESC LIMIT 1;",
        "SELECT title, rotten_tomatoes_score FROM movies WHERE rotten_tomatoes_score > 95 ORDER BY rotten_tomatoes_score DESC LIMIT 3;"
    ]

    for i, q in enumerate(queries_sql, 1):
        print(f"[SQL Query {i}]: {q}")
        print("RESULT:")
        print(query_data(q))
        print("." * 45)
        print()

    # 3. WEB_SEARCH
    print("-" * 40)
    print("3. WEB_SEARCH (Tavily API / Real-time info)")
    print("-" * 40)
    print("Testing snippet extraction, URL sourcing, and live retrieval format.")
    print()

    queries_web = [
        "Inception awards",
        "Recent Oscars winners 2026 best picture",
        "Christopher Nolan upcoming movie release date"
    ]

    for i, q in enumerate(queries_web, 1):
        print(f"[Web Query {i}]: {q}")
        print("RESULT:")
        print(web_search(q))
        print("." * 45)
        print()

    print("=" * 60)
    print("ALL TESTS INITIATED. Please manually verify:")
    print("1. Did search_docs return actual filenames/pages?")
    print("2. Did query_data return completely accurate numerical values in markdown tables?")
    print("3. Did web_search return URLs and accurate snippets?")
    print("=" * 60)

if __name__ == "__main__":
    run_task_a()
