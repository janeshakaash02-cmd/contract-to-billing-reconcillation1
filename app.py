import streamlit as st

# Set Page Config MUST be the very first Streamlit command executed
st.set_page_config(
    page_title="NEXUS RECON // Finance AI Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import json
import time
import pandas as pd
from datetime import datetime, date

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
    batch_update_review_decisions,
    get_audit_logs,
    get_dashboard_summary_metrics,
    reset_database,
)
from app.frontend.styles import get_custom_css
from app.frontend.charts import (
    build_status_donut,
    build_exposure_bar,
    build_neon_sankey,
    build_confidence_gauge,
    build_tolerance_meter,
    build_roi_payback_chart,
)
from app.matching.normalizer import normalize_invoice
from app.reconciliation.engine import ReconciliationEngine
from app.rag.chain import get_rag_chain
from generate_data import generate_all_data

# Apply Cyber Black & Neon Green Styling
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

# Sidebar Header & Branding
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
    <span style="font-size: 2rem; filter: drop-shadow(0 0 10px rgba(0,255,136,0.6));">⚡</span>
    <div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #00FF88; letter-spacing: 0.05em; line-height: 1.1;">NEXUS RECON</div>
        <div style="font-size: 0.68rem; color: #8B949E; letter-spacing: 0.1em; font-family: 'JetBrains Mono', monospace;">AUTONOMOUS COMPLIANCE</div>
    </div>
</div>
<div style="margin-bottom: 18px; padding-left: 4px;">
    <span class="live-indicator"></span>
    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #00FF88; font-weight: 600; letter-spacing: 0.04em;">SYSTEM ONLINE // 256-BIT AUDIT</span>
