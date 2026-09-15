# AI-Assisted Contract-to-Billing Reconciliation Engine

An enterprise-grade, portfolio-ready **Contract-to-Billing Reconciliation Engine** built for Finance AI / AI Engineer case studies. Demonstrates the practical combination of **deterministic financial logic**, **Retrieval-Augmented Generation (RAG)**, **vector databases**, **multi-strategy matching**, **explainable confidence scoring**, and **Human-in-the-Loop review** with an immutable compliance audit trail.

---

## 🎯 1. Business Problem

In enterprise finance operations, accounts payable and billing teams must verify whether customer invoices comply with complex contractual agreements (Master Services Agreements, Statements of Work, and Service Orders).

### Typical Failure Scenarios:
- **Omitted Contractual Discounts**: Contract specifies a 10% discount for the first year, but invoice bills full gross amount.
- **Quantity & Rate Drift**: Overbilled unit counts or incorrect baseline tier rates.
- **Contract Expiry & Date Anomalies**: Invoices submitted after contract termination or before the effective date.
- **Unhedged Currency Inconsistencies**: Contracts agreed in USD billed in EUR or INR without forex approval.
- **Duplicate Invoices**: Resubmitted or overlapping billing cycles.
- **Entity Name Variations**: Invoices citing "Apex Logistics Corporation" vs contractual entity "Apex Logistics Corp".

**Core Principle**: A finance system must **never allow an LLM to hallucinate arithmetic**. Python must compute exact variances, while AI retrieves evidence, explains discrepancies, and recommends action.

---

## 🏗️ 2. Architectural Philosophy: Who Does What?

| Responsibility Layer | System Component | What it Does | Why This Choice? |
| :--- | :--- | :--- | :--- |
| **Deterministic Python** | `app/matching/` & `app/reconciliation/` | Data normalization, exact ID/currency matches, arithmetic variance math ($ & %), tolerance thresholds, date window validation, duplicate checks. | Zero hallucination risk, exact auditability, sub-millisecond execution. |
| **Fuzzy Matching** | `app/matching/fuzzy_matcher.py` (RapidFuzz) | Customer name variations (e.g. Inc vs Incorporated), service token sorting, alias resolution. | Bridges messy real-world invoice naming to official legal contract parties. |
| **Document Ingestion** | `app/rag/ingestion.py` (PyMuPDF) | Extracts page numbers, clause categories, and paragraphs from executed PDF contracts. | Preserves document geometry and exact page citations for legal defensibility. |
| **Vector Database & RAG** | `app/rag/vector_store.py` (ChromaDB + MiniLM-L6-v2) | Embedded semantic search over contract clauses and corporate billing policies. | Grounded retrieval: finds specific discount rules, tiered overage policies, and SLA terms. |
| **AI Reasoning & Explanation** | `app/rag/chain.py` (LangChain) | Formulates 5-part root cause analysis: What Happened, Why It Happened, What Contract Says, Citations, Recommended Action. | Transforms dry numbers into actionable, plain-English finance executive narratives. |
| **Explainable Confidence** | `app/reconciliation/confidence.py` | Transparent multi-factor formula: ID (30%) + Amount (35%) + Date (15%) + Name (10%) + Evidence (10%). | Not a black-box LLM number. Explainable to regulators and audit committees. |
| **Human-in-the-Loop (HITL)** | `app/database/` & `streamlit_app.py` | Authoritative clearance: Accept, Reject, Override. Immutable audit trail logging. | System never silently clears material money without authorized finance sign-off. |

---

## 🔄 3. Architecture & Data Flow Diagram

```
Executed Contract PDFs              Vendor / Customer Invoices (CSV/Excel)
         │                                              │
         ▼                                              ▼
PyMuPDF Text & Page Extraction                Field & Entity Normalization
         │                                              │
         ▼                                              ▼
Clause Categorization & Chunking             Multi-Strategy Matching Engine
         │                                    ├── Exact Matcher (IDs, Currency)
         ▼                                    ├── Tolerance Matcher (Math & Dates)
ChromaDB Vector Store                         └── Fuzzy Matcher (RapidFuzz Names)
         │                                              │
         └───────────────┬──────────────────────────────┘
                         ▼
             Reconciliation Orchestrator
         ├── Deterministic Variance Calculations
         ├── Explainable Confidence Scoring (30/35/15/10/10)
         └── RAG Contract Clause Evidence Retrieval
                         │
                         ▼
             Result Classification
         ├── MATCHED (Auto-Approved)
         └── UNMATCHED / PROBABLE / DUPLICATE (Exception)
                         │
                         ▼
             Human-in-the-Loop Review
         ├── ACCEPT (with mandatory comment)
         ├── REJECT (dispute notice)
         └── OVERRIDE (adjusted baseline)
                         │
                         ▼
             Immutable Audit Trail
                         │
                         ▼
             Executive Dashboard & ROI
```

