# Tool Cost & Telemetry Analysis Report (Bonus B)

**Project:** Agentic RAG over Mixed Data Sources  
**Prepared By:** Anish R  
**Date:** 18-04-2026  

## 1. Overview of the Telemetry Review Process
This cost analysis was conducted by auditing the **Dual-Phase Degradation Test** logs. Each tool call performed by the agent was intercepted by the `TelemetryTracker` (Bonus B) to capture three critical metrics:
1.  **Execution Latency**: Time elapsed from tool invocation to result return.
2.  **Token Consumption**: Inbound and outbound token usage per turn, using GPT-4.1-mini pricing.
3.  **Search Credits**: Real-world API costs for external data scavenging via Tavily.

By comparing the "Baseline" run (100% data) with the "Degraded" run (50% data), we identified the fiscal impact of **Data Sparsity**—calculating how much more the agent costs when its internal knowledge is limited and it must rely on expensive web fallbacks.

---

## 2. Per-Tool Telemetry Summary

| Tool Name | Call Count (5 Qs) | Avg. Latency | Multi-Turn Token Cost (Est) | External API Cost | Total Cost Impact |
|:---|:---|:---|:---|:---|:---|
| **SQL Query** | 8 | ~0.8s | $0.0012 (~₹0.10) | $0.00 (₹0.00) | **Low** |
| **Doc Search** | 5 | ~1.2s | $0.0008 (~₹0.07) | $0.00 (₹0.00) | **Low** |
| **Web Search** | 4 | ~4.5s | $0.0120 (~₹1.01) | $0.0320 (~₹2.69) | **High** |

### **Key Metrics:**
*   **Most Frequent Tool:** `query_data` (SQL). It is our primary ground-truth source and is used to resolve ambiguity and extract core financial metrics.
*   **Most Expensive Tool:** `web_search` (Tavily). Each search costs ~$0.008 (~₹0.67), and the multi-turn reasoning required to process web snippets consumes the most LLM tokens.

---

## 3. Cost-Benefit Analysis

### **The Case for Agentic RAG**
The system currently operates at an average cost of **$0.01 (~₹0.84) per complex query**. 
*   **100% Grounding Retention**: The primary ROI justification for these costs is that the agent maintained a **100% grounding rate** during the degradation test. Even when 50% of the corpus was removed, the agent's "Refuse-to-Guess" policy (from Bonus A) and "Self-Critique" (from Bonus C) ensured that every claim remained cited.
*   **Economic Efficiency**: By prioritizing the **SQL Database** (zero external cost), we resolve 40% of queries for under **$0.001 (₹0.08)**. We only incur the **$0.016 (₹1.34)** "Web Tax" when local data is insufficient.

---

## 4. Drawbacks & Technical Solutions

| Observed Drawback | Impact | Technical Solution (Remediation) |
|:---|:---|:---|
| **High Web Latency** | Web-heavy queries (like Q5) take 10s+. | **Prompt Gating**: Only escalate to Web after a high-confidence DB "Not Found" signal to avoid redundant local doc scanning. |
| **Token Exhaustion** | Long review documents increase prompt size. | **Context Truncation**: We currently use a 1,200-character limit per result to ensure the context window remains under 128K for the GPT-4.1-mini class. |
| **Rate Limiting** | Rapid execution of 60+ questions risks TPM limits. | **Batching & Jitter**: The `task_D_subset_test` includes a 2-second sleep between queries to prevent API rejection. Persistent LLM accounts may face exhaustion after 60-80 high-depth requests; production deployments require billing-enabled accounts with higher rate limits. |

---

## 6. Budget Compliance & Caching Strategy

**Assignment Constraint:** Total API spend must remain under **₹1,500 (~$18.00 USD)**.

To ensure strict adherence to this budget without compromising the depth of reasoning or responsiveness, the following optimizations have been implemented:

### **1. Persistent Response Caching**
*   **Mechanism**: A file-based cache (`agent/response_cache.json`) stores final agent responses indexed by the user's question.
*   **Impact**: Redundant queries during development, regression testing, and evaluation now cost **$0.00 (₹0.00)**. This is critical when iterating on complex multi-turn reasoning prompts where a single query might otherwise consume several thousand tokens.

### **2. Aggressive Conciseness Policy**
*   **Mechanism**: The system prompt now explicitly instructs the `gpt-4.1-mini` model to provide direct, grounded answers without conversational filler.
*   **Impact**: Reduces outbound token counts by ~30%, directly lowering the cost of the most expensive part of the LLM transaction.

### **3. Tiered Data Escalation**
*   **Rule**: The agent is programmed to exhaust the local SQL database (free) and local documentation (free) before escalating to external search (pay-per-call).
*   **Grounding ROI**: This keeps the average cost per query at approximately **$0.005 - $0.015 (₹0.42 - ₹1.26)**, allowing for roughly **1,200 to 3,600 high-complexity queries** within the ₹1,500 budget.

---

## 7. Comprehensive Evaluation Forecast (80 Questions)

Based on the **~325 tokens** system prompt, the following projection estimates the total cost and token usage on average.

### **Token Accumulation Model (Per Question)**
| Turn # | Context Input (Prompt + History + Results) | Reasoning Output |
| :--- | :--- | :--- |
| **Turn 1** | ~375 tokens | ~200 tokens |
| **Turn 2** | ~1,075 tokens | ~200 tokens |
| **Turn 3** | ~1,775 tokens | ~200 tokens |
| **Turn 4** | ~2,475 tokens | ~200 tokens |
| **Turn 5** | ~3,175 tokens | ~300 tokens |
| **Total/Q** | **~8,875 Input Tokens** | **~1,100 Output Tokens** |

### **Projected Suite Cost (80 Questions)**
*   **Total Input Tokens**: 710,000 (0.71M)
*   **Total Output Tokens**: 88,000 (0.088M)
*   **Estimated Cost (USD)**: **~$0.16** ($0.106 input + $0.053 output)
*   **Estimated Cost (INR)**: **~₹13.40**

### **Conclusion:**
The use of **GPT-4.1-mini** allows for industrial-scale evaluation of the agent loop at **~₹0.17 per question**, ensuring that the project remains highly scalable while staying well within the ₹1,500 budget constraint.