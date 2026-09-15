import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

from app.config import (
    MANUAL_MINUTES_PER_INVOICE,
    FINANCE_HOURLY_COST,
    DEFAULT_TOLERANCE_PERCENT,
    DEFAULT_TOLERANCE_ABSOLUTE,
    LLM_PROVIDER,
    LLM_MODEL,
    EMBEDDING_PROVIDER,
)
from app.core.models import (
    ReviewDecision,
    ReconciliationStatus,
    ExceptionPriority,
    RawInvoice,
)
from app.database.db import (
    get_all_contracts,
    get_contract,
    get_all_invoices,
    save_invoices,
    get_reconciliation_results,
    get_reconciliation_result,
    update_review_decision,
    get_audit_logs,
    get_dashboard_summary_metrics,
    reset_database,
)
from app.frontend.styles import get_custom_css
from app.matching.normalizer import normalize_invoice
from app.reconciliation.engine import ReconciliationEngine
from app.rag.chain import get_rag_chain
from generate_data import generate_all_data

# Set Page Config
st.set_page_config(
    page_title="Contract-to-Billing Reconciliation Engine",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Custom Styling
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Helper function to initialize data if empty
def ensure_data_loaded():
    contracts = get_all_contracts()
    invoices = get_all_invoices()
    if not contracts or not invoices:
        with st.spinner("Initializing synthetic contracts and billing datasets..."):
            generate_all_data()
            engine = ReconciliationEngine(get_all_contracts())
            engine.reconcile_batch(get_all_invoices(), persist_to_db=True)
            st.rerun()

ensure_data_loaded()

# Sidebar Navigation & Controls
st.sidebar.title("⚖️ Finance AI Engine")
st.sidebar.caption("Contract-to-Billing Compliance Platform")

nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "📊 Executive Dashboard",
        "⚡ Reconciliation Runner",
        "📋 Exception Queue",
        "🔍 Review & Root Cause",
        "📑 Contract Explorer (RAG)",
        "📜 Audit Trail & Governance",
        "ℹ️ Architecture & Interview Guide",
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("Demo Controls")

if st.sidebar.button("🔄 Re-Run Full Reconciliation", use_container_width=True):
    with st.spinner("Re-evaluating all invoices against contractual terms..."):
        invoices = get_all_invoices()
        engine = ReconciliationEngine()
        engine.reconcile_batch(invoices, persist_to_db=True)
        st.sidebar.success("Reconciliation complete!")
        st.rerun()

if st.sidebar.button("🧹 Regenerate Synthetic Data", use_container_width=True):
    with st.spinner("Regenerating PDF contracts, vectors, and test invoices..."):
        generate_all_data()
        engine = ReconciliationEngine()
        engine.reconcile_batch(get_all_invoices(), persist_to_db=True)
        st.sidebar.success("Reset successfully!")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"**AI Provider:** `{LLM_PROVIDER}` ({LLM_MODEL})")
st.sidebar.caption(f"**Embeddings:** `{EMBEDDING_PROVIDER}` (MiniLM-L6-v2)")
st.sidebar.caption("Deterministic Math: **Python 3.12 Engine**")