---

## 🧮 4. Multi-Strategy Matching Logic

The reconciliation engine employs four distinct matching tiers:

### A. Exact Key Matching
- Validates `contract_id`, `customer_id`, `currency`, and `reference_number`.
- Handles ISO currency normalization (e.g., `$`, `USD`, `US Dollar` -> `USD`).

### B. Deterministic Tolerance Matching
- Calculates Expected Contract Amount:
  $$\text{Subtotal} = \text{Quantity} \times \text{Unit Price}$$
  $$\text{Discount Amount} = \text{Subtotal} \times \left(\frac{\text{Discount \%}}{100}\right)$$
  $$\text{Expected Amount} = \text{Subtotal} - \text{Discount Amount}$$
- Computes Absolute Variance: $|\text{Actual} - \text{Expected}|$
- Computes Percentage Variance: $\frac{|\text{Actual} - \text{Expected}|}{\text{Expected}} \times 100$
- Evaluates against permissible contract tolerance:
  $$\text{Within Tolerance} \iff (\text{Variance \%} \le \text{Tolerance \%}) \lor (\text{Variance \$} \le \text{Tolerance \$})$$

### C. Fuzzy & Semantic Entity Resolution
- Evaluates `rapidfuzz.token_sort_ratio` and `token_set_ratio` after stripping legal company suffixes (`Inc.`, `Corp`, `LLC`, `Pvt Ltd`).
- Resolves candidate contracts even when an invoice omits the contract ID.

### D. Semantic RAG Grounding
- Embeds contract clauses into ChromaDB using ONNX `all-MiniLM-L6-v2`.
- Semantically queries the contract to retrieve applicable discounts, overage thresholds, and billing policies.
- Guardrail: Returns `"Insufficient contractual evidence."` if no relevant clause exists.

---

## 📊 5. Explainable Confidence Scoring Model

Rather than asking the LLM to hallucinate a confidence score, the engine computes a transparent, auditable score:

$$\text{Confidence} = 0.30 \cdot S_{\text{id}} + 0.35 \cdot S_{\text{amount}} + 0.15 \cdot S_{\text{date}} + 0.10 \cdot S_{\text{name}} + 0.10 \cdot S_{\text{evidence}}$$

Every reconciliation record includes the exact breakdown list of factors contributing to the score.

---

## 📁 6. Project Structure

```
contract-billing-ai/
│
├── app/
│   ├── config.py                   # Environment settings & fallback defaults
│   ├── core/
│   │   └── models.py               # Pydantic schemas (Contracts, Invoices, Audit)
│   ├── database/
│   │   └── db.py                   # SQLite persistence & audit log queries
│   ├── rag/
│   │   ├── ingestion.py            # PDF clause extraction with PyMuPDF
│   │   ├── vector_store.py         # ChromaDB persistent vector manager
│   │   └── chain.py                # LangChain retrieval & 5-part AI explanation
│   ├── matching/
│   │   ├── normalizer.py           # Text, currency, and date normalization
│   │   ├── exact_matcher.py        # Exact key matching
│   │   ├── tolerance_matcher.py    # Arithmetic variance & tolerance checks
│   │   ├── fuzzy_matcher.py        # RapidFuzz customer name similarity
│   │   └── engine.py               # Multi-strategy matching orchestrator
│   ├── reconciliation/
│   │   ├── engine.py               # Reconciliation orchestrator
│   │   └── confidence.py           # Explainable confidence scoring formula
│   └── frontend/
│       └── styles.py               # Modern Dark/Slate CSS styling tokens
│
├── data/
│   ├── contracts/                  # 15 synthetic PDF contracts (ReportLab)
│   ├── invoices/                   # Synthetic invoices CSV
│   ├── policies/                   # Corporate billing & tolerance policies
│   └── chromadb/                   # Persistent vector store index
│
├── generate_data.py                # Generates 15 PDF contracts + 120+ edge-case invoices
├── run_demo.py                     # CLI quickstart demonstration script
├── streamlit_app.py                # Main interactive Streamlit application
├── tests/
│   ├── test_matching.py            # Normalization, exact, tolerance, and fuzzy tests
│   ├── test_reconciliation.py      # Classification, expired contract, and discount tests
│   └── test_rag_and_audit.py       # RAG retrieval and audit trail tests
├── pytest.ini                      # Pytest configuration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
└── README.md                       # Documentation & Interview guide
```

