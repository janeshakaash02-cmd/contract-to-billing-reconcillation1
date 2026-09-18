# ⚡ NEXUS RECON: The "Explain Like I'm 5" (ELI5) Step-by-Step Guide

Welcome to **NEXUS RECON**! This guide is written in plain, friendly English so anyone—from a finance intern to an executive or software engineer—can download, run, and master the application in under 10 minutes.

---

## 🐣 What Is This App? (ELI5 Analogy)

Imagine you go to a restaurant with a printed menu that says:
> *"Pizza is $10, and if you are a club member, you get 10% off ($9 total)."*

When the waiter brings the bill, it says **$12.50**. 

If you are super busy, you might not notice and just pay it. Over a whole year, you would lose hundreds of dollars on mistakes like this!

**NEXUS RECON is like having an ultra-smart robot accountant standing next to you:**
1. It reads all your official signed vendor contracts (the menus).
2. It reads every invoice that comes in (the bills).
3. It does the exact math in milliseconds to make sure the rates, quantities, discounts, and dates match.
4. If a bill is wrong, it alerts you, explains *why* it's wrong in plain English using **LangChain AI**, quotes the exact contract page, and lets you approve or dispute it with one click!

---

## 💻 System Requirements

Before you start, make sure you have:
1. **Python 3.10, 3.11, or 3.12** installed on your computer.
   - You can verify by opening your terminal or command prompt and typing:
     ```bash
     python --version
     ```
2. **Git** (optional, but recommended for cloning the repository).
3. A web browser (Google Chrome, Firefox, Edge, or Safari).

---

## 🚀 How to Download & Run Step-by-Step

### Step 1: Open Your Terminal
- **Windows**: Press `Win + R`, type `powershell` or `cmd`, and press **Enter**.
- **Mac / Linux**: Open the **Terminal** app.

### Step 2: Download / Clone the Repository
If you haven't downloaded the project yet, run:
```bash
git clone https://github.com/janeshakaash02-cmd/contract-to-billing-reconcillation1.git
cd contract-to-billing-reconcillation1
```
*(Or if you already have the folder, simply navigate into it, e.g., `cd e:\contract`)*.

### Step 3: Create & Activate a Virtual Environment
A virtual environment keeps the project's dependencies isolated and tidy:
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
python -m venv venv
.\venv\Scripts\activate.bat

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies
Install all required libraries (Streamlit, Pandas, Plotly, RapidFuzz, LangChain, PyMuPDF, etc.):
```bash
pip install -r requirements.txt
```

### Step 5: (Optional) Set Up Your AI Key
The app works **100% offline out-of-the-box** using deterministic semantic retrieval! 