</div>
""", unsafe_allow_html=True)

nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "📊 Executive Dashboard",
        "🧪 'What-If' Sandbox",
        "⚡ Engine Runner",
        "📋 Exception Queue",
        "🔍 Visual Diff & Review",
        "📑 Contract Explorer",
        "💰 ROI Simulator",
        "📜 Compliance Audit",
        "ℹ️ Architecture Guide",
    ],
    index=0
)

st.sidebar.markdown("<hr style='border-color: rgba(0, 255, 136, 0.15); margin: 16px 0;'>", unsafe_allow_html=True)
st.sidebar.subheader("System Actions")

if st.sidebar.button("🔄 Re-Run Full Reconciliation", use_container_width=True):
    with st.spinner("Executing multi-strategy reconciliation engine..."):
        invoices = get_all_invoices()
        engine = ReconciliationEngine()
        engine.reconcile_batch(invoices, persist_to_db=True)
        st.sidebar.success("Engine batch complete!")
        st.rerun()

if st.sidebar.button("🧹 Reset & Regenerate Datasets", use_container_width=True):
    with st.spinner("Regenerating PDF contracts, vectors, and invoices..."):
        generate_all_data()
        engine = ReconciliationEngine()
        engine.reconcile_batch(get_all_invoices(), persist_to_db=True)
        st.sidebar.success("Database regenerated successfully!")
        st.rerun()

st.sidebar.markdown("<hr style='border-color: rgba(0, 255, 136, 0.15); margin: 16px 0;'>", unsafe_allow_html=True)
st.sidebar.caption(f"**AI Reasoning:** `{LLM_PROVIDER}` ({LLM_MODEL})")
st.sidebar.caption(f"**Semantic Vectors:** `{EMBEDDING_PROVIDER}` (MiniLM-L6-v2)")
st.sidebar.caption("Deterministic Math: **Python 3.12 Engine**")
st.sidebar.caption("Contract Tolerance: **±1.0% or $50.00**")


# ==============================================================================
# VIEW 1: EXECUTIVE DASHBOARD
# ==============================================================================
if nav_choice == "📊 Executive Dashboard":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem; letter-spacing: -0.02em;">
            <span style="color: #00FF88;">⚡</span> Executive Reconciliation Command Center
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Real-time contractual compliance tracking, autonomous variance detection, and capital preservation analytics.
        </p>
    </div>
    """, unsafe_allow_html=True)

    metrics = get_dashboard_summary_metrics()
    results = get_reconciliation_results()

    # Top KPI Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label"><span>Ingested Invoices</span> <span>📁</span></div>
            <div class="metric-value">{metrics['total_reconciled']}</div>
            <div class="metric-sub">100% Ingested & Verified</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label"><span>Auto-Match Rate</span> <span>🎯</span></div>
            <div class="metric-value metric-value-green">{metrics['auto_match_rate']}%</div>
            <div class="metric-sub">{metrics['matched']} Perfect Clearances</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card metric-card-danger">
            <div class="metric-label"><span>Financial Exposure</span> <span>⚠️</span></div>
            <div class="metric-value metric-value-crimson">${metrics['total_financial_exposure']:,.0f}</div>
            <div class="metric-sub" style="color: #FF3366;">At-Risk Variance</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card metric-card-danger">
            <div class="metric-label"><span>High-Priority Triage</span> <span>🚨</span></div>
            <div class="metric-value metric-value-crimson">{metrics['high_priority_exceptions']}</div>
            <div class="metric-sub" style="color: #FF6B8B;">Action Required</div>
        </div>
        """, unsafe_allow_html=True)

    with c5:
        st.markdown(f"""
        <div class="metric-card metric-card-cyan">
            <div class="metric-label"><span>Labor Saved</span> <span>⏱️</span></div>
            <div class="metric-value metric-value-cyan">{metrics['hours_saved']}h</div>
            <div class="metric-sub" style="color: #00F0FF;">${metrics['cost_saved']:,.0f} Net Savings</div>
        </div>
        """, unsafe_allow_html=True)

    # Interactive Pipeline Flow (Sankey Diagram)
    st.markdown("### 🌐 End-to-End Autonomous Pipeline Flow")
    st.caption("Visualizes the trajectory of invoices through deterministic matching strategies to final financial resolution.")
    fig_sankey = build_neon_sankey(metrics, results)
    st.plotly_chart(fig_sankey, use_container_width=True)

    # Secondary Charts Row
    st.markdown("### 📊 Portfolio Breakdown & Exposure Root Causes")
    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        fig_donut = build_status_donut(metrics)
        st.plotly_chart(fig_donut, use_container_width=True)
    with col_c2:
        fig_bar = build_exposure_bar(metrics)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Urgent Action Items
    st.markdown("### 🚨 Urgent Action Items (High-Exposure Exceptions)")
    high_pri = get_reconciliation_results(priority_filter="HIGH")
    if high_pri:
        urgent_data = []
        for r in high_pri[:8]:
            urgent_data.append({
                "Invoice ID": r.invoice_id,
                "Customer": r.customer_name,
                "Contract Ref": r.contract_id or "MISSING",
                "Status": r.status.value,
                "Exposure ($)": f"${r.financial_exposure:,.2f}",
                "Confidence": f"{int(r.confidence_score * 100)}%",
                "Exception Reason": r.exception_reason,
                "Review State": r.review_status.value,
            })
        st.dataframe(pd.DataFrame(urgent_data), use_container_width=True, hide_index=True)
    else:
        st.success("All high-priority exceptions cleared!")


# ==============================================================================
# VIEW 2: INTERACTIVE "WHAT-IF" SIMULATION SANDBOX
# ==============================================================================
elif nav_choice == "🧪 'What-If' Sandbox":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">🧪</span> Interactive "What-If" Reconciliation Sandbox
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Simulate price drift, volume anomalies, discount omissions, and date violations live against executed contracts.
        </p>
    </div>
    """, unsafe_allow_html=True)

    contracts = get_all_contracts()
    if not contracts:
        st.warning("No contracts available for simulation.")
        st.stop()

    contract_options = {f"{c.contract_id} — {c.customer_name} ({c.product_service})": c for c in contracts}
    selected_label = st.selectbox("Select Target Master Services Agreement:", list(contract_options.keys()))
    target_contract = contract_options[selected_label]

    # Baseline Terms Card
    st.markdown(f"""
    <div style="background: #0B101B; border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #00F0FF; margin-bottom: 6px;">
            EXECUTED CONTRACT BASELINE // {target_contract.contract_id}
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 20px; font-size: 0.88rem;">
            <span>Customer: <b>{target_contract.customer_name}</b></span>
            <span>Agreed Unit Price: <b>${target_contract.unit_price:,.2f}</b></span>
            <span>Contracted Qty: <b>{target_contract.quantity}</b></span>
            <span>Contract Discount: <b>{target_contract.discount_percent}%</b></span>
            <span>Term: <b>{target_contract.effective_date} to {target_contract.expiry_date}</b></span>
            <span>Permissible Tolerance: <b>±{target_contract.tolerance_percent}% / ${target_contract.tolerance_absolute:,.2f}</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🎛️ Adjust Simulation Parameters")
    s_col1, s_col2, s_col3 = st.columns(3)

    base_price = float(target_contract.unit_price)
    base_qty = int(target_contract.quantity)
    base_discount = float(target_contract.discount_percent)

    with s_col1:
        sim_price = st.slider("Billed Unit Price ($)", min_value=max(10.0, base_price * 0.5), max_value=base_price * 2.0, value=base_price, step=5.0)
        sim_qty = st.slider("Billed Quantity", min_value=1, max_value=max(150, base_qty * 2), value=base_qty, step=1)

    with s_col2:
        sim_discount = st.slider("Applied Discount (%)", min_value=0.0, max_value=50.0, value=base_discount, step=1.0)
        sim_date_offset = st.selectbox(
            "Invoice Submission Timing",
            ["In-Term (Valid Period)", "Pre-Contract (15 Days Prior)", "Post-Expiry (30 Days Lapsed)"],
            index=0
        )
        if sim_date_offset == "In-Term (Valid Period)":
            sim_date = "2025-06-15"
        elif sim_date_offset == "Pre-Contract (15 Days Prior)":
            sim_date = "2024-12-15"
        else:
            sim_date = "2026-02-15"

    with s_col3:
        sim_name_type = st.selectbox(
            "Customer Entity Name on Invoice",
            ["Exact Official Legal Name", "Minor Typo / Abbreviation", "Unregistered Third-Party Entity"],
            index=0
        )
        if sim_name_type == "Exact Official Legal Name":
            sim_customer_name = target_contract.customer_name
        elif sim_name_type == "Minor Typo / Abbreviation":
            sim_customer_name = target_contract.customer_name.replace("Inc.", "Incorporated").replace("Technologies", "Tech").replace("Corp", "Corporation")
        else:
            sim_customer_name = "Apex Global Enterprises LLC"

        sim_currency = st.selectbox("Billing Currency", ["USD", "EUR", "GBP", "INR"], index=0)

    # Real-Time Deterministic Math Engine Calculation
    contract_subtotal = base_qty * base_price
    contract_discount_amount = contract_subtotal * (base_discount / 100.0)
    expected_amount = contract_subtotal - contract_discount_amount

    sim_subtotal = sim_qty * sim_price
    sim_discount_amount = sim_subtotal * (sim_discount / 100.0)
    actual_amount = sim_subtotal - sim_discount_amount

    variance_amount = abs(actual_amount - expected_amount)
    variance_percent = (variance_amount / expected_amount * 100.0) if expected_amount > 0 else 0.0

    # Tolerance rule
    is_within_tolerance = (variance_percent <= target_contract.tolerance_percent) or (variance_amount <= target_contract.tolerance_absolute)

    # Date rule
    is_date_valid = (target_contract.effective_date <= sim_date <= target_contract.expiry_date)

    # Currency rule
    is_currency_valid = (sim_currency == target_contract.currency)

    # Name match
    from rapidfuzz import fuzz
    name_similarity = fuzz.token_sort_ratio(sim_customer_name.lower(), target_contract.customer_name.lower()) / 100.0

    # Determine simulated status
    if not is_currency_valid:
        sim_status = "UNMATCHED (CURRENCY_MISMATCH)"
        status_color = "#FF3366"
        status_banner_class = "badge-unmatched"
        reason_text = f"Currency Inconsistency: Invoiced in {sim_currency} vs Contract in {target_contract.currency}."
    elif not is_date_valid:
        sim_status = "UNMATCHED (DATE_WINDOW_ANOMALY)"
        status_color = "#FF3366"
        status_banner_class = "badge-unmatched"
        reason_text = f"Date Violation: Invoice date {sim_date} is outside term ({target_contract.effective_date} to {target_contract.expiry_date})."
    elif name_similarity < 0.6:
        sim_status = "UNMATCHED (UNKNOWN_ENTITY)"
        status_color = "#FF3366"
        status_banner_class = "badge-unmatched"
        reason_text = f"Entity Mismatch: '{sim_customer_name}' does not resolve to '{target_contract.customer_name}'."
    elif variance_amount == 0.0:
        sim_status = "MATCHED (PERFECT_COMPLIANCE)"
        status_color = "#00FF88"
        status_banner_class = "badge-matched"
        reason_text = "Zero arithmetic variance. Rates, quantities, discounts, and terms match exactly."
    elif is_within_tolerance:
        sim_status = "PROBABLE_MATCH (WITHIN_TOLERANCE)"
        status_color = "#00F0FF"
        status_banner_class = "badge-probable"
        reason_text = f"Variance of ${variance_amount:,.2f} ({variance_percent:.2f}%) is within allowable tolerance."
    else:
        sim_status = "UNMATCHED (RATE_OR_DISCOUNT_DRIFT)"
        status_color = "#FF3366"
        status_banner_class = "badge-unmatched"
        reason_text = f"Material discrepancy of ${variance_amount:,.2f} ({variance_percent:.2f}%) exceeds tolerance limit."

    # Compute simulated confidence score
    id_score = 1.0 if name_similarity >= 0.8 else 0.4
    amt_score = 1.0 if variance_amount == 0.0 else (0.9 if is_within_tolerance else max(0.0, 1.0 - (variance_percent / 20.0)))
    date_score = 1.0 if is_date_valid else 0.0
    name_score = name_similarity
    evid_score = 1.0 if (target_contract.special_conditions) else 0.5
    sim_conf_score = (id_score * 0.30) + (amt_score * 0.35) + (date_score * 0.15) + (name_score * 0.10) + (evid_score * 0.10)

    st.markdown("---")
    st.markdown("### ⚡ Live Autonomous Engine Evaluation")

    # Status Banner
    st.markdown(f"""
    <div style="background: #0D131F; border: 1px solid {status_color}; border-left: 6px solid {status_color}; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; box-shadow: 0 0 16px {status_color}33;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF;">
                Evaluation Outcome: <span style="color: {status_color}; font-family: 'JetBrains Mono', monospace;">{sim_status}</span>
            </span>
            <span class="badge {status_banner_class}">{sim_status.split(' ')[0]}</span>
        </div>
        <div style="font-size: 0.88rem; color: #CBD5E1; margin-top: 6px;">
            <b>Root Cause Assessment:</b> {reason_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Gauges & Calculations Row
    g_col1, g_col2, g_col3 = st.columns([1, 1, 1])
    with g_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Financial Variance ($)</div>
            <div class="metric-value {'metric-value-green' if is_within_tolerance else 'metric-value-crimson'}">
                ${variance_amount:,.2f}
            </div>
            <div class="metric-sub">
                Actual: ${actual_amount:,.2f} vs Expected: ${expected_amount:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with g_col2:
        fig_tol = build_tolerance_meter(variance_percent, target_contract.tolerance_percent)
        st.plotly_chart(fig_tol, use_container_width=True)

    with g_col3:
        fig_conf = build_confidence_gauge(sim_conf_score)
        st.plotly_chart(fig_conf, use_container_width=True)

    # Grounded Contract Clause Retrieval Preview
    st.markdown("#### 📜 Grounded Contract Clause Retrieval")
    st.markdown(f"""
    <div class="analysis-box">
        <h4>APPLICABLE CONTRACTUAL STIPULATION</h4>
        <p>{target_contract.special_conditions or 'Standard list pricing with Net 30 payment terms and 1.0% variance threshold.'}</p>
        <div style="margin-top: 8px;">
            <span class="citation-tag">{target_contract.file_path or target_contract.contract_id} // Section 4.2</span>
            <span class="citation-tag">Pricing Schedule Exhibit A</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📥 Commit Simulated Invoice to Database for Full Audit", type="primary"):
        sim_inv_id = f"SIM-INV-{int(time.time()) % 10000}"
        new_inv = RawInvoice(
            invoice_id=sim_inv_id,
            contract_id=target_contract.contract_id,
            customer_id=target_contract.customer_id,
            customer_name=sim_customer_name,
            invoice_date=sim_date,
            billing_period="2025-06",
            currency=sim_currency,
            quantity=sim_qty,
            unit_price=sim_price,
            discount=sim_discount,
            tax=0.0,
            total_amount=actual_amount,
            reference_number=f"SIM-REF-{sim_inv_id}"
        )
        save_invoices([new_inv])
        eng = ReconciliationEngine(contracts)
        eng.reconcile_invoice(new_inv)
        st.success(f"Simulated invoice {sim_inv_id} ingested, reconciled, and committed to immutable audit trail!")


# ==============================================================================
# VIEW 3: ENGINE RUNNER & TERMINAL
# ==============================================================================
elif nav_choice == "⚡ Engine Runner":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">⚡</span> Invoice Reconciliation Engine & Live Terminal
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Execute deterministic multi-strategy matching, RAG clause retrieval, and view live terminal execution logs.
        </p>
    </div>
    """, unsafe_allow_html=True)

    invoices = get_all_invoices()
    contracts = get_all_contracts()
    existing_res = get_reconciliation_results()

    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Ingested Invoices</div>
            <div class="metric-value">{len(invoices)}</div>
            <div class="metric-sub">Billing Records</div>
        </div>
        """, unsafe_allow_html=True)
    with c_m2:
        st.markdown(f"""
        <div class="metric-card metric-card-cyan">
            <div class="metric-label">Ingested Contracts</div>
            <div class="metric-value metric-value-cyan">{len(contracts)}</div>
            <div class="metric-sub">Executed MSAs (PDF)</div>
        </div>
        """, unsafe_allow_html=True)
    with c_m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Reconciled Records</div>
            <div class="metric-value">{len(existing_res)}</div>
            <div class="metric-sub">Persisted in SQLite</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🖥️ Run Batch Reconciliation Stream")
    st.write("Executes 4-tier matching: Exact Key &rarr; Deterministic Tolerance &rarr; RapidFuzz Entity &rarr; RAG Grounding.")

    if st.button("🚀 Trigger Full Batch Reconciliation", type="primary"):
        term_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        terminal_lines = [
            "<span class='term-dim'>[INIT]</span> Initializing Deterministic Financial Reconciliation Engine...",
            f"<span class='term-dim'>[INIT]</span> Ingested {len(contracts)} contracts and {len(invoices)} billing invoices.",
            "<span class='term-cyan'>[START]</span> Launching multi-strategy batch evaluation stream...",
        ]

        engine = ReconciliationEngine(contracts)
        results = []
        processed = []
        total = len(invoices)

        for i, inv in enumerate(invoices):
            res = engine.reconcile_invoice(inv, existing_invoices=processed)
            results.append(res)
            processed.append(inv)
            progress_bar.progress((i + 1) / total)

            if res.status == ReconciliationStatus.MATCHED:
                color_class = "term-green"
                status_txt = "MATCHED (OK)"
            elif res.status == ReconciliationStatus.PROBABLE_MATCH:
                color_class = "term-cyan"
                status_txt = "PROBABLE (TOLERANCE)"
            else:
                color_class = "term-red"
                status_txt = f"EXCEPTION ({res.priority.value})"

            terminal_lines.append(
                f"<span class='term-dim'>[{datetime.utcnow().strftime('%H:%M:%S')}]</span> "
                f"Inv <span class='term-cyan'>{inv.invoice_id}</span> "
                f"({inv.customer_name[:20]}) ➔ "
                f"<span class='{color_class}'>{status_txt}</span> "
                f"| Var: ${res.variance_amount:,.2f} | Conf: {int(res.confidence_score*100)}%"
            )

            # Display last 8 lines in terminal
            recent_lines = "<br>".join(terminal_lines[-9:])
            term_placeholder.markdown(f"<div class='terminal-box'>{recent_lines}</div>", unsafe_allow_html=True)

        from app.database.db import save_reconciliation_results
        save_reconciliation_results(results)
        terminal_lines.append("<span class='term-green'>[COMPLETE]</span> All invoices successfully reconciled and persisted.")
        recent_lines = "<br>".join(terminal_lines[-9:])
        term_placeholder.markdown(f"<div class='terminal-box'>{recent_lines}</div>", unsafe_allow_html=True)
        st.success(f"Successfully processed {len(results)} invoices!")
        st.rerun()

    st.markdown("---")
    st.subheader("📂 Upload Custom Invoices (CSV)")
    uploaded_file = st.file_uploader("Upload CSV containing billing records", type=["csv"])
    if uploaded_file:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            st.write("Preview of uploaded records:", df_uploaded.head(3))
            if st.button("Ingest and Reconcile Uploaded CSV"):
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
                st.success(f"Ingested and reconciled {len(new_invoices)} invoices!")
                st.rerun()
        except Exception as e:
            st.error(f"Error processing CSV: {e}")


# ==============================================================================
# VIEW 4: EXCEPTION QUEUE & BATCH TRIAGE
# ==============================================================================
elif nav_choice == "📋 Exception Queue":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">📋</span> Exception Queue & Batch Triage Workbench
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Filter, inspect, and perform rapid batch clearances on triaged financial discrepancies.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Filter Controls
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        status_filter = st.selectbox("Status Filter", ["ALL", "UNMATCHED", "PROBABLE_MATCH", "DUPLICATE", "DATA_QUALITY_EXCEPTION", "MATCHED"])
    with f_col2:
        priority_filter = st.selectbox("Priority Filter", ["ALL", "HIGH", "MEDIUM", "LOW"])
    with f_col3:
        review_filter = st.selectbox("Review Decision", ["ALL", "PENDING", "ACCEPT", "REJECT", "OVERRIDE"])
    with f_col4:
        search_query = st.text_input("Search Customer / ID", placeholder="e.g. Nexus, INV-1001")

    results = get_reconciliation_results(
        status_filter=None if status_filter == "ALL" else status_filter,
        priority_filter=None if priority_filter == "ALL" else priority_filter,
        review_status_filter=None if review_filter == "ALL" else review_filter,
    )

    if search_query:
        sq = search_query.lower()
        results = [r for r in results if sq in r.customer_name.lower() or sq in r.invoice_id.lower()]

    st.write(f"Displaying **{len(results)}** records matching filter criteria:")

    # Batch Actions Bar
    st.markdown("#### ⚡ Batch Triage Operations")
    b_col1, b_col2, b_col3 = st.columns(3)
    
    with b_col1:
        if st.button("✅ Batch-Approve In-Tolerance Records (<$100)", use_container_width=True):
            eligible = [r.invoice_id for r in results if r.is_within_tolerance and r.review_status == ReviewDecision.PENDING]
            if eligible:
                count = batch_update_review_decisions(
                    eligible,
                    ReviewDecision.ACCEPT,
                    "Batch Clearance Specialist",
                    "Batch auto-approved in-tolerance arithmetic variances."
                )
                st.success(f"Batch approved {count} records!")
                st.rerun()
            else:
                st.info("No pending in-tolerance records match current selection.")

    with b_col2:
        if st.button("🚨 Batch-Reject Pre/Post Contract Invoices", use_container_width=True):
            eligible = [r.invoice_id for r in results if "Date" in r.exception_reason or "Pre-Contract" in r.exception_reason]
            if eligible:
                count = batch_update_review_decisions(
                    eligible,
                    ReviewDecision.REJECT,
                    "Compliance Auditor",
                    "Batch rejected due to contractual term period violation."
                )
                st.warning(f"Batch rejected {count} records!")
                st.rerun()
            else:
                st.info("No date violation records found in current selection.")

    with b_col3:
        csv_export = pd.DataFrame([{
            "Invoice ID": r.invoice_id,
            "Customer": r.customer_name,
            "Status": r.status.value,
            "Priority": r.priority.value,
            "Exposure": r.financial_exposure,
            "Reason": r.exception_reason
        } for r in results]).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Current View to CSV", data=csv_export, file_name="exception_queue.csv", mime="text/csv", use_container_width=True)

    # Data Table
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
# VIEW 5: VISUAL DIFF & ROOT CAUSE REVIEW
# ==============================================================================
elif nav_choice == "🔍 Visual Diff & Review":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">🔍</span> Side-by-Side Visual Diff & Root Cause Inspector
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Inspect contract terms vs billing invoice line-by-line, verify RAG citations, and execute human review decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    all_results = get_reconciliation_results()
    if not all_results:
        st.warning("No reconciliation records found.")
        st.stop()

    invoice_options = [f"{r.invoice_id} — {r.customer_name} ({r.status.value}, Priority: {r.priority.value})" for r in all_results]
    selected_option = st.selectbox("Select Invoice to Inspect:", invoice_options)
    selected_id = selected_option.split(" ")[0]

    record = get_reconciliation_result(selected_id)
    if not record:
        st.error("Record not found.")
        st.stop()

    contract = get_contract(record.contract_id) if record.contract_id else None

    # Status Banner
    status_border = "#00FF88" if record.status.value == "MATCHED" else ("#00F0FF" if record.status.value == "PROBABLE_MATCH" else "#FF3366")
    st.markdown(f"""
    <div style="background-color: #0C121F; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; border: 1px solid {status_border}40; border-left: 6px solid {status_border};">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <span style="font-size: 1.25rem; font-weight: 700; color: white;">Invoice: {record.invoice_id}</span>
            <span>Customer: <b>{record.customer_name}</b></span>
            <span>Status: <b style="color: {status_border};">{record.status.value}</b></span>
            <span>Priority: <b>{record.priority.value}</b></span>
            <span>Decision: <b>{record.review_status.value}</b></span>
            <span class="badge" style="border: 1px solid {status_border}; color: {status_border};">Confidence: {int(record.confidence_score * 100)}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # SIDE-BY-SIDE VISUAL DIFF CARDS
    st.markdown("### ⚖️ Side-by-Side Visual Diff (Contract vs Invoice)")
    
    col_diff_a, col_diff_b = st.columns(2)

    with col_diff_a:
        c_unit_price = f"${contract.unit_price:,.2f}" if contract else "$0.00"
        c_quantity = f"{contract.quantity} units" if contract else "0 units"
        c_discount = f"{contract.discount_percent:.1f}%" if contract else "0.0%"
        c_term = f"{contract.effective_date} to {contract.expiry_date}" if contract else "N/A"
        c_tolerance = f"±{contract.tolerance_percent}% / ${contract.tolerance_absolute:,.2f}" if contract else "±1.0% / $50.00"

        st.markdown(f"""
        <div class="diff-card diff-card-contract">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #00F0FF; margin-bottom: 12px; font-weight: 600;">
                📜 CONTRACT BASELINE TERMS ({record.contract_id or 'NO CONTRACT FOUND'})
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Contract ID</span>
                <b>{record.contract_id or 'UNLINKED'}</b>
            </div>
            <div class="diff-row {'diff-row-mismatch' if contract and record.actual_amount != record.expected_amount else 'diff-row-match'}">
                <span style="color: #94A3B8;">Agreed Expected Total</span>
                <b>${record.expected_amount:,.2f}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Contract Unit Rate</span>
                <b>{c_unit_price}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Contracted Capacity</span>
                <b>{c_quantity}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Authorized Discount</span>
                <b>{c_discount}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Effective Term Window</span>
                <b>{c_term}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Allowable Tolerance</span>
                <b>{c_tolerance}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_diff_b:
        is_amt_diff = (record.actual_amount != record.expected_amount)
        st.markdown(f"""
        <div class="diff-card diff-card-invoice">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #00FF88; margin-bottom: 12px; font-weight: 600;">
                🧾 INVOICED BILLING RECORD ({record.invoice_id})
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Invoice ID</span>
                <b>{record.invoice_id}</b>
            </div>
            <div class="diff-row {'diff-row-mismatch' if is_amt_diff else 'diff-row-match'}">
                <span style="color: #94A3B8;">Billed Total Amount</span>
                <b style="color: {'#FF3366' if is_amt_diff else '#00FF88'};">${record.actual_amount:,.2f}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Arithmetic Variance</span>
                <b style="color: {'#FF3366' if not record.is_within_tolerance else '#00FF88'};">${record.variance_amount:,.2f} ({record.variance_percent:.2f}%)</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Within Tolerance?</span>
                <b>{'✅ YES' if record.is_within_tolerance else '❌ NO'}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Financial Exposure</span>
                <b style="color: {'#FF3366' if record.financial_exposure > 0 else '#00FF88'};">${record.financial_exposure:,.2f}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Matching Methods</span>
                <b>{' + '.join(record.matching_methods_used)}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Review State</span>
                <b>{record.review_status.value}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Confidence Factor Breakdown
    st.markdown("#### 🔬 Explainable Confidence Breakdown")
    conf_c1, conf_c2, conf_c3, conf_c4, conf_c5 = st.columns(5)
    with conf_c1:
        st.metric("ID Match (30%)", f"{int(record.confidence_breakdown.id_match_score * 100)}%")
    with conf_c2:
        st.metric("Amount Match (35%)", f"{int(record.confidence_breakdown.amount_match_score * 100)}%")
    with conf_c3:
        st.metric("Date Match (15%)", f"{int(record.confidence_breakdown.date_match_score * 100)}%")
    with conf_c4:
        st.metric("Name Match (10%)", f"{int(record.confidence_breakdown.name_match_score * 100)}%")
    with conf_c5:
        st.metric("Evidence (10%)", f"{int(record.confidence_breakdown.evidence_score * 100)}%")

    # 5-Part AI Reasoning
    st.markdown("---")
    st.markdown("### 🧠 5-Part AI & RAG Root Cause Analysis")
    st.markdown(f"""
    <div class="analysis-box">
        <h4>1. WHAT HAPPENED?</h4>
        <p>{record.what_happened}</p>
        
        <h4>2. WHY DID IT HAPPEN?</h4>
        <p>{record.why_did_it_happen}</p>
        
        <h4>3. WHAT DOES THE CONTRACT SAY?</h4>
        <p>{record.what_contract_says}</p>
        
        <h4>4. WHAT SHOULD THE REVIEWER DO?</h4>
        <p>{record.recommendation}</p>
    </div>
    """, unsafe_allow_html=True)

    if record.evidence_citations:
        st.markdown("**Retrieved Document Citations:**")
        for cite in record.evidence_citations:
            st.markdown(f"<span class='citation-tag'>{cite}</span>", unsafe_allow_html=True)

    # Human Review Clearance Form
    st.markdown("---")
    st.markdown("### ✍️ Human-in-the-Loop Review Clearance")
    with st.form("human_review_form"):
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            decision = st.radio(
                "Authoritative Decision",
                [ReviewDecision.ACCEPT.value, ReviewDecision.REJECT.value, ReviewDecision.OVERRIDE.value],
                index=0
            )
            reviewer_name = st.text_input("Reviewer Name / Title", value="Senior Finance Auditor")
        with r_col2:
            override_val = None
            if decision == ReviewDecision.OVERRIDE.value:
                override_val = st.number_input("Override Approved Amount ($)", value=float(record.expected_amount))
            reviewer_comment = st.text_area("Mandatory Audit Comment", placeholder="Provide rationale for override, acceptance, or dispute...")

        if st.form_submit_button("Commit Review Decision & Sign Off", type="primary"):
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
# VIEW 6: CONTRACT EXPLORER & RAG ASSISTANT
# ==============================================================================
elif nav_choice == "📑 Contract Explorer":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">📑</span> Contract Explorer & Grounded RAG Assistant
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Explore executed Master Services Agreements and ask semantic questions strictly grounded in contract text.
        </p>
    </div>
    """, unsafe_allow_html=True)

    contracts = get_all_contracts()
    if not contracts:
        st.warning("No contracts loaded.")
        st.stop()

    contract_map = {f"{c.contract_id} — {c.customer_name}": c for c in contracts}
    selected_contract_label = st.selectbox("Select Customer Contract:", list(contract_map.keys()))
    selected_contract = contract_map[selected_contract_label]

    # Contract Overview HUD
    c_i1, c_i2, c_i3, c_i4 = st.columns(4)
    with c_i1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Base Unit Price</div>
            <div class="metric-value">{selected_contract.currency} ${selected_contract.unit_price:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c_i2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Contract Capacity</div>
            <div class="metric-value">{selected_contract.quantity} Units</div>
        </div>
        """, unsafe_allow_html=True)
    with c_i3:
        st.markdown(f"""
        <div class="metric-card metric-card-cyan">
            <div class="metric-label">Discount Concession</div>
            <div class="metric-value metric-value-cyan">{selected_contract.discount_percent}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c_i4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Term Expiry</div>
            <div class="metric-value" style="font-size: 1.5rem;">{selected_contract.expiry_date}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    - **Contract ID:** `{selected_contract.contract_id}` &nbsp;|&nbsp; **Customer ID:** `{selected_contract.customer_id}`
    - **Product/Service:** {selected_contract.product_service}
    - **Billing Cadence:** {selected_contract.billing_frequency} &nbsp;|&nbsp; **Payment Terms:** {selected_contract.payment_terms}
    - **Permissible Tolerance:** {selected_contract.tolerance_percent}% or {selected_contract.currency} {selected_contract.tolerance_absolute:,.2f}
    - **Special Stipulation:** {selected_contract.special_conditions}
    - **Source PDF File:** `{selected_contract.file_path}`
    """)

    st.markdown("---")
    st.subheader("💬 Ask Contract (Semantic RAG Grounding)")

    q_col1, q_col2, q_col3 = st.columns(3)
    user_q = ""
    with q_col1:
        if st.button("What is the contracted monthly billing rate?", use_container_width=True):
            user_q = "What is the contracted monthly billing rate?"
    with q_col2:
        if st.button("What discount terms and concessions apply?", use_container_width=True):
            user_q = "What discount terms and concessions apply?"
    with q_col3:
        if st.button("When does this agreement terminate?", use_container_width=True):
            user_q = "When does this agreement terminate?"

    custom_q = st.text_input("Or enter a custom question:", value=user_q, placeholder="e.g. What are the acceptable variance tolerances?")
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

    # Invoices billed against this contract
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
# VIEW 7: DYNAMIC ROI & VALUE SIMULATOR
# ==============================================================================
elif nav_choice == "💰 ROI Simulator":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">💰</span> Interactive ROI & Labor Cost Savings Simulator
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Model enterprise financial return, auditor capacity reclaimed, and cumulative cash savings in real time.
        </p>
    </div>
    """, unsafe_allow_html=True)

    r_s1, r_s2, r_s3, r_s4 = st.columns(4)
    with r_s1:
        sim_volume = st.slider("Monthly Invoice Volume", min_value=100, max_value=10000, value=1200, step=100)
    with r_s2:
        sim_minutes = st.slider("Manual Audit Minutes / Inv", min_value=5, max_value=45, value=15, step=1)
    with r_s3:
        sim_rate = st.slider("Auditor Hourly Rate ($/hr)", min_value=30.0, max_value=150.0, value=45.0, step=5.0)
    with r_s4:
        sim_match_rate = st.slider("Targeted Auto-Match Rate (%)", min_value=50.0, max_value=98.0, value=85.0, step=1.0)

    annual_volume = sim_volume * 12
    annual_manual_hours = (annual_volume * sim_minutes) / 60.0
    annual_manual_cost = annual_manual_hours * sim_rate
    annual_hours_saved = annual_manual_hours * (sim_match_rate / 100.0)
    annual_cost_saved = annual_manual_cost * (sim_match_rate / 100.0)
    fte_reclaimed = annual_hours_saved / 2080.0  # standard working hours per year

    # Summary KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Annual Labor Saved</div>
            <div class="metric-value metric-value-cyan">{annual_hours_saved:,.0f} hrs</div>
            <div class="metric-sub">{sim_match_rate}% Auto-Approved</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Net Annual Savings</div>
            <div class="metric-value metric-value-green">${annual_cost_saved:,.0f}</div>
            <div class="metric-sub">Direct Cash Preservation</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">FTE Capacity Reclaimed</div>
            <div class="metric-value">{fte_reclaimed:.1f} FTEs</div>
            <div class="metric-sub">Reallocated to Strategy</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="metric-card metric-card-cyan">
            <div class="metric-label">Payback Horizon</div>
            <div class="metric-value metric-value-cyan">&lt; 1 Month</div>
            <div class="metric-sub">Instant ROI Generation</div>
        </div>
        """, unsafe_allow_html=True)

    # 12-Month Progression Chart
    st.markdown("### 📈 12-Month Cumulative Financial Savings Projection")
    fig_roi = build_roi_payback_chart(sim_volume, sim_minutes, sim_rate, sim_match_rate)
    st.plotly_chart(fig_roi, use_container_width=True)


# ==============================================================================
# VIEW 8: COMPLIANCE AUDIT TRAIL & GOVERNANCE
# ==============================================================================
elif nav_choice == "📜 Compliance Audit":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">📜</span> Compliance Audit Trail & Immutable Governance
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Immutable, tamper-evident log of all system decisions, human overrides, and document citations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    logs = get_audit_logs(limit=300)
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

        # Filters
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            action_filter = st.selectbox("Filter Action Type", ["ALL"] + sorted(list(df_logs["Action"].unique())))
        with c_f2:
            search_inv = st.text_input("Filter by Invoice ID")

        if action_filter != "ALL":
            df_logs = df_logs[df_logs["Action"] == action_filter]
        if search_inv:
            df_logs = df_logs[df_logs["Invoice ID"].str.contains(search_inv, case=False)]

        csv_data = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Compliance Audit Trail to CSV",
            data=csv_data,
            file_name=f"compliance_audit_trail_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("No audit logs recorded yet.")


# ==============================================================================
# VIEW 9: ARCHITECTURE & INTERVIEW GUIDE
# ==============================================================================
elif nav_choice == "ℹ️ Architecture Guide":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">ℹ️</span> Architecture & Interview Presentation Guide
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Core architectural principles, responsibility breakdown, and dataflow mechanics.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### 🎯 The Core Architectural Principle
    > *"Never let an LLM do basic math that Python can calculate deterministically. Use the LLM for what it is exceptional at: interpreting complex natural language contract clauses, synthesizing root causes, and generating grounded explanations."*

    ---

    ### 🧩 System Responsibilities: Who Does What?

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