# ==============================================================================
# VIEW 1: EXECUTIVE DASHBOARD
# ==============================================================================
if nav_choice == "📊 Executive Dashboard":
    st.title("📊 Executive Reconciliation Dashboard")
    st.markdown("Automated contract-to-billing compliance tracking, financial exposure, and manual labor savings.")

    metrics = get_dashboard_summary_metrics()

    # KPI Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Invoices</div>
            <div class="metric-value">{metrics['total_reconciled']}</div>
            <div class="metric-sub">100% Ingested</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Auto-Match Rate</div>
            <div class="metric-value">{metrics['auto_match_rate']}%</div>
            <div class="metric-sub">{metrics['matched']} Perfect Matches</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Financial Exposure</div>
            <div class="metric-value">${metrics['total_financial_exposure']:,.0f}</div>
            <div class="metric-sub" style="color: #F87171;">At-Risk Variance</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">High-Priority Exceptions</div>
            <div class="metric-value" style="color: #F87171;">{metrics['high_priority_exceptions']}</div>
            <div class="metric-sub">Action Required</div>
        </div>
        """, unsafe_allow_html=True)

    with c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Labor Hours Saved</div>
            <div class="metric-value" style="color: #38BDF8;">{metrics['hours_saved']}h</div>
            <div class="metric-sub" style="color: #38BDF8;">${metrics['cost_saved']:,.0f} Cost Savings</div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("ℹ️ Labor & Cost Calculation Assumptions", expanded=False):
        st.markdown(f"""
        - **Manual audit time per invoice:** `{MANUAL_MINUTES_PER_INVOICE} minutes` (based on searching contract PDFs, verifying clauses, and cross-checking lines).
        - **Finance Specialist Blended Rate:** `${FINANCE_HOURLY_COST}/hour`.
        - **Total Hours Saved Formula:** `(Auto-Matched Invoices × {MANUAL_MINUTES_PER_INVOICE}) / 60 = {metrics['hours_saved']} hrs`.
        - **Net Cost Saved Formula:** `{metrics['hours_saved']} hrs × ${FINANCE_HOURLY_COST} = ${metrics['cost_saved']:,.2f}`.
        """)

    st.markdown("### Reconciliation Performance & Risk Distribution")
    col_chart1, col_chart2 = st.columns([1, 1])

    with col_chart1:
        # Donut Chart for Statuses
        status_labels = ["Matched", "Probable Match", "Unmatched", "Duplicate", "Data Quality"]
        status_values = [
            metrics['matched'],
            metrics['probable_matches'],
            metrics['unmatched'],
            metrics['duplicates'],
            metrics['data_quality_exceptions'],
        ]
        colors_map = ["#10B981", "#3B82F6", "#EF4444", "#F59E0B", "#A855F7"]

        fig_status = go.Figure(data=[go.Pie(
            labels=status_labels,
            values=status_values,
            hole=0.55,
            marker=dict(colors=colors_map),
            textinfo='label+percent',
            hoverinfo='label+value+percent'
        )])
        fig_status.update_layout(
            title="Invoice Classification Breakdown",
            template="plotly_dark",
            margin=dict(t=40, b=20, l=20, r=20),
            height=320,
            showlegend=False
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with col_chart2:
        # Top Exception Categories Bar Chart
        if metrics['top_reasons']:
            df_reasons = pd.DataFrame(metrics['top_reasons'])
            # Shorten label for clean chart
            df_reasons["short_reason"] = df_reasons["reason"].apply(lambda x: x[:36] + "..." if len(x) > 36 else x)
            fig_reasons = px.bar(
                df_reasons,
                x="count",
                y="short_reason",
                orientation='h',
                color="exposure",
                color_continuous_scale="Reds",
                labels={"count": "Number of Invoices", "short_reason": "Exception Reason", "exposure": "Exposure ($)"},
                title="Top Exceptions by Frequency & Financial Exposure"
            )
            fig_reasons.update_layout(
                template="plotly_dark",
                margin=dict(t=40, b=20, l=20, r=20),
                height=320,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_reasons, use_container_width=True)
        else:
            st.info("No active exceptions currently recorded.")

    # High Priority Exceptions Table
    st.markdown("### 🚨 Urgent Action Items (High-Priority Exceptions)")
    high_pri_results = get_reconciliation_results(priority_filter="HIGH")
    if high_pri_results:
        summary_rows = []
        for r in high_pri_results[:8]:
            summary_rows.append({
                "Invoice ID": r.invoice_id,
                "Customer": r.customer_name,
                "Contract ID": r.contract_id or "MISSING",
                "Status": r.status.value,
                "Exposure ($)": f"${r.financial_exposure:,.2f}",
                "Confidence": f"{int(r.confidence_score * 100)}%",
                "Exception Reason": r.exception_reason,
                "Review State": r.review_status.value,
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
    else:
        st.success("No high-priority exceptions requiring attention!")


# ==============================================================================
# VIEW 2: RECONCILIATION RUNNER
# ==============================================================================
elif nav_choice == "⚡ Reconciliation Runner":
    st.title("⚡ Invoice Reconciliation Engine")
    st.markdown("Run deterministic multi-strategy matching and RAG clause retrieval across invoices.")

    invoices = get_all_invoices()
    contracts = get_all_contracts()

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        st.metric("Ingested Invoices", len(invoices))
    with col_meta2:
        st.metric("Ingested Contracts", len(contracts))
    with col_meta3:
        existing_res = get_reconciliation_results()
        st.metric("Reconciled Records", len(existing_res))

    st.markdown("---")
    st.subheader("Run Batch Reconciliation")
    st.write("Execute exact matching, tolerance calculations, fuzzy entity resolution, and RAG clause validation.")

    if st.button("🚀 Run Reconciliation on All Invoices", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        engine = ReconciliationEngine(contracts)
        results = []
        processed = []
        
        total = len(invoices)
        for i, inv in enumerate(invoices):
            status_text.text(f"Reconciling {inv.invoice_id} ({inv.customer_name})...")
            res = engine.reconcile_invoice(inv, existing_invoices=processed)
            results.append(res)
            processed.append(inv)
            progress_bar.progress((i + 1) / total)
            
        from app.database.db import save_reconciliation_results
        save_reconciliation_results(results)
        status_text.text("Batch reconciliation completed and persisted!")
        st.success(f"Successfully reconciled {len(results)} invoices!")
        st.rerun()

    st.markdown("---")
    st.subheader("Upload Custom Invoices (CSV / Excel)")
    uploaded_file = st.file_uploader("Upload CSV containing billing records", type=["csv"])
    if uploaded_file:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            st.write("Preview of uploaded file:", df_uploaded.head(3))
            if st.button("Ingest and Reconcile Uploaded File"):
                new_invoices = []
                for _, row in df_uploaded.iterrows():
                    new_invoices.append(RawInvoice(
                        invoice_id=str(row.get("invoice_id", "")),
                        contract_id=str(row.get("contract_id", "")) if pd.notna(row.get("contract_id")) else None,
                        customer_id=str(row.get("customer_id", "")) if pd.notna(row.get("customer_id")) else None,
                        customer_name=str(row.get("customer_name", "Unknown")),
                        invoice_date=str(row.get("invoice_date", "2025-01-01")),
                        billing_period=str(row.get("billing_period", "")) if pd.notna(row.get("billing_period")) else None,
                        currency=str(row.get("currency", "USD")),
                        quantity=int(row.get("quantity", 1)),
                        unit_price=float(row.get("unit_price", 0.0)),
                        discount=float(row.get("discount", 0.0)),
                        tax=float(row.get("tax", 0.0)),
                        total_amount=float(row.get("total_amount", 0.0)),
                        reference_number=str(row.get("reference_number", "")) if pd.notna(row.get("reference_number")) else None
                    ))
                save_invoices(new_invoices)
                engine = ReconciliationEngine(contracts)
                engine.reconcile_batch(new_invoices, persist_to_db=True)
                st.success(f"Uploaded and reconciled {len(new_invoices)} invoices!")
                st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {e}")


# ==============================================================================
# VIEW 3: EXCEPTION QUEUE
# ==============================================================================
elif nav_choice == "📋 Exception Queue":
    st.title("📋 Billing Exception Management Queue")
    st.markdown("Triaged financial discrepancies requiring Human-in-the-Loop review.")

    # Filter Controls
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        status_filter = st.selectbox("Filter Status", ["ALL", "UNMATCHED", "PROBABLE_MATCH", "DUPLICATE", "DATA_QUALITY_EXCEPTION", "MATCHED"])
    with f_col2:
        priority_filter = st.selectbox("Filter Priority", ["ALL", "HIGH", "MEDIUM", "LOW"])
    with f_col3:
        review_filter = st.selectbox("Filter Review State", ["ALL", "PENDING", "ACCEPT", "REJECT", "OVERRIDE"])

    results = get_reconciliation_results(
        status_filter=None if status_filter == "ALL" else status_filter,
        priority_filter=None if priority_filter == "ALL" else priority_filter,
        review_status_filter=None if review_filter == "ALL" else review_filter,
    )

    st.write(f"Displaying **{len(results)}** reconciliation records matching filter criteria:")

    if results:
        table_data = []
        for r in results:
            table_data.append({
                "Invoice ID": r.invoice_id,
                "Priority": r.priority.value,
                "Status": r.status.value,
                "Customer": r.customer_name,
                "Contract Ref": r.contract_id or "MISSING",
                "Expected ($)": f"${r.expected_amount:,.2f}",
                "Billed ($)": f"${r.actual_amount:,.2f}",
                "Variance ($)": f"${r.variance_amount:,.2f}",
                "Exposure ($)": f"${r.financial_exposure:,.2f}",
                "Confidence": f"{int(r.confidence_score * 100)}%",
                "Review Decision": r.review_status.value,
                "Reason": r.exception_reason,
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    else:
        st.info("No records match the current filter selection.")


# ==============================================================================
# VIEW 4: REVIEW & ROOT CAUSE ANALYSIS
# ==============================================================================
elif nav_choice == "🔍 Review & Root Cause":
    st.title("🔍 Discrepancy Root Cause Analysis & Human Review")
    st.markdown("Inspect deterministic math vs retrieved contractual clauses, and take authoritative review actions.")

    all_results = get_reconciliation_results()
    if not all_results:
        st.warning("No reconciliation records found. Please run reconciliation first.")
        st.stop()

    invoice_options = [f"{r.invoice_id} - {r.customer_name} ({r.status.value}, Priority: {r.priority.value})" for r in all_results]
    selected_option = st.selectbox("Select Invoice to Inspect:", invoice_options)
    selected_id = selected_option.split(" ")[0]

    record = get_reconciliation_result(selected_id)
    if not record:
        st.error("Record not found.")
        st.stop()

    # Status Banner
    st.markdown(f"""
    <div style="background-color: #1E293B; border-radius: 8px; padding: 12px 18px; margin-bottom: 16px; border-left: 5px solid {'#10B981' if record.status.value == 'MATCHED' else '#EF4444'};">
        <span style="font-size: 1.2rem; font-weight: 700; color: white;">Invoice: {record.invoice_id}</span> &nbsp;&nbsp;|&nbsp;&nbsp;
        <span>Customer: <b>{record.customer_name}</b></span> &nbsp;&nbsp;|&nbsp;&nbsp;
        <span>Status: <b style="color: {'#10B981' if record.status.value == 'MATCHED' else '#F87171'};">{record.status.value}</b></span> &nbsp;&nbsp;|&nbsp;&nbsp;
        <span>Priority: <b>{record.priority.value}</b></span> &nbsp;&nbsp;|&nbsp;&nbsp;
        <span>Current Decision: <b>{record.review_status.value}</b></span>
    </div>
    """, unsafe_allow_html=True)

    col_side_a, col_side_b = st.columns([1, 1])

    with col_side_a:
        st.subheader("1. Deterministic Financial Math")
        st.markdown(f"""
        - **Billed Amount:** `${record.actual_amount:,.2f}`
        - **Contract Expected:** `${record.expected_amount:,.2f}`
        - **Arithmetic Variance:** `${record.variance_amount:,.2f}` (`{record.variance_percent:.2f}%`)
        - **Allowable Tolerance:** `1.0%` or `$50.00`
        - **Within Tolerance:** `{'Yes' if record.is_within_tolerance else 'No'}`
        - **Total Financial Risk Exposure:** `${record.financial_exposure:,.2f}`
        """)

        st.markdown("#### Explainable Confidence Score")
        st.markdown(f"**Overall Score:** `{int(record.confidence_score * 100)}%`")
        for factor in record.confidence_breakdown.factors:
            st.markdown(f"- {factor}")

        st.markdown(f"**Methods Applied:** `{' + '.join(record.matching_methods_used)}`")

    with col_side_b:
        st.subheader("2. Contract Evidence & RAG Grounding")
        contract = get_contract(record.contract_id) if record.contract_id else None
        if contract:
            st.markdown(f"**Contract Reference:** `{contract.contract_id}`")
            st.markdown(f"**Term Period:** `{contract.effective_date}` to `{contract.expiry_date}`")
            st.markdown(f"**Contract Baseline Rate:** `${contract.unit_price:,.2f}` × `{contract.quantity}` units")
            st.markdown(f"**Discount Clause:** `{contract.discount_percent}%` ({contract.discount_notes})")
            st.markdown(f"**Special Stipulation:** {contract.special_conditions}")
        else:
            st.warning("No associated Master Services Agreement attached to this billing item.")

        if record.evidence_citations:
            st.markdown("**Retrieved Document Citations:**")
            for cite in record.evidence_citations:
                st.markdown(f"<span class='citation-tag'>{cite}</span>", unsafe_allow_html=True)

    # 5-Part AI Reasoning
    st.markdown("---")
    st.subheader("3. AI & RAG Root Cause Analysis")

    st.markdown(f"""
    <div class="analysis-box">
        <h4 style="color: #60A5FA; margin-bottom: 4px;">1. WHAT HAPPENED?</h4>
        <p>{record.what_happened}</p>
        
        <h4 style="color: #60A5FA; margin-bottom: 4px;">2. WHY DID IT HAPPEN?</h4>
        <p>{record.why_did_it_happen}</p>
        
        <h4 style="color: #60A5FA; margin-bottom: 4px;">3. WHAT DOES THE CONTRACT SAY?</h4>
        <p>{record.what_contract_says}</p>
        
        <h4 style="color: #60A5FA; margin-bottom: 4px;">4. WHAT SHOULD THE FINANCE REVIEWER DO?</h4>
        <p>{record.recommendation}</p>
    </div>
    """, unsafe_allow_html=True)

    # Human-in-the-Loop Review Action Form
    st.markdown("---")
    st.subheader("4. Human Reviewer Action (HITL)")
    st.write("The AI recommendation is advisory. Authoritative financial clearance requires human sign-off.")

    with st.form("human_review_form"):
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            decision = st.radio(
                "Review Decision",
                [ReviewDecision.ACCEPT.value, ReviewDecision.REJECT.value, ReviewDecision.OVERRIDE.value],
                index=0
            )
            reviewer_name = st.text_input("Reviewer Name / Title", value="Senior Finance Auditor")
            
        with r_col2:
            override_val = None
            if decision == ReviewDecision.OVERRIDE.value:
                override_val = st.number_input("Override Approved Amount ($)", value=float(record.expected_amount))
            reviewer_comment = st.text_area("Review Justification / Audit Comment", placeholder="Provide rationale for override or acceptance...")

        submit_review = st.form_submit_button("Submit Authoritative Review Decision", type="primary")
        if submit_review:
            if not reviewer_comment:
                st.error("Audit regulations require a mandatory comment for any exception clearance.")
            else:
                ok = update_review_decision(
                    invoice_id=record.invoice_id,
                    decision=ReviewDecision(decision),
                    reviewer_name=reviewer_name,
                    comment=reviewer_comment,
                    override_amount=override_val
                )
                if ok:
                    st.success(f"Decision '{decision}' successfully committed for {record.invoice_id} with immutable audit log!")
                    st.rerun()


# ==============================================================================
# VIEW 5: CONTRACT EXPLORER & RAG Q&A
# ==============================================================================
elif nav_choice == "📑 Contract Explorer (RAG)":
    st.title("📑 Contract Explorer & Grounded RAG Assistant")
    st.markdown("Explore executed Master Services Agreements and ask semantic questions strictly grounded in contract text.")

    contracts = get_all_contracts()
    if not contracts:
        st.warning("No contracts loaded.")
        st.stop()

    contract_map = {f"{c.contract_id} - {c.customer_name}": c for c in contracts}
    selected_contract_label = st.selectbox("Select Customer Contract:", list(contract_map.keys()))
    selected_contract = contract_map[selected_contract_label]

    # Display Contract Overview
    c_info1, c_info2, c_info3, c_info4 = st.columns(4)
    with c_info1:
        st.metric("Base Unit Price", f"{selected_contract.currency} {selected_contract.unit_price:,.2f}")
    with c_info2:
        st.metric("Contracted Capacity", f"{selected_contract.quantity} units")
    with c_info3:
        st.metric("Discount Concession", f"{selected_contract.discount_percent}%")
    with c_info4:
        st.metric("Term Expiry", selected_contract.expiry_date)

    st.markdown(f"""
    - **Contract ID:** `{selected_contract.contract_id}` &nbsp;|&nbsp; **Customer ID:** `{selected_contract.customer_id}`
    - **Product/Service:** {selected_contract.product_service}
    - **Billing Cadence:** {selected_contract.billing_frequency} &nbsp;|&nbsp; **Payment Terms:** {selected_contract.payment_terms}
    - **Permissible Tolerance:** {selected_contract.tolerance_percent}% or {selected_contract.currency} {selected_contract.tolerance_absolute:,.2f}
    - **Special Conditions:** {selected_contract.special_conditions}
    - **Source PDF File:** `{selected_contract.file_path}`
    """)

    st.markdown("---")
    st.subheader("💬 Ask Contract (Semantic RAG Assistant)")
    st.write("Ask natural-language questions about terms, penalties, discounts, and SLA conditions.")

    # Preset Question Quick-Buttons
    q_col1, q_col2, q_col3 = st.columns(3)
    user_q = ""
    with q_col1:
        if st.button("What is the contracted monthly billing rate?"):
            user_q = "What is the contracted monthly billing rate?"
    with q_col2:
        if st.button("What discount terms and concessions apply?"):
            user_q = "What discount terms and concessions apply?"
    with q_col3:
        if st.button("When does this agreement terminate?"):
            user_q = "When does this agreement terminate?"

    custom_q = st.text_input("Or enter your question:", value=user_q, placeholder="e.g., What are the acceptable variance tolerances?")
    if custom_q:
        rag = get_rag_chain()
        with st.spinner("Retrieving grounded contract clauses..."):
            ans_data = rag.ask_contract(custom_q, contract_id=selected_contract.contract_id)
            
            st.markdown("### Grounded Answer:")
            st.markdown(f"> {ans_data['answer']}")
            
            if ans_data['evidence_citations']:
                st.markdown("**Evidence Citations:**")
                for cite in ans_data['evidence_citations']:
                    st.markdown(f"- `{cite}`")

    # Show related invoices for this contract
    st.markdown("---")
    st.subheader(f"Invoices Billed Against {selected_contract.contract_id}")
    all_invoices = get_all_invoices()
    contract_invoices = [inv for inv in all_invoices if inv.contract_id == selected_contract.contract_id]
    if contract_invoices:
        df_inv = pd.DataFrame([inv.model_dump() for inv in contract_invoices])
        st.dataframe(df_inv[["invoice_id", "invoice_date", "billing_period", "quantity", "unit_price", "discount", "total_amount", "reference_number"]], use_container_width=True)
    else:
        st.info("No invoices currently linked to this contract.")


# ==============================================================================
# VIEW 6: AUDIT TRAIL & GOVERNANCE
# ==============================================================================
elif nav_choice == "📜 Audit Trail & Governance":
    st.title("📜 Compliance Audit Trail")
    st.markdown("Immutable record of all automated reconciliations, reviewer decisions, overrides, and timestamps.")

    logs = get_audit_logs(limit=200)
    if logs:
        log_records = []
        for l in logs:
            log_records.append({
                "Timestamp (UTC)": l.timestamp,
                "Invoice ID": l.invoice_id,
                "Contract ID": l.contract_id or "-",
                "Actor": l.actor,
                "Action": l.action_type,
                "Prior Status": l.previous_status or "-",
                "New Status": l.new_status or "-",
                "Details": l.details,
                "Evidence Citation": l.evidence_citation or "-",
            })
        df_logs = pd.DataFrame(log_records)
        
        # Download CSV button
        csv_data = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Audit Trail to CSV",
            data=csv_data,
            file_name=f"compliance_audit_trail_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
        
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("No audit logs recorded yet.")


# ==============================================================================
# VIEW 7: ARCHITECTURE & INTERVIEW GUIDE
# ==============================================================================
elif nav_choice == "ℹ️ Architecture & Interview Guide":
    st.title("ℹ️ Architecture & Interview Presentation Guide")
    st.markdown("Key talking points, responsibilities breakdown, and architecture explanation for interview panels.")

    st.markdown("""
    ### 🎯 The Core Architectural Principle
    > *"Never let an LLM do basic math that Python can calculate deterministically. Use the LLM for what it is exceptional at: interpreting complex natural language contract clauses, synthesizing root causes, and generating grounded explanations."*

    ---

    ### 🧩 Responsibility Matrix (What does each component do?)

    | Layer | Technology | Responsibilities | Why This Choice? |
    | :--- | :--- | :--- | :--- |
    | **Deterministic Python** | Python 3.12, Pandas | Currency normalization, exact key matching, arithmetic variance math ($ & %), tolerance thresholds, date window validation, duplicate checks. | Zero hallucination risk, exact auditability, sub-millisecond execution. |
    | **Fuzzy Matching** | RapidFuzz | Customer name variations (e.g. Inc vs Incorporated), service token sorting, alias resolution. | Bridges messy real-world invoice naming to official legal contract parties. |
    | **Document Ingestion** | PyMuPDF (fitz) | Extracts page numbers, clause categories, and paragraphs from executed PDF contracts. | Preserves document geometry and exact page citations for legal defensibility. |
    | **Vector Database & RAG** | ChromaDB (MiniLM-L6-v2) | Embedded semantic search over contract clauses and corporate billing policies. | Grounded retrieval: finds specific discount rules, tiered overage policies, and SLA terms. |
    | **AI Reasoning & Explanation** | LangChain / LLM | Formulates 5-part root cause analysis: What Happened, Why It Happened, What Contract Says, Citations, Recommended Action. | Transforms dry numbers into actionable, plain-English finance executive narratives. |
    | **Explainable Confidence** | Multi-Factor Formula | Weighted score: ID (30%) + Amount (35%) + Date (15%) + Name (10%) + Evidence (10%). | Not a black-box LLM number. Explainable to regulators and audit committees. |
    | **Human-in-the-Loop (HITL)** | SQLite, Streamlit | Authoritative clearance: Accept, Reject, Override. Immutable audit trail logging. | System never silently clears material money without authorized finance sign-off. |

    ---

    ### 🔄 End-to-End Dataflow Diagram

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
    """)