If you would like to connect a live cloud LLM (like Groq's superfast Llama 3.3 or OpenAI):
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` in any text editor and add your free Groq API key:
   ```env
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_your_actual_key_here
   LLM_MODEL=llama-3.3-70b-versatile
   ```

### Step 6: Launch the App!
Run this single command in your terminal:
```bash
streamlit run app.py
```
Your web browser will automatically open to:
👉 **`http://localhost:8501`**

---

## 🗺️ How to Use Every Section of the App (Tour Guide)

On the left-hand sidebar, you will see a navigation menu with **9 interactive sectors**. Here is what each one does and how to use it:

```
┌─────────────────────────────────────────────────────────────┐
│                      NEXUS RECON MENU                       │
├─────────────────────────────────────────────────────────────┤
│  📊 Executive Dashboard        (High-level KPI metrics)     │
│  🧪 'What-If' Sandbox          (Simulate billing errors)    │
│  ⚡ Engine Runner              (Batch processing & CSV)     │
│  📋 Exception Queue            (Triage & batch approvals)   │
│  🔍 Visual Diff & Review       (Side-by-side & AI audits)   │
│  📑 Contract Explorer          (Ask contracts questions)    │
│  💰 ROI Simulator              (Labor & cash savings calc)  │
│  📜 Compliance Audit           (Immutable audit trail log)  │
│  ℹ️ Architecture Guide         (Engineering mechanics)      │
└─────────────────────────────────────────────────────────────┘
```

---

### Sector 1: 📊 Executive Dashboard (The Cockpit)
- **What it is**: The high-level command center for CFOs and Finance Directors.
- **What you see**:
  - **KPI Cards**: Total Ingested Invoices, Auto-Match Rate (e.g. 78%), Total Financial Exposure at risk ($), and Labor Hours Saved.
  - **Interactive Sankey Diagram**: Shows bills flowing from "Ingested Feed" &rarr; "Exact Match" or "Tolerance Match" &rarr; "Exceptions".
  - **Portfolio Breakdown Donut Chart**: Proportions of Matched vs Unmatched bills.
  - **Urgent Action Items**: Quick table showing the largest at-risk invoices needing review.

---

### Sector 2: 🧪 'What-If' Simulation Sandbox (The Testing Lab)
- **What it is**: A playground where you can test how the AI engine reacts to invoice errors.
- **How to use it**:
  1. Pick an agreement from the dropdown (e.g., *Starlight Media Group*).
  2. Move the sliders: change the **Unit Price**, increase the **Quantity**, or zero-out the **Discount**.
  3. Pick a date anomaly (e.g. *"Post-Expiry"* or *"Pre-Contract"*).
  4. Notice the **Live Outcome Banner** instantly update:
     - 🟢 **MATCHED**: When variance is $0.
     - 🔵 **PROBABLE MATCH**: When difference is within the contract's tolerance (e.g. within ±1% or $50).
     - 🔴 **EXCEPTION**: When someone overcharged or billed outside the contract dates!
  5. Click **"📥 Commit Simulated Invoice to Database for Full Audit"** to save your simulation into the audit ledger!

---

### Sector 3: ⚡ Engine Runner & Live Terminal (The Engine Room)
- **What it is**: Where bulk invoice reconciliation actually happens.
- **Features**:
  - **Summary Cards**: Displays how many invoices and contracts are currently in the system.
  - **🚀 Trigger Full Batch Reconciliation**:
    - Click this button and watch the **progress bar** advance.
    - Below the progress bar, a **live cyber terminal** streams invoice-by-invoice updates with color-coded status badges, dollar variance, and confidence score.
  - **📂 Upload Custom Invoices (CSV)**:
    - Have your own billing spreadsheet? Drag and drop your `.csv` file here!
    - The app previews your records.
    - Click **"Ingest and Reconcile Uploaded CSV"** and the system will run all checks against your contracts immediately!

---

### Sector 4: 📋 Exception Queue & Batch Triage (The Sorting Hat)
- **What it is**: The workbench where finance auditors review flagged invoices.
- **How to use it**:
  - **Filter Controls**: Filter by Status (Matched, Unmatched, Duplicate), Priority (High, Med, Low), or Search by customer name.
  - **⚡ Quick Batch Actions**:
    - **"✅ Batch-Approve In-Tolerance Records (<$100)"**: Automatically approves all tiny differences within allowable limits with a single click.
    - **"🚨 Batch-Reject Pre/Post Contract Invoices"**: Bulk-rejects invoices sent outside valid contract dates.
    - **"📥 Export Current View to CSV"**: Downloads the filtered list into an Excel/CSV spreadsheet for offline reporting.

---

### Sector 5: 🔍 Side-by-Side Visual Diff & Review (The Detective Room)
- **What it is**: Deep forensic inspection for a single invoice.
- **What you see**:
  - **Left Card (Contract Baseline)** vs **Right Card (Billed Invoice)**: Colors highlight differences (e.g., billed $10,000 vs agreed $9,000).
  - **🔬 Explainable Confidence Breakdown**:
    Shows why the system is confident (ID Match 30% + Amount Match 35% + Date Match 15% + Name Match 10% + Evidence 10%).
  - **🧠 LangChain 5-Part Root Cause Analysis**:
    1. *What Happened?*
    2. *Why Did It Happen?*
    3. *What Does The Contract Say?*
    4. *What Should The Reviewer Do?*
    5. *Retrieved Contract Citations* (e.g., `[Contract CTR-1001, Page 2]`).
  - **✍️ Human Clearance Form**:
    - Select **ACCEPT**, **REJECT**, or **OVERRIDE**.
    - If you select OVERRIDE, type the approved dollar amount.
    - Enter your name and audit comment, then click **"Commit Review Decision & Sign Off"**. This permanently updates the invoice and writes to the audit log!

---

### Sector 6: 📑 Contract Explorer & LangChain RAG (The Library)
- **What it is**: Read contracts and "chat" with them using semantic AI.
- **How to use it**:
  - Select any contract from the dropdown.
  - View the contract's base price, capacity, discount rates, and expiry date.
  - **Click any of the Quick Prompt Buttons**:
    - *"What is the contracted monthly billing rate?"*
    - *"What discount terms and concessions apply?"*
    - *"When does this agreement terminate?"*
  - Or type your own question in the box! LangChain reads the contract PDF chunks from the vector database and provides a grounded answer with page numbers.
  - Below that, you can see all historical invoices billed against this specific contract.

---

### Sector 7: 💰 ROI & Labor Savings Simulator (The Cash Register)
- **What it is**: Calculate how much money and time this software saves an enterprise.
- **How to use it**:
  - Adjust the 4 sliders:
    - Monthly Invoice Volume (e.g., 1,500 bills/month)
    - Manual Audit Minutes per Invoice (e.g., 15 minutes)
    - Auditor Hourly Rate (e.g., $45/hour)
    - Target Auto-Match Rate (e.g., 85%)
  - Watch the **Annual Labor Saved**, **Net Annual Savings ($)**, and **FTEs Reclaimed** update in real time!
  - Look at the **12-Month Cumulative Financial Savings Projection** chart to see the payback period (< 1 month).

---

### Sector 8: 📜 Compliance Audit Trail & Governance (The Vault)
- **What it is**: The legally defensible, SOX 404 & SOC 2 compliant tamper-evident ledger of every event.
- **Why Can't Humans Directly Edit Past History?** Under financial compliance (SOX 404 & GAAP), historical audit logs **must be strictly immutable** (write-once, append-only). Allowing someone to delete or overwrite past actions would create fraud vulnerabilities and fail regulatory audits.
- **How Humans CAN Edit & Annotate (Auditor Addendum)**:
  - Open **"✍️ Human Auditor Action Center: Append Official Addendum or Compliance Memo"**.
  - Select any Invoice ID, choose an Addendum Type (`AUDITOR_ADDENDUM`, `SECONDARY_SIGN_OFF`, `POLICY_EXCEPTION_MEMO`, `LEGAL_DISPUTE_ESCALATION`, `ARITHMETIC_CORRECTION_NOTE`), type your name and mandatory compliance justification, and submit.
  - An official, immutable addendum is permanently appended to the ledger!
- **Inspection & Filtering**:
  - **KPI HUD**: Live counts of Total Events, AI Autonomous Runs, Human Sign-Offs, and Auditor Addendums.
  - **Filters**: Filter by Actor (`ALL`, `AI_ENGINE`, or specific human auditors), Action Type, or Invoice ID.
  - **Lifecycle Trace**: Select any invoice to inspect its complete chronological chain of custody from ingestion to final sign-off.
  - **Export**: Download the filtered ledger anytime as a CSV spreadsheet.

---

### Sector 9: ℹ️ Architecture & Interview Guide (The Blueprint)
- **What it is**: The technical reference explaining how the engine was designed:
  - *Rule #1: Never let an LLM do basic math that Python can calculate deterministically!*
  - Complete matrix explaining what Python, RapidFuzz, PyMuPDF, ChromaDB, LangChain, and SQLite do.
  - End-to-end dataflow pipeline diagram.

---

## 🧠 Where Do Confidence Scores & Human Actions Come From? (ELI5 Breakdown)

### 1. 🎯 What is the Confidence Score and where does it come from?
The Confidence Score is **NOT** an arbitrary number or an LLM hallucination. It is calculated by a strict, explainable mathematical formula combining 5 weighted evidence tiers:

$$\text{Confidence Score} = (0.30 \times \text{ID}) + (0.35 \times \text{Amount}) + (0.15 \times \text{Date}) + (0.10 \times \text{Name}) + (0.10 \times \text{Evidence})$$

| Factor | Weight | What It Checks |
| :--- | :---: | :--- |
| 🏷️ **ID Match** | **30%** | Does the invoice have an exact match for Contract ID (`CTR-XXXX`) or Customer ID? |
| 💵 **Amount Match** | **35%** | Does the billed total match the contract rate, or is it within the allowed tolerance (±1% / $50)? |
| 📅 **Date Match** | **15%** | Was the invoice submitted during the valid contract term (not expired or pre-contract)? |
| 🏢 **Name Similarity** | **10%** | RapidFuzz fuzzy matching score (e.g., *Acme Corp* vs *Acme Corporation*). |
| 📜 **Evidence Grounding**| **10%** | Did the LangChain vector database retrieve the exact contract clause text and page citation? |

If an invoice is a perfect match across all 5 checks, its score is **95% to 99%**. If it has missing contract references or pricing variances, the score reflects precisely which factors failed.

---

### 2. ✍️ Where is the Human Action Section and what does it do?
**Human Action** is the "Human-in-the-Loop" (HITL) compliance mechanism. An AI should never silently spend company money without human oversight!

Whenever an invoice has a discrepancy, it is placed in **PENDING** review status. You can take authoritative Human Action in **two places**:
1. **Directly in Sector 3 (`⚡ Engine Runner & Human Actions`)**: Right under the reconciliation terminal, select any invoice in the quick inspector and submit your decision.
2. **In Sector 5 (`🔍 Visual Diff & Deep Review`)**: For deep side-by-side forensic analysis.

#### The 3 Human Actions You Can Take:
1. **`ACCEPT` (Approve for Payment)**:
   - Use this when an invoice variance is harmless or verbally authorized.
   - The invoice status changes to **MATCHED** and clears for payment.
2. **`REJECT` (Dispute Invoice)**:
   - Use this when a vendor overcharged, billed outside contract dates, or sent an unrecognized bill.
   - The invoice is blocked and marked for a dispute or credit note request.
3. **`OVERRIDE` (Adjust Approved Amount)**:
   - Use this when you want to legally approve an adjusted baseline (e.g. approve $9,000 instead of the billed $10,000).
   - Enter the override amount and mandatory comment.

Every action requires your name and an **Audit Justification Comment**, and is recorded forever into the immutable Compliance Audit Trail!

---

## 📥 Sample CSV Format for Custom Invoices

If you want to test the **Upload Custom Invoices (CSV)** feature in Sector 3, make sure your CSV file has headers like this:

```csv
invoice_id,contract_id,customer_id,customer_name,invoice_date,billing_period,currency,quantity,unit_price,discount,tax,total_amount,reference_number
INV-TEST-01,CTR-1001,CUST-201,Acme Corporation,2025-03-15,2025-03,USD,1,10000.0,1000.0,0.0,9000.0,PO-9821
INV-TEST-02,CTR-1002,CUST-202,Omni Global Tech,2025-03-15,2025-03,USD,5,1200.0,0.0,0.0,6000.0,PO-9822
```

---

## ❓ Frequently Asked Questions (FAQ)

### Q1: Where can I see which invoices need my attention?
Look at the left sidebar! You will see:
`📋 Exception Queue (⚠️ X Pending)`
And inside Sector 3 (`⚡ Engine Runner`), you will see the **Invoices Requiring Human Action** metric card and table.

### Q2: The browser says "Port 8501 is already in use"?
Streamlit is already running! You can open your existing tab at `http://localhost:8501`, or launch on a different port:
```bash
streamlit run app.py --server.port 8502
```

### Q3: How do I reset all data back to the clean original state?
In the left sidebar, click the button **"🧹 Reset & Regenerate Datasets"**. The system will regenerate synthetic contracts, re-index the vector store, re-run reconciliation, and reset the SQLite database in ~5 seconds!

### Q4: Can I run unit tests to verify the engine?
Yes! In your terminal, run:
```bash
pytest
```
You will see `20 passed` across all matching, RAG, and reconciliation test suites.

---

*Enjoy autonomous, transparent, and legally defensible finance reconciliation with NEXUS RECON!* ⚡

