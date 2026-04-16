# Task A Final Report: Tool Scaffolding & Constrained Interface Design

Phase 1 successfully established the core infrastructure, data ingestion pipelines, and standalone tool interfaces required for the Movies Agent.

## 1. Project Scaffolding
The strict directory structure has been implemented:
- `agent/`: Placeholder for Task B logic.
- `tools/`: Standalone implementations for `search_docs`, `query_data`, and `web_search`.
- `data/`: Contains `database.db` (SQLite) and ingestion scripts.
- `vectorstore/`: Formerly ChromaDB, now serves as the source for the BM25 search logic.
- `utils/`: Includes `logger.py` for trace logging and session management.

## 2. Data Ingestion
- **Structured Data**: `dataset/movies_structured.csv` was ingested into a local SQLite database (`data/database.db`). The `movies` table supports standard SQL SELECT queries with fields for budget, gross, and ratings.
- **Unstructured Data**: The 15 movie reviews in `dataset/unstructured_reviews/` are indexed in-memory using the **BM25Okapi** algorithm. This ensures fast, keyword-accurate retrieval without the overhead of vector embeddings for this small corpus.

## 3. Tool Implementation & Guardrails
Each tool features negative constraints to guide LLM reasoning and prevent hallucinations:

### search_docs (Unstructured RAG)
- **Logic**: Filters documents by movie entity (extracted from query) before scoring.
- **Guardrail**: Implements a score threshold (0.5) and returns a structured refusal if the movie is not found in the corpus.
- **Citations**: Automatically prepends `[Source: File, Page: 1]` to all snippets.

### query_data (Structured SQL)
- **Logic**: Executes read-only SQLite queries.
- **Guardrail**: Strictly blocks destructive keywords (`DROP`, `DELETE`, `UPDATE`) and returns data as Markdown tables for better LLM reasoning.

### web_search (Real-time Info)
- **Logic**: Connects to the **Tavily API**.
- **Guardrail**: Enforces a short query constraint (<10 words) and returns a numbered list of sources with URLs and published dates.

## 4. Final Verification Results

```text
============================================================
TESTING PHASE: TASK A (Standalone Tools Validation)
============================================================

1. SEARCH_DOCS (BM25 Keyword Search)
- [Doc Query]: What does the review say about Inception?
  RESULT: No documents found for the requested movie in the corpus.
- [Doc Query]: Themes of Titanic?
  RESULT: [Source: Titanic.txt, Page: 1] Movie: Titanic ... visual spectacle and melodrama.

2. QUERY_DATA (SQLite)
- [SQL Query]: Inception stats
  RESULT: | title | budget | opening_weekend | worldwide_gross | ... | 87 |
- [SQL Query]: Highest grossing movie
  RESULT: | title: Avatar | worldwide_gross: 2.92371e+09 |

3. WEB_SEARCH (Tavily)
- [Web Query]: Christopher Nolan upcoming movie
  RESULT: [Web Source 1] The Odyssey - July 17, 2026.
============================================================
```

Task A is verified and complete. Ready for Task B (Agent Loop Implementation).
