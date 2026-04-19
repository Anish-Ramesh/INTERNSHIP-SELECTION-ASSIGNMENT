# Movie Reasoning Agent: Agentic RAG Implementation

This repository contains an advanced **Agentic Retrieval-Augmented Generation (RAG)** system designed for deep reasoning over a hybrid movie dataset. The system utilizes the **ReAct (Reasoning + Acting)** pattern to dynamically interact with structured databases, unstructured document indices, and real-time web search.

## 1. System Overview

The agent is designed as a "Reasoning Engine" that solves multi-domain queries by bridging disparate data sources. It treats movie analysis as a search-space problem, escalating through tools in a prioritized order:
1. **Internal Structured Data**: SQLite for financial metrics and metadata.
2. **Internal Unstructured Data**: BM25-based semantic retrieval for thematic critiques.
3. **Web Fallback**: Real-time retrieval via Tavily for fringe facts or recent updates.

## 2. Technical Stack

- **Reasoning Loop**: Azure AI Inference SDK (Powered by GitHub Models / GPT-4o-mini).
- **Structured Retrieval**: SQLite + Pandas.
- **Unstructured Retrieval**: Rank-BM25 on localized movie review documents.
- **Web Search**: Tavily Search API.
- **State Management**: Persistent JSON-based trace caching for cost and latency optimization.

## 3. Quick Start (Setup)

The project includes a single-command setup script to initialize the environment and process the data.

### **One-Step Installation**
Ensure you have Python 3.9+ and pip installed, then run:
```bash
python setup_project.py
```
This script will:
- **Create a virtual environment (`venv`)** automatically.
- Install all dependencies from `requirements.txt` into the `venv`.
- Execute `preprocess.py` using the `venv` interpreter to bridge the raw datasets into a queryable SQLite database and BM25 document collection.

### **Configuration**
Create a `.env` file in the root directory:
```bash
GITHUB_TOKEN=your_token_here
TAVILY_API_KEY=your_key_here
```

## 4. Operational Modes

### **A. Interactive REPL (Agent)**
Continuous conversation mode with full reasoning trace visibility.
```bash
python agent/agent_loop.py
```
*Type 'exit' or 'quit' to terminate the session.*

### **B. Single Query Mode**
Execute a direct reasoning task from the command line.
```bash
python agent/agent_loop.py "Who directed the 2006 film 'The Host' and what is its Rotten Tomatoes score?"
```

## 5. Evaluation & Audit

### **20-Question Diagnostic Suite**
To verify system accuracy, grounding, and safety, run the comprehensive evaluation suite:
```bash
python task_D_20eval_test.py
```
Aggregated results are saved to `evaluation/task_D_results.json`.

### **Corpus Degradation Audit (Resilience Test)**
This script verifies the system's ability to maintain accuracy using external fallbacks when 50% of the internal document corpus is removed.
```bash
python degradation_runner.py
```

## 6. Known Failure Modes & Limitations

An honest assessment of the current architecture identifies the following behavior boundaries:

1. **Safety-Helpfulness Drift**: In "Refusal" scenarios (e.g., medical or financial advice), the model occasionally provides general news trends from the web before stating a refusal. This is an artifact of the "Helpfulness" instruction in the underlying LLM.
2. **Semantic Entity Conflict**: Queries for generic titles (e.g., "The Host") may resolve to different film versions if not explicitly disambiguated in the user prompt.
3. **Token Budget Truncation**: For extremely large SQL result sets (>100 rows), only the top results are prioritized for reasoning to prevent context window overflow.
4. **Step Budget Hard Cap**: The agent is strictly limited to **8 tool calls** to prevent infinite recursion in loops. Queries requiring deeper chains will terminate with an error.

---

## 7. AI Disclosure
This project was co-developed with **Antigravity**, a powerful AI coding agent. Architectural decisions, multi-tool orchestration logic, and forensic audit runners were pair-programmed to ensure high-fidelity reproducible code.