---

## 🚀 7. How to Run the Application

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Git

### 2. Installation
```bash
# Clone the repository
git clone <repo-url>
cd "contract to billing reconcillation"

# Install dependencies
pip install -r requirements.txt
```

### 3. Generate Datasets & Run CLI Demo
```bash
# Generates 15 PDF contracts, ChromaDB vector clauses, and 120+ invoices
python generate_data.py

# Run the complete end-to-end CLI demonstration
python run_demo.py
```

### 4. Launch Interactive Streamlit Dashboard
```bash
streamlit run streamlit_app.py
```
Open your browser at `http://localhost:8501`.

### 5. Run Automated Test Suite
```bash
python -m pytest tests/ -v
```
All 20 unit tests pass in under 3 seconds.

---

## 🧪 8. Synthetic Dataset & Edge Cases Tested

The synthetic generator (`generate_data.py`) creates 15 multi-page PDF contracts and 122 invoice records covering:
1. **Exact Match**: Fully compliant invoices matching all terms.
2. **Tolerance Within Limit**: Minor variance (0.4%) within 1.0% margin.
3. **Variance Beyond Tolerance**: Material discrepancy (e.g. 12% overcharge).
4. **Missing Contract Reference**: Invoice omitting contract ID or citing non-existent contract.
5. **Duplicate Invoices**: Identical billing period, customer, and amount resubmitted.
6. **Wrong Discount**: Contract stipulates 10% discount, but invoice billed at gross.
7. **Wrong Quantity**: Billed for 130 seats instead of contracted 100 seats.
8. **Currency Mismatch**: USD contract billed in EUR or GBP.
9. **Customer Name Variation**: "Acme Global Corporation Inc" vs "Acme Global Corp".
10. **Contract Expired**: Invoices dated after contract termination date.
11. **Pre-Contract Date**: Invoices dated prior to effective date.
12. **Data Quality Exception**: Invoices with missing customer names or negative amounts.

---

## 💡 9. Interview Talking Points

When presenting this project in an interview, emphasize:

### Q: "Why not use an LLM Agent for the entire reconciliation?"
> **Answer**: *"Financial systems require strict auditability and mathematical correctness. LLMs are non-deterministic and can hallucinate arithmetic. We decouple the problem: Python calculates the exact financial variance ($ and %), while RAG and LLM reasoning interpret legal text, retrieve contract evidence, and explain the discrepancy to the finance user."*

### Q: "How does the Human-in-the-Loop workflow operate?"
> **Answer**: *"The AI engine classifies exceptions and provides recommendations with direct page citations. A human reviewer must explicitly click Accept, Reject, or Override with a mandatory justification comment. Every action is logged into an immutable SQLite audit trail with timestamps and reviewer identity."*

### Q: "How does the system ensure fast, low-cost performance?"
> **Answer**: *"By using local ONNX embeddings (all-MiniLM-L6-v2) and ChromaDB, the system operates with zero external network latency and zero per-call API cost. For production, it can seamlessly switch to OpenAI or Gemini via `.env`."*

---

## ⚖️ 10. Limitations & Future Roadmap
- **OCR for Scanned PDFs**: Current ingestion uses PyMuPDF for native digital PDFs; adding Tesseract OCR / Azure Document Intelligence would enable scanned paper support.
- **ERP Integration**: Webhook connectors to NetSuite, SAP, and Workday for direct posting of approved reconciliations.
- **Multi-Line Item Splitting**: Support complex line-level many-to-one tax and shipping reconciliations.
