# Movie Reasoning Agent: Agentic RAG System
**Repo URL:** [https://github.com/Anish-Ramesh/INTERNSHIP-SELECTION-ASSIGNMENT](https://github.com/Anish-Ramesh/INTERNSHIP-SELECTION-ASSIGNMENT)

An advanced **Agentic Reasoning RAG system** designed to solve complex, multi-tool movie queries. Built on a modular reasoning architecture (ReAct), this system integrates structured SQL data, unstructured document search, and real-time web retrieval to provide grounded, citation-heavy answers.

---

## 1. Technology Stack

- **Language**: Python 3.9+
- **Inference**: [GitHub Models](https://github.com/marketplace/models) (Azure AI Inference SDK)
- **Architecture**: Modular ReAct (Reasoning + Acting) pattern
- **Retrieval Engine**:
  - **Structured**: SQLite (via Pandas SQL interface)
  - **Unstructured**: BM25 (Rank-BM25)
  - **Web**: Tavily Search API
- **Data Handling**: Pandas, JSON, CSV
- **Security**: Gitleaks (Credentials Scanning)

---

## 2. Core Architecture: Modular Agent Design

This project utilizes a **Modular Agent Architecture** to ensure high readability and reproducibility:
- **Separation of Concerns**: Agent logic, tools, data handlers, and evaluation modules are strictly distinct.
- **Traceability**: Every reasoning step is logged with rationales, inputs, and outputs in high-fidelity JSON.
- **Scaleability**: Independent tools allow for easy integration of new data sources without modifying the core agent loop.

---

## 3. Dataset Sources

The system is grounded in a hybrid dataset curated from the following sources:
1. **Unstructured Reviews**: [Rotten Tomatoes Movie & Critic Reviews](https://www.kaggle.com/datasets/stefanoleone992/rotten-tomatoes-movies-and-critic-reviews-dataset?select=rotten_tomatoes_movies.csv)
2. **Structured Metadata**: [Top 1000 Movies by Worldwide Gross](https://www.kaggle.com/datasets/crisleyoliveira/top1000moviesgross)

---

## 4. Setup & Installation

### **Prerequisites**
- Python 3.9+
- [GitHub Personal Access Token](https://github.com/settings/tokens) (for GitHub Models)
- [Tavily API Key](https://tavily.com/) (for web search)

### **Installation Guide**
For Windows (PowerShell), MacOS (Terminal), or Linux (Bash):
1. **Clone the repository**:
   ```bash
   git clone https://github.com/Anish-Ramesh/INTERNSHIP-SELECTION-ASSIGNMENT
   cd INTERNSHIP-SELECTION-ASSIGNMENT
   ```
2. **Setup virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### **Configure Environment**
Create a `.env` file from the example:
```bash
cp .env.example .env
# Edit .env with your GITHUB_TOKEN and TAVILY_API_KEY
```

---

## 5. Execution & Analysis

### **1. Data Preprocessing**
Initialize the local database and document indices:
```bash
python preprocess.py
```

### **2. Running the Agent**
Execute single-query reasoning from the CLI:
```bash
python agent/agent_loop.py "Who directed Oppenheimer and what is their most recent project?"
```

### **3. Comprehensive Evaluation**
Run the 20-question diagnostic suite:
```bash
python task_D_test.py
```

### **4. Corpus Resilience Analysis**
Verify system performance under data loss (50% corpus):
```bash
python agent/degradation_runner.py
```
*Tip: This runner compares "Normal" vs "Degraded" performance to validate web-fallback reliability.*

---

## 6. Project Structure

```text
.
├── agent/
│   ├── agent_loop.py        # Core reasoning loop
│   ├── bonus_features.py    # Telemetry & Reflection recovery
│   ├── degradation_runner.py# Corpus resilience analyzer
│   └── response_cache.json  # Persistent full-trace caching
├── dataset/
│   ├── unstructured_reviews/# Source .txt review files
│   ├── movies_structured.csv# Filtered SQL dataset
│   ├── top1000movies.csv     # Raw structured source
│   └── rotten_tomatoes_movies.csv # Raw unstructured source
├── evaluation/
│   ├── logs/                # Step-by-step reasoning traces
│   ├── task_D_results.json  # Evaluation suite metrics
│   └── degradation_comparison.json # Resilience audit data
├── tools/
│   ├── query_data.py        # SQLite interface
│   ├── search_docs.py       # BM25 RAG interface
│   └── web_search.py        # Tavily interface
├── utils/
│   └── logger.py            # Trace management
├── task_A_test.py           # Single-tool verification script
├── task_B_test.py           # Multi-tool verification script
├── task_C_test.py           # Cross-dataset verification script
├── task_D_test.py           # 20-question evaluation runner
├── preprocess.py            # Ingestion & Indexing script
├── requirements.txt         # Project dependencies
├── .env.example             # Template for API credentials
├── .gitignore               # Standard exclusions (venv, __pycache__)
├── EVALUATION.md            # Comprehensive test analysis report
├── Degradation_Audit_Report.md # Resilience & Forensic audit
├── tool_cost_analysis.md    # Token usage & Budget telemetry
└── README.md                # (You are here)
```

---

## 7. Key Audit & Evaluation Reports

The system includes three comprehensive reports documenting performance, cost, and resilience:

### **[1. Evaluation Report (EVALUATION.md)](file:///c:/Users/Anish/OneDrive/Documents/Prodapt/INTERNSHIP-SELECTION-ASSIGNMENT/EVALUATION.md)**
- **Focus**: Accuracy across 20 diverse reasoning questions.
- **Key Takeaway**: Achieved a **75% success rate** with 100% grounding for retrieved facts. 
- **Features**: Detailed ReAct traces for every answer and a breakdown of failure modes (Safety Drift).

### **[2. Degradation Audit (Degradation_Audit_Report.md)](file:///c:/Users/Anish/OneDrive/Documents/Prodapt/INTERNSHIP-SELECTION-ASSIGNMENT/Degradation_Audit_Report.md)**
- **Focus**: Forensic analysis of system behavior with **50% corpus removal**.
- **Key Takeaway**: Proved **100% Accuracy Retention** by successfully automating web-fallback when internal reviews were missing.
- **Features**: Before/After step-count comparisons and delta behavioral analysis.

### **[3. Tool Cost Analysis (tool_cost_analysis.md)](file:///c:/Users/Anish/OneDrive/Documents/Prodapt/INTERNSHIP-SELECTION-ASSIGNMENT/tool_cost_analysis.md)**
- **Focus**: Operational telemetry, token consumption, and budget mapping.
- **Key Takeaway**: Project spend remains **< 10% of the ₹1,500 budget**, largely due to **Persistent Full-Trace Caching**.
- **Features**: Per-tool latency tracking and estimated USD cost-per-query.

---

## 8. Security & Compliance
The codebase has been scanned for potential secrets and vulnerabilities:
```bash
gitleaks detect --source . -v
# Result: 8 commits scanned. No leaks found.
```

---

## 9. AI Disclosure
Developed with the assistance of the **Antigravity AI Agent** and **ChatGPT**. Architectural decisions, tiered escalation logic, and diagnostic runners were pair-programmed and verified for technical accuracy.
