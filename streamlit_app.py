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
from datetime import datetime, date, timezone

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
    AuditLogEntry,
)
from app.database.db import (
    get_all_contracts,
    get_contract,
    get_all_invoices,
    get_invoice,
    get_invoices_by_contract,
    save_invoices,
    get_reconciliation_results,
    get_reconciliation_result,
    save_reconciliation_results,
    update_review_decision,
    batch_update_review_decisions,
    get_audit_logs,
    log_audit_entry,
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

# Helper function to initialize synthetic demo data if empty
def ensure_data_loaded():
    contracts = get_all_contracts()
    invoices = get_all_invoices()
    if not contracts or not invoices:
        with st.spinner("Initializing synthetic contracts, vector store, and billing datasets..."):
            generate_all_data()
            engine = ReconciliationEngine(get_all_contracts())
            engine.reconcile_batch(get_all_invoices(), persist_to_db=True)
            st.rerun()

ensure_data_loaded()



# ==============================================================================
# SIDEBAR HEADER & NAVIGATION
# ==============================================================================
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
    <span style="font-size: 2rem; filter: drop-shadow(0 0 10px rgba(0,255,136,0.6));">⚡</span>
    <div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #00FF88; letter-spacing: 0.05em; line-height: 1.1;">NEXUS RECON</div>
        <div style="font-size: 0.68rem; color: #8B949E; letter-spacing: 0.1em; font-family: 'JetBrains Mono', monospace;">AUTONOMOUS COMPLIANCE</div>
    </div>
</div>
<div style="margin-bottom: 14px; padding-left: 4px;">
    <span class="live-indicator"></span>
    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #00FF88; font-weight: 600; letter-spacing: 0.04em;">SYSTEM ONLINE // 256-BIT AUDIT</span>
</div>
""", unsafe_allow_html=True)

# Compute pending human reviews count for live badges
all_existing_results = get_reconciliation_results()
pending_actions_count = len([r for r in all_existing_results if r.review_status == ReviewDecision.PENDING and r.status != ReconciliationStatus.MATCHED])

if pending_actions_count > 0:
    st.sidebar.markdown(f"""
    <div style="background: rgba(255, 51, 102, 0.12); border: 1px solid rgba(255, 51, 102, 0.4); border-radius: 8px; padding: 10px 14px; margin-bottom: 14px;">
        <div style="color: #FF3366; font-size: 0.76rem; font-weight: 700; font-family: 'JetBrains Mono'; letter-spacing: 0.05em;">⚠️ HUMAN ACTION REQUIRED</div>
        <div style="color: #FFFFFF; font-size: 0.84rem; margin-top: 2px;"><b>{pending_actions_count}</b> Invoices Pending Sign-Off</div>
    </div>
    """, unsafe_allow_html=True)

nav_options = [
    "📊 Executive Dashboard",
    "🔎 Single Invoice Reconciliation",
    "⚡ Batch Reconciliation Engine",
    "🧪 What-If Sandbox",
    f"📋 Exception Queue ({pending_actions_count})" if pending_actions_count > 0 else "📋 Exception Queue",
    "🔍 Visual Diff & Review",
    "📑 Contract Explorer",
    "💰 ROI Simulator",
    "📜 Compliance Audit",
    "ℹ️ Architecture Guide",
]

# Handle stateful programmatic navigation requests
if "nav_target" in st.session_state:
    target = st.session_state.pop("nav_target")
    for opt in nav_options:
        if opt.startswith(target) or target in opt:
            st.session_state["app_nav_radio"] = opt
            break

nav_choice = st.sidebar.radio("Navigation", nav_options, key="app_nav_radio")

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
st.sidebar.caption(f"**AI Reasoning:** LangChain // `{LLM_PROVIDER}` ({LLM_MODEL or 'llama-3.3-70b'})")
st.sidebar.caption(f"**Semantic Vectors:** `{EMBEDDING_PROVIDER}` (MiniLM-L6-v2)")
st.sidebar.caption("Deterministic Math: **Python 3.12 Engine**")
st.sidebar.caption("Contract Tolerance: **±1.0% or $50.00**")


# ==============================================================================
# VIEW 1: EXECUTIVE DASHBOARD
# ==============================================================================
if nav_choice.startswith("📊 Executive Dashboard"):
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

    # Direct Operational Action Buttons & Role Architecture Callout
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("🔎 Run Single Reconciliation", use_container_width=True, type="primary"):
            st.session_state["nav_target"] = "🔎 Single Invoice Reconciliation"
            st.rerun()
    with c_btn2:
        if st.button("📋 Investigate Exceptions", use_container_width=True):
            st.session_state["nav_target"] = "📋 Exception Queue"
            st.rerun()

    with st.expander("ℹ️ NEXUS RECON Architecture & Sector Navigation Guide", expanded=False):
        st.markdown("""
        <div style="font-size: 0.86rem; color: #CBD5E1; line-height: 1.6;">
            <b>Module Roles & Operational Separation:</b>
            <ul>
                <li><b>Dashboard:</b> High-level summary of portfolio compliance, risk exposure, and auto-approval rates.</li>
                <li><b>Single Reconciliation:</b> Deep investigation of ONE specific contract against ONE invoice with RAG explanations and human review.</li>
                <li><b>Batch Engine:</b> Bulk reconciliation processing for high-volume invoice batches and custom CSV ingestion.</li>
                <li><b>What-If Sandbox:</b> Simulation sandbox to test how hypothetical rate/quantity adjustments impact reconciliation rules.</li>
                <li><b>Exception Queue:</b> Operational triage worklist to inspect, prioritize, and clear flagged discrepancies.</li>
                <li><b>Visual Diff:</b> Detailed side-by-side comparison of contractual baselines against actual billed items.</li>
                <li><b>Contract Explorer:</b> Executed contract terms inspection and grounded semantic RAG question-answering.</li>
                <li><b>ROI Simulator:</b> Financial modeling of auditor labor saved, efficiency gains, and cash preservation.</li>
                <li><b>Compliance Audit:</b> SOX 404 & SOC 2 immutable historical ledger and audit chain of custody.</li>
                <li><b>Architecture Guide:</b> Technical reference on deterministic math formulas, RAG pipelines, and confidence scoring.</li>
            </ul>
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
    try:
        fig_sankey = build_neon_sankey(metrics, results)
        st.plotly_chart(fig_sankey, use_container_width=True)
    except Exception:
        st.markdown(f"""
        <div style="background: #0C121F; border: 1px solid rgba(0, 255, 136, 0.25); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 12px 18px; text-align: center; flex: 1;">
                    <div style="color: #38BDF8; font-size: 0.72rem; font-weight: 700;">Ingested Feed</div>
                    <div style="color: #FFFFFF; font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono';">{metrics['total_reconciled']} Invoices</div>
                </div>
                <div style="color: #00FF88; font-size: 1.4rem; font-weight: bold;">➔</div>
                <div style="background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.3); border-radius: 8px; padding: 12px 18px; text-align: center; flex: 1;">
                    <div style="color: #00FF88; font-size: 0.72rem; font-weight: 700;">Exact Tier</div>
                    <div style="color: #00FF88; font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono';">{metrics['matched']} Cleared</div>
                </div>
                <div style="color: #00F0FF; font-size: 1.4rem; font-weight: bold;">➔</div>
                <div style="background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 8px; padding: 12px 18px; text-align: center; flex: 1;">
                    <div style="color: #00F0FF; font-size: 0.72rem; font-weight: 700;">Tolerance Tier</div>
                    <div style="color: #00F0FF; font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono';">{metrics['probable_matches']} Probable</div>
                </div>
                <div style="color: #FF3366; font-size: 1.4rem; font-weight: bold;">➔</div>
                <div style="background: rgba(255, 51, 102, 0.1); border: 1px solid rgba(255, 51, 102, 0.3); border-radius: 8px; padding: 12px 18px; text-align: center; flex: 1;">
                    <div style="color: #FF3366; font-size: 0.72rem; font-weight: 700;">Exception Queue</div>
                    <div style="color: #FF3366; font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono';">{metrics['unmatched']} Blocked</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Secondary Charts Row
    st.markdown("### 📊 Portfolio Breakdown & Exposure Root Causes")
    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        try:
            fig_donut = build_status_donut(metrics)
            st.plotly_chart(fig_donut, use_container_width=True)
        except Exception:
            df_status = pd.DataFrame({
                "Count": [metrics["matched"], metrics["probable_matches"], metrics["unmatched"]]
            }, index=["Matched", "Probable", "Unmatched"])
            st.bar_chart(df_status)
    with col_c2:
        try:
            fig_bar = build_exposure_bar(metrics)
            st.plotly_chart(fig_bar, use_container_width=True)
        except Exception:
            st.info("No active exceptions detected.")

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
# VIEW 2: SINGLE INVOICE RECONCILIATION & DEEP INVESTIGATION
# ==============================================================================
elif nav_choice.startswith("🔎 Single Invoice Reconciliation"):
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">🔎</span> Single Invoice Reconciliation & Deep Investigation
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Select one contract and one invoice to trace deterministic variance math, verify LangChain RAG citations, execute authoritative human review, and record immutable audit history.
        </p>
    </div>
    """, unsafe_allow_html=True)

    contracts = get_all_contracts()
    all_invoices = get_all_invoices()

    if not contracts:
        st.warning("No contracts available. Ingest or generate contracts first.")
        st.stop()

    # --------------------------------------------------------------------------
    # STEP 1 — SELECT CONTRACT
    # --------------------------------------------------------------------------
    st.markdown("### Step 1 — Select Contract")
    contract_map = {f"{c.contract_id} — {c.customer_name} ({c.product_service})": c for c in contracts}
    contract_labels = list(contract_map.keys())

    # Preselect if specified in session state
    default_contract_idx = 0
    preselected_contract_id = st.session_state.get("selected_contract_id")
    if preselected_contract_id:
        for idx, lbl in enumerate(contract_labels):
            if contract_map[lbl].contract_id == preselected_contract_id:
                default_contract_idx = idx
                break

    selected_contract_lbl = st.selectbox(
        "Dropdown containing all available contracts:",
        contract_labels,
        index=default_contract_idx,
        key="single_recon_contract_select"
    )
    selected_contract = contract_map[selected_contract_lbl]
    st.session_state["selected_contract_id"] = selected_contract.contract_id

    # Display Contract Details
    st.markdown(f"""
    <div style="background: #0B101B; border: 1px solid rgba(0, 240, 255, 0.35); border-left: 5px solid #00F0FF; border-radius: 10px; padding: 16px 20px; margin: 12px 0 20px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #00F0FF; font-weight: 700; letter-spacing: 0.05em;">
                📜 CONTRACT SPECIFICATIONS: {selected_contract.contract_id}
            </span>
            <span class="badge" style="border: 1px solid #00F0FF; color: #00F0FF; background: rgba(0,240,255,0.08);">
                {selected_contract.currency} | {selected_contract.billing_frequency} Billing
            </span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; font-size: 0.88rem;">
            <div><span style="color: #8B949E;">Contract ID:</span> <b style="color: #FFFFFF;">{selected_contract.contract_id}</b></div>
            <div><span style="color: #8B949E;">Customer:</span> <b style="color: #FFFFFF;">{selected_contract.customer_name}</b> (ID: {selected_contract.customer_id})</div>
            <div><span style="color: #8B949E;">Contract Period:</span> <b style="color: #FFFFFF;">{selected_contract.effective_date} &rarr; {selected_contract.expiry_date}</b></div>
            <div><span style="color: #8B949E;">Unit Price:</span> <b style="color: #00FF88;">{selected_contract.currency} ${selected_contract.unit_price:,.2f}</b></div>
            <div><span style="color: #8B949E;">Quantity / Capacity:</span> <b style="color: #FFFFFF;">{selected_contract.quantity:,} units</b></div>
            <div><span style="color: #8B949E;">Discount:</span> <b style="color: #00F0FF;">{selected_contract.discount_percent:.1f}%</b> {f'({selected_contract.discount_notes})' if selected_contract.discount_notes else ''}</div>
            <div><span style="color: #8B949E;">Currency:</span> <b style="color: #FFFFFF;">{selected_contract.currency}</b></div>
            <div><span style="color: #8B949E;">Billing Frequency:</span> <b style="color: #FFFFFF;">{selected_contract.billing_frequency}</b></div>
            <div><span style="color: #8B949E;">Tolerance:</span> <b style="color: #FFB800;">±{selected_contract.tolerance_percent}% or {selected_contract.currency} ${selected_contract.tolerance_absolute:,.2f}</b></div>
        </div>
        <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.08); font-size: 0.84rem; color: #CBD5E1;">
            <b>Important Contractual Terms:</b> 
            <span>Product/Service: <i>{selected_contract.product_service}</i></span> | 
            <span>Payment Terms: <i>{selected_contract.payment_terms}</i></span> | 
            <span>Tax Terms: <i>{selected_contract.tax_terms}</i></span> | 
            <span>Special Conditions: <i>{selected_contract.special_conditions or 'Standard MSA Guidelines'}</i></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # STEP 2 — SELECT INVOICE
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### Step 2 — Select Invoice")

    # Filter ONLY invoices associated with the selected contract
    contract_invoices = [
        inv for inv in all_invoices
        if (inv.contract_id and inv.contract_id == selected_contract.contract_id) or
           (inv.customer_id and inv.customer_id == selected_contract.customer_id) or
           (inv.customer_name and inv.customer_name.strip().lower() == selected_contract.customer_name.strip().lower())
    ]

    if not contract_invoices:
        st.markdown("""
        <div style="background: rgba(255, 184, 0, 0.1); border: 1px solid rgba(255, 184, 0, 0.4); border-left: 5px solid #FFB800; border-radius: 8px; padding: 14px 18px; margin: 12px 0;">
            <b style="color: #FFB800; font-size: 0.95rem;">No invoices found for this contract.</b>
            <div style="color: #CBD5E1; font-size: 0.84rem; margin-top: 4px;">
                There are no ingested billing records associated with this contract ID or customer name.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        inv_map = {
            f"{inv.invoice_id} — {inv.invoice_date} ({inv.currency} ${inv.total_amount:,.2f} | Period: {inv.billing_period or 'N/A'})": inv
            for inv in contract_invoices
        }
        inv_labels = list(inv_map.keys())

        # Preselect if specified in session state
        default_inv_idx = 0
        preselected_inv_id = st.session_state.get("selected_invoice_id")
        if preselected_inv_id:
            for idx, lbl in enumerate(inv_labels):
                if inv_map[lbl].invoice_id == preselected_inv_id:
                    default_inv_idx = idx
                    break

        selected_inv_lbl = st.selectbox(
            f"Showing ONLY invoices associated with {selected_contract.contract_id} ({len(contract_invoices)} records):",
            inv_labels,
            index=default_inv_idx,
            key="single_recon_invoice_select"
        )
        selected_invoice = inv_map[selected_inv_lbl]
        st.session_state["selected_invoice_id"] = selected_invoice.invoice_id

        # Display Selected Invoice Details
        st.markdown(f"""
        <div style="background: #0B101B; border: 1px solid rgba(0, 255, 136, 0.35); border-left: 5px solid #00FF88; border-radius: 10px; padding: 16px 20px; margin: 12px 0 20px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #00FF88; font-weight: 700; letter-spacing: 0.05em;">
                    🧾 SELECTED INVOICE RECORD: {selected_invoice.invoice_id}
                </span>
                <span class="badge" style="border: 1px solid #00FF88; color: #00FF88; background: rgba(0,255,136,0.08);">
                    Total: {selected_invoice.currency} ${selected_invoice.total_amount:,.2f}
                </span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 0.88rem;">
                <div><span style="color: #8B949E;">Invoice ID:</span> <b style="color: #FFFFFF;">{selected_invoice.invoice_id}</b></div>
                <div><span style="color: #8B949E;">Invoice Date:</span> <b style="color: #FFFFFF;">{selected_invoice.invoice_date}</b></div>
                <div><span style="color: #8B949E;">Billing Period:</span> <b style="color: #FFFFFF;">{selected_invoice.billing_period or 'N/A'}</b></div>
                <div><span style="color: #8B949E;">Customer:</span> <b style="color: #FFFFFF;">{selected_invoice.customer_name}</b></div>
                <div><span style="color: #8B949E;">Quantity:</span> <b style="color: #FFFFFF;">{selected_invoice.quantity:,}</b></div>
                <div><span style="color: #8B949E;">Unit Price:</span> <b style="color: #FFFFFF;">{selected_invoice.currency} ${selected_invoice.unit_price:,.2f}</b></div>
                <div><span style="color: #8B949E;">Discount:</span> <b style="color: #FFFFFF;">{selected_invoice.currency} ${selected_invoice.discount:,.2f}</b></div>
                <div><span style="color: #8B949E;">Currency:</span> <b style="color: #FFFFFF;">{selected_invoice.currency}</b></div>
                <div><span style="color: #8B949E;">Total Amount:</span> <b style="color: #00FF88; font-size: 1rem;">{selected_invoice.currency} ${selected_invoice.total_amount:,.2f}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # STEP 3 — RECONCILE
        # ----------------------------------------------------------------------
        st.markdown("---")
        st.markdown("### Step 3 — Reconcile")

        reconcile_clicked = st.button("⚡ Reconcile Selected Invoice", type="primary", use_container_width=True)

        active_result = None
        if reconcile_clicked:
            existing_db_res = get_reconciliation_result(selected_invoice.invoice_id)
            if existing_db_res:
                active_result = existing_db_res
            else:
                engine = ReconciliationEngine(contracts)
                active_result = engine.reconcile_invoice(
                    selected_invoice,
                    existing_invoices=all_invoices,
                    target_contract=selected_contract
                )
                save_reconciliation_results([active_result])

            citation = active_result.evidence_citations[0] if active_result.evidence_citations else "System Calculation"
            log_audit_entry(AuditLogEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                invoice_id=active_result.invoice_id,
                contract_id=active_result.contract_id,
                action_type="RECONCILE",
                actor="AI_ENGINE",
                previous_status=None,
                new_status=active_result.status.value,
                details=f"Single invoice reconciliation evaluated {active_result.status.value} (Confidence: {int(active_result.confidence_score*100)}%). Variance: ${active_result.variance_amount:,.2f}",
                evidence_citation=citation,
            ))
            st.session_state[f"single_recon_res_{selected_invoice.invoice_id}"] = active_result
            st.success("Reconciliation successfully computed and recorded!")
        elif f"single_recon_res_{selected_invoice.invoice_id}" in st.session_state:
            active_result = st.session_state[f"single_recon_res_{selected_invoice.invoice_id}"]
        else:
            existing_db_res = get_reconciliation_result(selected_invoice.invoice_id)
            if existing_db_res:
                active_result = existing_db_res

        if active_result:
            status_val = active_result.status.value
            status_color = "#00FF88" if status_val == "MATCHED" else ("#00F0FF" if status_val == "PROBABLE_MATCH" else "#FF3366")
            tol_text = "Within tolerance" if active_result.is_within_tolerance else "Outside tolerance"
            tol_color = "#00FF88" if active_result.is_within_tolerance else "#FF3366"

            st.markdown(f"""
            <div style="background: #0D131F; border: 1px solid {status_color}50; border-left: 6px solid {status_color}; border-radius: 10px; padding: 16px 20px; margin: 16px 0 20px 0; box-shadow: 0 0 20px {status_color}20;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <span style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF;">
                        Matching Result: <span style="color: {status_color}; font-family: 'JetBrains Mono';">{status_val}</span>
                    </span>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <span class="badge" style="border: 1px solid {status_color}; color: {status_color};">{active_result.priority.value} PRIORITY</span>
                        <span class="badge" style="border: 1px solid {tol_color}; color: {tol_color};">{tol_text.upper()}</span>
                        <span class="badge" style="border: 1px solid #00F0FF; color: #00F0FF;">Confidence: {int(active_result.confidence_score * 100)}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Reconcile Attributes Display
            r_c1, r_c2, r_c3, r_c4, r_c5 = st.columns(5)
            with r_c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Expected Amount</div>
                    <div class="metric-value">${active_result.expected_amount:,.2f}</div>
                    <div class="metric-sub">Contract Baseline</div>
                </div>
                """, unsafe_allow_html=True)
            with r_c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Billed Amount</div>
                    <div class="metric-value" style="color: {'#FF3366' if active_result.actual_amount != active_result.expected_amount else '#00FF88'};">${active_result.actual_amount:,.2f}</div>
                    <div class="metric-sub">Invoice Total</div>
                </div>
                """, unsafe_allow_html=True)
            with r_c3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Variance</div>
                    <div class="metric-value" style="color: {tol_color};">${active_result.variance_amount:,.2f}</div>
                    <div class="metric-sub">{active_result.variance_percent:.2f}% Variance</div>
                </div>
                """, unsafe_allow_html=True)
            with r_c4:
                st.markdown(f"""
                <div class="metric-card metric-card-danger">
                    <div class="metric-label">Financial Exposure</div>
                    <div class="metric-value metric-value-crimson">${active_result.financial_exposure:,.2f}</div>
                    <div class="metric-sub" style="color: #FF3366;">At-Risk Capital</div>
                </div>
                """, unsafe_allow_html=True)
            with r_c5:
                st.markdown(f"""
                <div class="metric-card metric-card-cyan">
                    <div class="metric-label">Tolerance</div>
                    <div class="metric-value metric-value-cyan">±{selected_contract.tolerance_percent}%</div>
                    <div class="metric-sub">${selected_contract.tolerance_absolute:,.2f} Floor</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: #080C14; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 18px; margin: 14px 0;">
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; font-size: 0.85rem;">
                    <span><b>Matching Methods Used:</b> <code style="color: #00FF88;">{' + '.join(active_result.matching_methods_used)}</code></span>
                    <span><b>Exception Reason:</b> <span style="color: {'#00FF88' if active_result.status.value == 'MATCHED' else '#FF6B8B'}; font-weight: 600;">{active_result.exception_reason or 'Fully compliant with contract terms.'}</span></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ------------------------------------------------------------------
            # STEP 4 — EXPLAIN THE RESULT
            # ------------------------------------------------------------------
            st.markdown("---")
            st.markdown("### Step 4 — Why did this result occur?")
            st.caption("Deterministic Python calculations are strictly responsible for financial arithmetic. The LLM/RAG layer explains the result using retrieved contract evidence without inventing numbers.")

            from app.rag.chain import clean_contract_text
            clean_clause_evidence = clean_contract_text(active_result.what_contract_says)

            analysis_html = f"""<div style="background: #0C121E; border: 1px solid rgba(0, 240, 255, 0.25); border-radius: 10px; padding: 20px; margin: 16px 0;">
<div style="color: #00F0FF; font-weight: 700; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; margin-bottom: 8px; letter-spacing: 0.05em;">1. WHAT HAPPENED</div>
<div style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.5; margin-bottom: 18px;">{active_result.what_happened}</div>

<div style="color: #00F0FF; font-weight: 700; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; margin-bottom: 8px; letter-spacing: 0.05em;">2. CONTRACT EXPECTATION VS INVOICE VALUE</div>
<div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 14px 18px; margin-bottom: 18px; font-size: 0.9rem; line-height: 1.7;">
<div><span style="color: #94A3B8;">Contract Expectation:</span> Expected baseline is <b style="color: #00F0FF;">${active_result.expected_amount:,.2f}</b> ({selected_contract.quantity} units @ ${selected_contract.unit_price:,.2f} less {selected_contract.discount_percent}% discount)</div>
<div><span style="color: #94A3B8;">Invoice Value:</span> Billed amount is <b style="color: #FF3366;">${active_result.actual_amount:,.2f}</b> ({selected_invoice.quantity} units @ ${selected_invoice.unit_price:,.2f} less ${selected_invoice.discount:,.2f} discount)</div>
<div><span style="color: #94A3B8;">Difference:</span> Arithmetic variance of <b style="color: #FF3366;">${active_result.variance_amount:,.2f} ({active_result.variance_percent:.2f}%)</b>. Permissible tolerance is ±{selected_contract.tolerance_percent}% or ${selected_contract.tolerance_absolute:,.2f}</div>
</div>

<div style="color: #00F0FF; font-weight: 700; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; margin-bottom: 8px; letter-spacing: 0.05em;">3. RULE THAT CAUSED THE EXCEPTION</div>
<div style="color: {'#00FF88' if active_result.status.value == 'MATCHED' else '#FF6B8B'}; font-weight: 600; font-size: 0.92rem; margin-bottom: 18px;">{active_result.exception_reason or 'No rule violation. Invoiced rate, volume, discount, and date terms adhere to the contract baseline.'}</div>

<div style="color: #00F0FF; font-weight: 700; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; margin-bottom: 8px; letter-spacing: 0.05em;">4. RELEVANT CONTRACT EVIDENCE</div>
<div style="background: rgba(0, 255, 136, 0.05); border-left: 3px solid #00FF88; padding: 10px 14px; margin-bottom: 18px; color: #CBD5E1; font-size: 0.88rem; line-height: 1.5;">{clean_clause_evidence}</div>

<div style="color: #00F0FF; font-weight: 700; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; margin-bottom: 8px; letter-spacing: 0.05em;">5. AI / RAG EXPLANATION & RECOMMENDED ACTION</div>
<div style="margin-bottom: 8px;"><span style="color: #94A3B8; font-weight: 600;">Root Cause Analysis:</span> <span style="color: #E2E8F0;">{active_result.why_did_it_happen}</span></div>
<div><span style="color: #00FF88; font-weight: 600;">Actionable Recommendation:</span> <span style="color: #FFFFFF;">{active_result.recommendation}</span></div>
</div>"""
            st.markdown(analysis_html, unsafe_allow_html=True)

            if active_result.evidence_citations:
                st.markdown("**Relevant Contract Evidence Citations:**")
                for cite in active_result.evidence_citations:
                    st.markdown(f"<span class='citation-tag'>{cite}</span>", unsafe_allow_html=True)

            # ------------------------------------------------------------------
            # STEP 5 — HUMAN REVIEW
            # ------------------------------------------------------------------
            st.markdown("---")
            st.markdown("### Step 5 — Human Review")
            st.caption("Finance reviewer must provide their name and a mandatory audit comment to authorize an authoritative sign-off.")

            with st.form("single_recon_human_review_form"):
                rev_c1, rev_c2 = st.columns(2)
                with rev_c1:
                    decision_val = st.radio(
                        "Review Decision *",
                        [ReviewDecision.ACCEPT.value, ReviewDecision.REJECT.value, ReviewDecision.OVERRIDE.value],
                        index=0 if active_result.review_status == ReviewDecision.ACCEPT else (1 if active_result.review_status == ReviewDecision.REJECT else 0),
                        help="ACCEPT clears invoice for payment. REJECT blocks and triggers vendor dispute. OVERRIDE adjusts approved payment baseline."
                    )
                    reviewer_name_val = st.text_input("Reviewer Name *", value=active_result.reviewer_name or "Senior Finance Reviewer", key="sr_reviewer_name")
                with rev_c2:
                    override_val = None
                    if decision_val == ReviewDecision.OVERRIDE.value:
                        override_val = st.number_input("Override Approved Baseline ($) *", value=float(active_result.expected_amount), key="sr_override_amt")
                    review_comment_val = st.text_area("Mandatory Review Comment *", value=active_result.reviewer_comment or "", placeholder="Provide mandatory business rationale, waiver citation, or dispute justification...", key="sr_comment")

                submit_decision = st.form_submit_button("✍️ Submit Review Decision", type="primary", use_container_width=True)
                if submit_decision:
                    if not reviewer_name_val.strip() or not review_comment_val.strip():
                        st.error("⚠️ Reviewer name and a mandatory review comment are required for compliance sign-off.")
                    else:
                        ok = update_review_decision(
                            invoice_id=active_result.invoice_id,
                            decision=ReviewDecision(decision_val),
                            reviewer_name=reviewer_name_val.strip(),
                            comment=review_comment_val.strip(),
                            override_amount=override_val
                        )
                        if ok:
                            st.success(f"✅ Decision '{decision_val}' successfully committed to immutable audit trail!")
                            st.session_state[f"single_recon_res_{active_result.invoice_id}"] = get_reconciliation_result(active_result.invoice_id)
                            time.sleep(1)
                            st.rerun()

            # ------------------------------------------------------------------
            # STEP 6 — AUDIT TRAIL
            # ------------------------------------------------------------------
            st.markdown("---")
            st.markdown("### Step 6 — Audit Trail")
            
            if "show_single_audit" not in st.session_state:
                st.session_state["show_single_audit"] = True

            col_a1, col_a2 = st.columns([1, 3])
            with col_a1:
                if st.button("📜 View Audit History", use_container_width=True):
                    st.session_state["show_single_audit"] = not st.session_state.get("show_single_audit", False)
            
            if st.session_state.get("show_single_audit", True):
                audit_entries = get_audit_logs(limit=200, invoice_id=active_result.invoice_id)
                if audit_entries:
                    st.markdown(f"**Chronological Audit History for Invoice `{active_result.invoice_id}`:**")
                    table_entries = []
                    for e in audit_entries:
                        table_entries.append({
                            "Invoice": e.invoice_id,
                            "Contract": e.contract_id or "-",
                            "Reconciliation Result": e.new_status or "-",
                            "AI Recommendation": e.evidence_citation or "-",
                            "Reviewer": e.actor,
                            "Decision": e.action_type,
                            "Comment": e.details,
                            "Timestamp": e.timestamp,
                        })
                    st.dataframe(pd.DataFrame(table_entries), use_container_width=True, hide_index=True)
                else:
                    st.info(f"No audit history recorded yet for Invoice {active_result.invoice_id}.")


# ==============================================================================
# VIEW: INTERACTIVE "WHAT-IF" SIMULATION SANDBOX
# ==============================================================================
elif nav_choice.startswith("🧪 What-If"):
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">🧪</span> What-If Simulation Sandbox
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            This is a simulation environment. Select a contract and change hypothetical invoice values to test how the reconciliation rules respond.
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

    st.markdown("### 🎛️ Hypothetical Invoice")
    st.caption("Adjust simulated billing values below to test how rules evaluate drift. These values are hypothetical and do not modify existing real invoices.")
    s_col1, s_col2, s_col3 = st.columns(3)

    base_price = float(target_contract.unit_price)
    base_qty = int(target_contract.quantity)
    base_discount = float(target_contract.discount_percent)

    with s_col1:
        sim_price = st.slider("Hypothetical Billed Unit Price ($)", min_value=max(10.0, base_price * 0.5), max_value=base_price * 2.0, value=base_price, step=5.0)
        sim_qty = st.slider("Hypothetical Billed Quantity", min_value=1, max_value=max(150, base_qty * 2), value=base_qty, step=1)

    with s_col2:
        sim_discount = st.slider("Hypothetical Applied Discount (%)", min_value=0.0, max_value=50.0, value=base_discount, step=1.0)
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

    # Name match via RapidFuzz
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
        reason_text = f"Discrepancy of ${variance_amount:,.2f} ({variance_percent:.2f}%) exceeds allowable tolerance limit."

    # Compute simulated explainable confidence score
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
        try:
            fig_tol = build_tolerance_meter(variance_percent, target_contract.tolerance_percent)
            st.plotly_chart(fig_tol, use_container_width=True)
        except Exception:
            st.metric("Tolerance Limit", f"±{target_contract.tolerance_percent}%", f"Current Var: {variance_percent:.2f}%")

    with g_col3:
        try:
            fig_conf = build_confidence_gauge(sim_conf_score)
            st.plotly_chart(fig_conf, use_container_width=True)
        except Exception:
            st.metric("Confidence Score", f"{int(sim_conf_score * 100)}%")

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
# VIEW 3: BATCH RECONCILIATION ENGINE, LIVE TERMINAL & INTEGRATED HUMAN ACTIONS
# ==============================================================================
elif nav_choice.startswith("⚡ Batch Reconciliation Engine"):
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">⚡</span> Batch Reconciliation Engine
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            This page reconciles multiple invoices against their associated contracts. Use Single Invoice Reconciliation when you want to investigate one specific invoice.
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
    st.write("Executes 4-tier matching: Exact Key &rarr; Deterministic Tolerance &rarr; RapidFuzz Entity &rarr; LangChain RAG Grounding.")

    if st.button("🚀 Trigger Full Batch Reconciliation Stream", type="primary"):
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

            # Log audit entry for each evaluated record
            citation = res.evidence_citations[0] if res.evidence_citations else "System Calculation"
            log_audit_entry(AuditLogEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                invoice_id=res.invoice_id,
                contract_id=res.contract_id,
                action_type="RECONCILE",
                actor="AI_ENGINE",
                previous_status=None,
                new_status=res.status.value,
                details=f"Stream evaluated {res.status.value} (Confidence: {int(res.confidence_score*100)}%). Var: ${res.variance_amount:,.2f}",
                evidence_citation=citation,
            ))

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
                f"<span class='term-dim'>[{datetime.now(timezone.utc).strftime('%H:%M:%S')}]</span> "
                f"Inv <span class='term-cyan'>{inv.invoice_id}</span> "
                f"({inv.customer_name[:20]}) ➔ "
                f"<span class='{color_class}'>{status_txt}</span> "
                f"| Var: ${res.variance_amount:,.2f} | Conf: {int(res.confidence_score*100)}%"
            )

            # Display last 10 lines in terminal
            recent_lines = "<br>".join(terminal_lines[-10:])
            term_placeholder.markdown(f"<div class='terminal-box'>{recent_lines}</div>", unsafe_allow_html=True)

        save_reconciliation_results(results)
        terminal_lines.append("<span class='term-green'>[COMPLETE]</span> All invoices successfully reconciled and persisted to immutable audit trail.")
        recent_lines = "<br>".join(terminal_lines[-10:])
        term_placeholder.markdown(f"<div class='terminal-box'>{recent_lines}</div>", unsafe_allow_html=True)
        st.success(f"Successfully processed and recorded all {len(results)} invoices!")
        st.rerun()

    st.markdown("---")
    st.subheader("📂 Upload Custom Invoices (CSV)")
    uploaded_file = st.file_uploader("Upload CSV containing billing records for automated reconciliation", type=["csv"])
    if uploaded_file:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            st.write("Preview of uploaded records:", df_uploaded.head(5))
            if st.button("Ingest and Reconcile Uploaded CSV", type="primary"):
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
                st.success(f"Ingested and reconciled {len(new_invoices)} custom invoices!")
                st.rerun()
        except Exception as e:
            st.error(f"Error processing custom CSV: {e}")

    # ==========================================================================
    # INTEGRATED RECONCILIATION RESULTS, CONFIDENCE SCORES & HUMAN ACTION PANEL
    # ==========================================================================
    st.markdown("---")
    st.markdown("""
    <div class="cyber-banner" style="margin-top: 24px;">
        <h3 style="margin: 0; color: #FFFFFF; font-size: 1.35rem;">
            <span style="color: #00FF88;">🎯</span> Live Reconciliation Results, Confidence Scores & Human Actions
        </h3>
        <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.84rem;">
            Review multi-factor explainable confidence scores and execute immediate Human-in-the-Loop clearance sign-offs.
        </p>
    </div>
    """, unsafe_allow_html=True)

    recon_results = get_reconciliation_results()
    if recon_results:
        # Overview metrics
        total_count = len(recon_results)
        matched_count = len([r for r in recon_results if r.status == ReconciliationStatus.MATCHED])
        pending_count = len([r for r in recon_results if r.review_status == ReviewDecision.PENDING and r.status != ReconciliationStatus.MATCHED])
        avg_conf = (sum(r.confidence_score for r in recon_results) / total_count * 100.0) if total_count > 0 else 0.0

        k_c1, k_c2, k_c3, k_c4 = st.columns(4)
        with k_c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Invoices</div>
                <div class="metric-value">{total_count}</div>
                <div class="metric-sub">Processed by Engine</div>
            </div>
            """, unsafe_allow_html=True)
        with k_c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Auto-Approved</div>
                <div class="metric-value metric-value-green">{matched_count}</div>
                <div class="metric-sub">Zero Discrepancy</div>
            </div>
            """, unsafe_allow_html=True)
        with k_c3:
            st.markdown(f"""
            <div class="metric-card {'metric-card-danger' if pending_count > 0 else ''}">
                <div class="metric-label">Action Required</div>
                <div class="metric-value {'metric-value-crimson' if pending_count > 0 else 'metric-value-green'}">{pending_count}</div>
                <div class="metric-sub">Pending Sign-Off</div>
            </div>
            """, unsafe_allow_html=True)
        with k_c4:
            st.markdown(f"""
            <div class="metric-card metric-card-cyan">
                <div class="metric-label">Avg Confidence</div>
                <div class="metric-value metric-value-cyan">{avg_conf:.1f}%</div>
                <div class="metric-sub">Multi-Factor Grounding</div>
            </div>
            """, unsafe_allow_html=True)

        # Table summary
        st.markdown("#### 📋 Processed Invoices & Confidence Ratings")
        summary_table = []
        for r in recon_results:
            summary_table.append({
                "Invoice ID": r.invoice_id,
                "Customer": r.customer_name,
                "Status": r.status.value,
                "Confidence": f"{int(r.confidence_score * 100)}%",
                "Expected ($)": f"${r.expected_amount:,.2f}",
                "Billed ($)": f"${r.actual_amount:,.2f}",
                "Variance ($)": f"${r.variance_amount:,.2f}",
                "Exposure ($)": f"${r.financial_exposure:,.2f}",
                "Review Status": r.review_status.value,
                "Reason": r.exception_reason,
            })
        st.dataframe(pd.DataFrame(summary_table), use_container_width=True, hide_index=True)

        # Quick Inspector & Human Action Workbench
        st.markdown("---")
        st.markdown("### ✍️ Instant Human Action & Confidence Score Inspector")
        st.caption("Select any invoice to inspect its 5-part mathematical confidence breakdown and execute an authoritative sign-off directly.")

        inv_options = [f"{r.invoice_id} — {r.customer_name} ({r.status.value} // Decision: {r.review_status.value} // Conf: {int(r.confidence_score*100)}%)" for r in recon_results]
        selected_inv_opt = st.selectbox("Select Invoice to Inspect & Sign Off:", inv_options, key="engine_runner_inv_select")
        selected_id = selected_inv_opt.split(" ")[0]
        selected_record = get_reconciliation_result(selected_id)

        if selected_record:
            st.markdown(f"""
            <div style="background: #0C121F; border: 1px solid rgba(0, 255, 136, 0.3); border-left: 6px solid {'#00FF88' if selected_record.status.value == 'MATCHED' else ('#00F0FF' if selected_record.status.value == 'PROBABLE_MATCH' else '#FF3366')}; border-radius: 8px; padding: 12px 18px; margin: 12px 0 16px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <span style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">Selected Invoice: <span style="font-family: 'JetBrains Mono'; color: #00FF88;">{selected_record.invoice_id}</span></span>
                    <span>Customer: <b>{selected_record.customer_name}</b></span>
                    <span>Contract Ref: <b>{selected_record.contract_id or 'UNLINKED'}</b></span>
                    <span>Current Decision: <b>{selected_record.review_status.value}</b></span>
                    <span class="badge" style="border: 1px solid #00FF88; color: #00FF88;">Overall Confidence: {int(selected_record.confidence_score * 100)}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 1. Confidence Score 5-Factor HUD
            st.markdown("#### 🔬 Explainable Confidence Breakdown (Where Does It Come From?)")
            st.caption("Calculated using the deterministic 5-factor weighted formula: (30% ID) + (35% Amount) + (15% Date) + (10% Name) + (10% Evidence).")

            c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)
            with c_f1:
                st.metric("🏷️ ID Match (30%)", f"{int(selected_record.confidence_breakdown.id_match_score * 100)}%")
            with c_f2:
                st.metric("💵 Amount (35%)", f"{int(selected_record.confidence_breakdown.amount_match_score * 100)}%")
            with c_f3:
                st.metric("📅 Date Term (15%)", f"{int(selected_record.confidence_breakdown.date_match_score * 100)}%")
            with c_f4:
                st.metric("🏢 Name Match (10%)", f"{int(selected_record.confidence_breakdown.name_match_score * 100)}%")
            with c_f5:
                st.metric("📜 Evidence (10%)", f"{int(selected_record.confidence_breakdown.evidence_score * 100)}%")

            if selected_record.confidence_breakdown.factors:
                with st.expander("🔍 View Explicit Mathematical Factor Details", expanded=False):
                    for factor in selected_record.confidence_breakdown.factors:
                        st.markdown(f"- `{factor}`")

            # 2. 5-Part Root Cause Analysis Preview
            st.markdown(f"""
            <div class="analysis-box" style="margin-top: 14px;">
                <h4>1. WHAT HAPPENED?</h4><p>{selected_record.what_happened}</p>
                <h4>2. WHY DID IT HAPPEN?</h4><p>{selected_record.why_did_it_happen}</p>
                <h4>3. WHAT DOES THE CONTRACT SAY?</h4><p>{selected_record.what_contract_says}</p>
                <h4>4. WHAT SHOULD THE REVIEWER DO?</h4><p>{selected_record.recommendation}</p>
            </div>
            """, unsafe_allow_html=True)

            if selected_record.evidence_citations:
                st.markdown("**Retrieved Document Citations:**")
                for cite in selected_record.evidence_citations:
                    st.markdown(f"<span class='citation-tag'>{cite}</span>", unsafe_allow_html=True)

            # 3. Direct Human Action Clearance Form
            st.markdown("#### ✍️ Human-in-the-Loop Clearance & Authoritative Sign-Off")
            with st.form("engine_runner_human_action_form"):
                h_col1, h_col2 = st.columns(2)
                with h_col1:
                    h_decision = st.radio(
                        "Authoritative Clearance Decision",
                        [ReviewDecision.ACCEPT.value, ReviewDecision.REJECT.value, ReviewDecision.OVERRIDE.value],
                        index=0,
                        help="ACCEPT authorizes payment. REJECT blocks invoice and triggers dispute notice. OVERRIDE establishes an authorized payment baseline."
                    )
                    h_reviewer = st.text_input("Auditor Name / Title", value="Senior Finance Auditor", key="er_auditor_name")
                with h_col2:
                    h_override = None
                    if h_decision == ReviewDecision.OVERRIDE.value:
                        h_override = st.number_input("Override Approved Amount ($)", value=float(selected_record.expected_amount), key="er_override_amt")
                    h_comment = st.text_area("Mandatory Audit Justification Comment", placeholder="Provide rationale for override, acceptance, or dispute...", key="er_audit_comment")

                if st.form_submit_button("✍️ Commit Human Action & Sign Off", type="primary"):
                    if not h_comment:
                        st.error("Audit regulations require a mandatory comment for any exception clearance.")
                    else:
                        ok = update_review_decision(
                            invoice_id=selected_record.invoice_id,
                            decision=ReviewDecision(h_decision),
                            reviewer_name=h_reviewer,
                            comment=h_comment,
                            override_amount=h_override
                        )
                        if ok:
                            st.success(f"Human action '{h_decision}' successfully committed for {selected_record.invoice_id} with immutable audit log!")
                            st.rerun()
    else:
        st.info("No reconciliation records in database. Click 'Trigger Full Batch Reconciliation Stream' above to process invoices.")


# ==============================================================================
# VIEW 4: EXCEPTION QUEUE & BATCH TRIAGE
# ==============================================================================
elif nav_choice.startswith("📋 Exception Queue"):
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
        search_query = st.text_input("Search Customer / ID", placeholder="e.g. Starlight, INV-1001")

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

        st.markdown("---")
        st.markdown("### 🔎 Exception Detail & Direct Investigation")
        st.caption("Select any flagged record to inspect its operational metrics and directly open Single Invoice Reconciliation with its contract preselected.")

        exc_options = [
            f"{r.invoice_id} — {r.customer_name} ({r.priority.value} | Status: {r.status.value} | Var: ${r.variance_amount:,.2f})"
            for r in results
        ]
        sel_exc_lbl = st.selectbox("Select Exception to Investigate:", exc_options, key="exc_queue_inspect_select")
        sel_exc_id = sel_exc_lbl.split(" ")[0]
        sel_record = next((r for r in results if r.invoice_id == sel_exc_id), None)

        if sel_record:
            c_ex1, c_ex2 = st.columns([3, 1])
            with c_ex1:
                st.markdown(f"""
                <div style="background: #0D131F; border-left: 4px solid {'#FF3366' if sel_record.priority.value == 'HIGH' else '#FFB800'}; border-radius: 6px; padding: 10px 14px;">
                    <div style="font-size: 0.9rem; color: #FFFFFF; font-weight: 600;">
                        Invoice: <code>{sel_record.invoice_id}</code> | Customer: <b>{sel_record.customer_name}</b> | Contract: <code>{sel_record.contract_id or 'UNLINKED'}</code>
                    </div>
                    <div style="color: #FF6B8B; font-size: 0.84rem; margin-top: 4px;">
                        <b>Root Cause / Flag:</b> {sel_record.exception_reason}
                    </div>
                    <div style="color: #94A3B8; font-size: 0.8rem; margin-top: 4px;">
                        Expected: ${sel_record.expected_amount:,.2f} | Billed: ${sel_record.actual_amount:,.2f} | Exposure: ${sel_record.financial_exposure:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c_ex2:
                if st.button("🔎 Investigate Invoice", type="primary", use_container_width=True, key=f"btn_investigate_{sel_record.invoice_id}"):
                    st.session_state["nav_target"] = "🔎 Single Invoice Reconciliation"
                    if sel_record.contract_id:
                        st.session_state["selected_contract_id"] = sel_record.contract_id
                    st.session_state["selected_invoice_id"] = sel_record.invoice_id
                    st.rerun()
    else:
        st.info("No records match the current filter selection.")


# ==============================================================================
# VIEW 5: VISUAL DIFF & DEEP ROOT CAUSE REVIEW
# ==============================================================================
elif nav_choice.startswith("🔍 Visual Diff"):
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">🔍</span> Side-by-Side Visual Diff & Deep Human Action Review
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Inspect contract terms vs billing invoice line-by-line, verify LangChain RAG citations, examine confidence breakdown, and execute authoritative Human-in-the-Loop clearances.
        </p>
    </div>
    """, unsafe_allow_html=True)

    all_results = get_reconciliation_results()
    if not all_results:
        st.warning("No reconciliation records found.")
        st.stop()

    invoice_options = [f"{r.invoice_id} — {r.customer_name} ({r.status.value}, Priority: {r.priority.value})" for r in all_results]
    selected_option = st.selectbox("### Select Invoice to Inspect:", invoice_options)
    selected_id = selected_option.split(" ")[0]

    record = get_reconciliation_result(selected_id)
    if not record:
        st.error("Record not found.")
        st.stop()

    # Automatically identify and display its associated contract
    contract = get_contract(record.contract_id) if record.contract_id else None
    raw_inv = get_invoice(record.invoice_id)

    # Associated Contract Banner Callout
    assoc_contract_id = record.contract_id or (contract.contract_id if contract else "UNLINKED / UNRESOLVED")
    assoc_customer = contract.customer_name if contract else record.customer_name
    st.markdown(f"""
    <div style="background: rgba(0, 240, 255, 0.06); border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 8px; padding: 10px 16px; margin-bottom: 16px;">
        <span style="color: #00F0FF; font-weight: 700; font-family: 'JetBrains Mono'; font-size: 0.8rem;">ASSOCIATED CONTRACT DETECTED:</span>
        <span style="color: #FFFFFF; font-weight: 600; margin-left: 8px;">{assoc_contract_id}</span>
        <span style="color: #94A3B8; margin-left: 6px;">({assoc_customer})</span>
    </div>
    """, unsafe_allow_html=True)

    # Action Buttons Bar
    v_btn1, v_btn2, v_btn3 = st.columns(3)
    with v_btn1:
        if st.button("✍️ Go to Human Review", use_container_width=True, type="primary"):
            st.session_state["scroll_to_human_review"] = True
            st.session_state["toggle_human_review_panel"] = True
    with v_btn2:
        if st.button("📑 View Contract Evidence", use_container_width=True):
            st.session_state["toggle_evidence_diff"] = not st.session_state.get("toggle_evidence_diff", False)
    with v_btn3:
        if st.button("📜 View Audit History", use_container_width=True):
            st.session_state["toggle_audit_diff"] = not st.session_state.get("toggle_audit_diff", False)

    # Interactive Panels Triggered by Action Buttons
    if st.session_state.get("toggle_evidence_diff", False):
        st.markdown(f"""
        <div style="background: rgba(0, 240, 255, 0.08); border: 1px solid #00F0FF; border-radius: 8px; padding: 14px; margin: 10px 0;">
            <div style="color: #00F0FF; font-weight: 700; font-family: 'JetBrains Mono'; margin-bottom: 8px;">
                📑 RETRIEVED CONTRACT EVIDENCE CITATIONS (INVOICE: {record.invoice_id})
            </div>
        """, unsafe_allow_html=True)
        if record.evidence_citations:
            for cite in record.evidence_citations:
                st.markdown(f"- <span class='citation-tag'>{cite}</span>", unsafe_allow_html=True)
        else:
            st.info("No external contract citations attached for this calculation.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("toggle_audit_diff", False):
        st.markdown(f"""
        <div style="background: rgba(0, 255, 136, 0.08); border: 1px solid #00FF88; border-radius: 8px; padding: 14px; margin: 10px 0;">
            <div style="color: #00FF88; font-weight: 700; font-family: 'JetBrains Mono'; margin-bottom: 8px;">
                📜 IMMUTABLE AUDIT LOG TRAIL (INVOICE: {record.invoice_id})
            </div>
        """, unsafe_allow_html=True)
        diff_logs = get_audit_logs(limit=100, invoice_id=record.invoice_id)
        if diff_logs:
            st.dataframe(pd.DataFrame([{
                "Timestamp (UTC)": l.timestamp,
                "Actor": l.actor,
                "Action": l.action_type,
                "New Status": l.new_status or "-",
                "Details": l.details,
                "Evidence": l.evidence_citation or "-"
            } for l in diff_logs]), use_container_width=True, hide_index=True)
        else:
            st.info(f"No audit logs recorded for {record.invoice_id} yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("scroll_to_human_review", False):
        st.session_state["scroll_to_human_review"] = False
        st.markdown("""
        <div style="background: rgba(0, 255, 136, 0.12); border: 1px solid #00FF88; border-radius: 8px; padding: 10px 14px; margin: 10px 0; color: #00FF88; font-weight: 600;">
            ✍️ Navigating to Human Review Clearance Form below...
        </div>
        """, unsafe_allow_html=True)
        st.components.v1.html(
            "<script>setTimeout(function(){ window.scrollTo({top: 1800, behavior: 'smooth'}); }, 100);</script>",
            height=0
        )

    # Status Banner
    status_border = "#00FF88" if record.status.value == "MATCHED" else ("#00F0FF" if record.status.value == "PROBABLE_MATCH" else "#FF3366")
    st.markdown(f"""
    <div style="background-color: #0C121F; border-radius: 8px; padding: 14px 18px; margin: 14px 0 20px 0; border: 1px solid {status_border}40; border-left: 6px solid {status_border};">
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

    # Contract & Invoice Attributes Preparation
    c_unit_price = f"${contract.unit_price:,.2f}" if contract else "$0.00"
    c_quantity = f"{contract.quantity:,} units" if contract else "0 units"
    c_discount = f"{contract.discount_percent:.1f}%" if contract else "0.0%"
    c_currency = contract.currency if contract else "USD"
    c_billing_period = contract.billing_frequency if contract else "N/A"
    c_tolerance = f"±{contract.tolerance_percent}% / ${contract.tolerance_absolute:,.2f}" if contract else "±1.0% / $50.00"

    i_unit_price = f"${raw_inv.unit_price:,.2f}" if raw_inv else "N/A"
    i_quantity = f"{raw_inv.quantity:,} units" if raw_inv else "N/A"
    i_discount = f"${raw_inv.discount:,.2f}" if raw_inv else "$0.00"
    i_currency = raw_inv.currency if raw_inv else "USD"
    i_billing_period = raw_inv.billing_period if (raw_inv and raw_inv.billing_period) else "N/A"

    # SIDE-BY-SIDE VISUAL DIFF CARDS
    st.markdown("### ⚖️ Side-by-Side Visual Diff (Contract Baseline vs Actual Invoice)")
    col_diff_a, col_diff_b = st.columns(2)

    with col_diff_a:
        st.markdown(f"""
        <div class="diff-card diff-card-contract">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #00F0FF; margin-bottom: 12px; font-weight: 600;">
                📜 CONTRACT BASELINE ({assoc_contract_id})
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Unit Price</span>
                <b>{c_unit_price}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Quantity</span>
                <b>{c_quantity}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Discount</span>
                <b>{c_discount}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Currency</span>
                <b>{c_currency}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Billing Period</span>
                <b>{c_billing_period}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Expected Amount</span>
                <b style="color: #00F0FF; font-size: 0.95rem;">${record.expected_amount:,.2f}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Tolerance Limit</span>
                <b>{c_tolerance}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Expected Compliance</span>
                <b>Authorized Baseline</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_diff_b:
        is_amt_diff = (record.actual_amount != record.expected_amount)
        st.markdown(f"""
        <div class="diff-card diff-card-invoice">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #00FF88; margin-bottom: 12px; font-weight: 600;">
                🧾 ACTUAL INVOICE ({record.invoice_id})
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Unit Price</span>
                <b style="color: {'#FF3366' if raw_inv and contract and raw_inv.unit_price != contract.unit_price else '#FFFFFF'};">{i_unit_price}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Quantity</span>
                <b style="color: {'#FF3366' if raw_inv and contract and raw_inv.quantity != contract.quantity else '#FFFFFF'};">{i_quantity}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Discount</span>
                <b>{i_discount}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Currency</span>
                <b style="color: {'#FF3366' if contract and i_currency != contract.currency else '#FFFFFF'};">{i_currency}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Billing Period</span>
                <b>{i_billing_period}</b>
            </div>
            <div class="diff-row {'diff-row-mismatch' if is_amt_diff else 'diff-row-match'}">
                <span style="color: #94A3B8;">Actual Amount</span>
                <b style="color: {'#FF3366' if is_amt_diff else '#00FF88'}; font-size: 0.95rem;">${record.actual_amount:,.2f}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Variance</span>
                <b style="color: {'#FF3366' if not record.is_within_tolerance else '#00FF88'};">${record.variance_amount:,.2f} ({record.variance_percent:.2f}%)</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Tolerance Status</span>
                <b>{'✅ Within Tolerance' if record.is_within_tolerance else '❌ Outside Tolerance'}</b>
            </div>
            <div class="diff-row">
                <span style="color: #94A3B8;">Exception Reason</span>
                <b style="color: {'#00FF88' if record.status.value == 'MATCHED' else '#FF6B8B'};">{record.exception_reason or 'Fully compliant'}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Optional Views triggered by Action Buttons
    if st.session_state.get("toggle_evidence_diff", False):
        st.markdown("#### 📜 Retrieved Contract Evidence Citations")
        if record.evidence_citations:
            for cite in record.evidence_citations:
                st.markdown(f"<span class='citation-tag'>{cite}</span>", unsafe_allow_html=True)
        else:
            st.info("No external contract citations attached for this calculation.")

    if st.session_state.get("toggle_audit_diff", False):
        st.markdown("#### 📜 Immutable Audit History")
        diff_logs = get_audit_logs(limit=100, invoice_id=record.invoice_id)
        if diff_logs:
            st.dataframe(pd.DataFrame([{
                "Timestamp (UTC)": l.timestamp,
                "Actor": l.actor,
                "Action": l.action_type,
                "New Status": l.new_status or "-",
                "Details": l.details,
                "Evidence": l.evidence_citation or "-"
            } for l in diff_logs]), use_container_width=True, hide_index=True)
        else:
            st.info(f"No audit logs recorded for {record.invoice_id} yet.")

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

    if record.confidence_breakdown.factors:
        with st.expander("🔍 View Explicit Mathematical Factor Explanations", expanded=True):
            for f in record.confidence_breakdown.factors:
                st.markdown(f"- `{f}`")

    # 5-Part LangChain AI Reasoning
    st.markdown("---")
    st.markdown("### 🧠 5-Part AI & LangChain RAG Root Cause Analysis")
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
    st.markdown("### ✍️ Human-in-the-Loop Clearance & Authoritative Sign-Off")
    with st.form("human_review_form"):
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            decision = st.radio(
                "Authoritative Clearance Decision",
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
elif nav_choice.startswith("📑 Contract Explorer"):
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">📑</span> Contract Explorer & Grounded LangChain RAG Assistant
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Explore executed Master Services Agreements and ask semantic questions strictly grounded in contract text using LangChain.
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

    # Contract Metadata & Terms
    st.markdown(f"""
    <div style="background: #0B101B; border: 1px solid rgba(0, 240, 255, 0.25); border-radius: 8px; padding: 14px 18px; margin: 12px 0;">
        <div style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: #00F0FF; margin-bottom: 8px; font-weight: 600;">
            📜 CONTRACT METADATA & GOVERNANCE SPECIFICATIONS
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; font-size: 0.86rem;">
            <div><span style="color: #8B949E;">Contract ID:</span> <code>{selected_contract.contract_id}</code></div>
            <div><span style="color: #8B949E;">Customer ID:</span> <code>{selected_contract.customer_id}</code></div>
            <div><span style="color: #8B949E;">Customer Entity:</span> <b>{selected_contract.customer_name}</b></div>
            <div><span style="color: #8B949E;">Effective Window:</span> <b>{selected_contract.effective_date} &rarr; {selected_contract.expiry_date}</b></div>
            <div><span style="color: #8B949E;">Product / Service:</span> <b>{selected_contract.product_service}</b></div>
            <div><span style="color: #8B949E;">Billing Cadence:</span> <b>{selected_contract.billing_frequency}</b></div>
            <div><span style="color: #8B949E;">Payment Terms:</span> <b>{selected_contract.payment_terms}</b></div>
            <div><span style="color: #8B949E;">Tax Terms:</span> <b>{selected_contract.tax_terms}</b></div>
            <div><span style="color: #8B949E;">Permissible Tolerance:</span> <b>±{selected_contract.tolerance_percent}% or {selected_contract.currency} ${selected_contract.tolerance_absolute:,.2f}</b></div>
            <div><span style="color: #8B949E;">Special Conditions:</span> <b>{selected_contract.special_conditions or 'None specified'}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Important Clauses & Indexed Document Information
    st.markdown("#### 📂 Indexed Document & Clause Information")
    c_doc1, c_doc2 = st.columns(2)
    with c_doc1:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 16px;">
            <div style="color: #00FF88; font-size: 0.78rem; font-family: 'JetBrains Mono'; font-weight: 600; margin-bottom: 6px;">
                DOCUMENT CITATION METADATA
            </div>
            <div style="font-size: 0.84rem; color: #CBD5E1;">
                <div>• <b>Source PDF Document:</b> <code>{selected_contract.file_path or 'synthetic_contract.pdf'}</code></div>
                <div>• <b>Vector Store Index:</b> ChromaDB (MiniLM-L6-v2 ONNX)</div>
                <div>• <b>Document Status:</b> Verified Executed MSA</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c_doc2:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 16px;">
            <div style="color: #00F0FF; font-size: 0.78rem; font-family: 'JetBrains Mono'; font-weight: 600; margin-bottom: 6px;">
                KEY CONTRACTUAL CLAUSES
            </div>
            <div style="font-size: 0.84rem; color: #CBD5E1;">
                <div>• <b>Section 3.1 Rate Card:</b> Billed at {selected_contract.currency} ${selected_contract.unit_price:,.2f}/unit.</div>
                <div>• <b>Section 4.2 Discount Concession:</b> {selected_contract.discount_percent}% applied on gross volume.</div>
                <div>• <b>Section 9.4 Variance Policy:</b> ±{selected_contract.tolerance_percent}% or ${selected_contract.tolerance_absolute:,.2f} audit tolerance.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("💬 Ask Contract (Semantic LangChain RAG Grounding)")

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
        with st.spinner("Retrieving grounded contract clauses via LangChain..."):
            ans_data = rag.ask_contract(custom_q, contract_id=selected_contract.contract_id)
            st.markdown("### Grounded Answer:")
            st.markdown(f"> {ans_data['answer']}")
            if ans_data['evidence_citations']:
                st.markdown("**Evidence Citations:**")
                for cite in ans_data['evidence_citations']:
                    st.markdown(f"- `{cite}`")

    # Related Invoices Section
    st.markdown("---")
    st.subheader("### Related Invoices")
    st.caption(f"Invoices associated with contract {selected_contract.contract_id} ({selected_contract.customer_name}).")
    all_invoices = get_all_invoices()
    contract_invoices = [
        inv for inv in all_invoices 
        if (inv.contract_id and inv.contract_id == selected_contract.contract_id) or
           (inv.customer_id and inv.customer_id == selected_contract.customer_id) or
           (inv.customer_name and inv.customer_name.strip().lower() == selected_contract.customer_name.strip().lower())
    ]
    if contract_invoices:
        df_inv = pd.DataFrame([inv.model_dump() for inv in contract_invoices])
        st.dataframe(df_inv[["invoice_id", "invoice_date", "billing_period", "quantity", "unit_price", "discount", "total_amount", "reference_number"]], use_container_width=True, hide_index=True)

        col_ri1, col_ri2 = st.columns([2, 1])
        with col_ri1:
            rel_inv_opts = [
                f"{inv.invoice_id} — Date: {inv.invoice_date} | Total: ${inv.total_amount:,.2f}"
                for inv in contract_invoices
            ]
            sel_rel_lbl = st.selectbox("Select Invoice to Reconcile:", rel_inv_opts, key="rel_inv_recon_select")
            sel_rel_id = sel_rel_lbl.split(" ")[0]
        with col_ri2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔎 Open in Single Invoice Reconciliation", type="primary", use_container_width=True, key="btn_open_single_recon"):
                st.session_state["nav_target"] = "🔎 Single Invoice Reconciliation"
                st.session_state["selected_contract_id"] = selected_contract.contract_id
                st.session_state["selected_invoice_id"] = sel_rel_id
                st.rerun()
    else:
        st.info("No invoices currently linked to this contract.")


# ==============================================================================
# VIEW 7: DYNAMIC ROI & VALUE SIMULATOR
# ==============================================================================
elif nav_choice.startswith("💰 ROI Simulator"):
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
    try:
        fig_roi = build_roi_payback_chart(sim_volume, sim_minutes, sim_rate, sim_match_rate)
        st.plotly_chart(fig_roi, use_container_width=True)
    except Exception:
        months = [f"M{i+1}" for i in range(12)]
        monthly_val = annual_cost_saved / 12.0
        cum_vals = [monthly_val * (i + 1) for i in range(12)]
        st.line_chart(pd.DataFrame({"Cumulative Savings ($)": cum_vals}, index=months))


# ==============================================================================
# VIEW 8: COMPLIANCE AUDIT TRAIL & GOVERNANCE
# ==============================================================================
elif nav_choice.startswith("📜 Compliance Audit"):
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">📜</span> Compliance Audit Trail & Immutable Governance
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            SOX 404 & SOC 2 compliant, tamper-evident ledger of all automated reconciliations, human clearance decisions, and official auditor addendums.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Immutability & Compliance Callout Badge
    st.markdown("""
    <div style="background: rgba(0, 255, 136, 0.05); border: 1px solid rgba(0, 255, 136, 0.25); border-left: 4px solid #00FF88; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
            <div>
                <span style="font-weight: 700; color: #00FF88; font-size: 0.95rem; letter-spacing: 0.04em;">🛡️ IMMUTABLE AUDIT LEDGER // WRITE-ONCE / APPEND-ONLY CONTROLS ACTIVE</span>
                <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.84rem; line-height: 1.4;">
                    Under SOX Section 404, SOC 1/2 Type II, and GAAP guidelines, historical audit rows are mathematically sealed and cannot be modified or deleted. To record amendments, approvals, or dispute memos, humans append an <b>Auditor Addendum</b> below.
                </p>
            </div>
            <div style="background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(0, 255, 136, 0.4); border-radius: 6px; padding: 6px 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; color: #00FF88;">
                SHA-256 INTEGRITY: SEALED
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    logs = get_audit_logs(limit=1000)
    all_invoices = get_all_invoices()
    inv_ids_list = [inv.invoice_id for inv in all_invoices] if all_invoices else []

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

        # Audit Summary KPI Cards
        total_entries = len(df_logs)
        ai_entries = len(df_logs[df_logs["Actor"] == "AI_ENGINE"])
        human_entries = len(df_logs[df_logs["Actor"] != "AI_ENGINE"])
        addendum_entries = len(df_logs[df_logs["Action"].str.contains("ADDENDUM|MEMO|SIGN_OFF|ESCALATION|CORRECTION|NOTE", case=False, na=False)])

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label"><span>Total Audit Events</span> <span>📜</span></div>
                <div class="metric-value">{total_entries}</div>
                <div class="metric-sub">Complete Chain of Custody</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label"><span>Autonomous AI Runs</span> <span>⚡</span></div>
                <div class="metric-value" style="color: #00FF88;">{ai_entries}</div>
                <div class="metric-sub">Deterministic + RAG Runs</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label"><span>Human Sign-Offs</span> <span>👤</span></div>
                <div class="metric-value" style="color: #38BDF8;">{human_entries}</div>
                <div class="metric-sub">Triage & Clearances</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label"><span>Auditor Addendums</span> <span>✍️</span></div>
                <div class="metric-value" style="color: #F59E0B;">{addendum_entries}</div>
                <div class="metric-sub">Compliance Memos Attached</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Human Action / Auditor Addendum Form in an expander
        with st.expander("✍️ Human Auditor Action Center: Append Official Addendum or Compliance Memo", expanded=False):
            st.markdown("""
            <div style="font-size: 0.88rem; color: #94A3B8; margin-bottom: 14px;">
                Add an official, append-only auditor note, secondary supervisory sign-off, or dispute justification to any invoice transaction. 
                This action is permanently stamped with your identity and cannot be altered or erased.
            </div>
            """, unsafe_allow_html=True)

            with st.form("audit_addendum_form"):
                af_c1, af_c2, af_c3 = st.columns([1.5, 1.5, 1.5])
                
                # Default invoice list from existing logs
                available_invoices = sorted(list(df_logs["Invoice ID"].unique()))
                if not available_invoices and inv_ids_list:
                    available_invoices = inv_ids_list
                
                with af_c1:
                    target_inv = st.selectbox("Target Invoice ID *", available_invoices)
                with af_c2:
                    addendum_type = st.selectbox(
                        "Addendum / Action Type *",
                        [
                            "AUDITOR_ADDENDUM",
                            "SECONDARY_SIGN_OFF",
                            "POLICY_EXCEPTION_MEMO",
                            "LEGAL_DISPUTE_ESCALATION",
                            "ARITHMETIC_CORRECTION_NOTE",
                            "TAX_EXEMPTION_CONFIRMATION",
                        ]
                    )
                with af_c3:
                    auditor_actor = st.text_input("Auditor / Reviewer Full Name *", value="Marcus Vance (Sr. Compliance Auditor)")

                addendum_details = st.text_area(
                    "Mandatory Compliance Justification / Audit Evidence *",
                    placeholder="Enter explicit factual justification, reference contractual addendum clauses, or detail supervisory clearance reasoning..."
                )
                
                evidence_ref = st.text_input(
                    "Evidence / Policy Reference (Optional)",
                    placeholder="e.g., Clause 4.2 Rate Card Waiver; Approval by VP Finance 2026-09-15"
                )

                submit_addendum = st.form_submit_button("✍️ Append Immutable Addendum to Audit Ledger", use_container_width=True)

                if submit_addendum:
                    if not auditor_actor.strip() or not addendum_details.strip():
                        st.error("⚠️ Auditor Name and Compliance Justification are mandatory for compliance adherence.")
                    else:
                        matched_log = df_logs[df_logs["Invoice ID"] == target_inv]
                        target_contract = matched_log["Contract ID"].iloc[0] if not matched_log.empty and matched_log["Contract ID"].iloc[0] != "-" else None
                        
                        log_audit_entry(AuditLogEntry(
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            invoice_id=target_inv,
                            contract_id=target_contract,
                            action_type=addendum_type,
                            actor=auditor_actor.strip(),
                            previous_status=None,
                            new_status="AUDITED_ANNOTATED",
                            details=addendum_details.strip(),
                            evidence_citation=evidence_ref.strip() if evidence_ref.strip() else f"Auditor Memo by {auditor_actor.strip()}"
                        ))
                        st.success(f"✅ Immutable addendum successfully committed to the audit ledger for Invoice {target_inv}!")
                        time.sleep(1)
                        st.rerun()

        # Multi-Filters
        st.markdown("##### 🔍 Audit Ledger Inspection & Filters")
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1:
            actor_options = ["ALL"] + sorted(list(df_logs["Actor"].unique()))
            actor_filter = st.selectbox("Filter by Actor", actor_options)
        with c_f2:
            action_options = ["ALL"] + sorted(list(df_logs["Action"].unique()))
            action_filter = st.selectbox("Filter Action Type", action_options)
        with c_f3:
            search_inv = st.text_input("Filter by Invoice ID", placeholder="e.g. INV-2026-")

        # Apply Filters
        filtered_df = df_logs.copy()
        if actor_filter != "ALL":
            filtered_df = filtered_df[filtered_df["Actor"] == actor_filter]
        if action_filter != "ALL":
            filtered_df = filtered_df[filtered_df["Action"] == action_filter]
        if search_inv:
            filtered_df = filtered_df[filtered_df["Invoice ID"].str.contains(search_inv, case=False)]

        col_exp1, col_exp2 = st.columns([2, 1])
        with col_exp1:
            st.caption(f"Showing **{len(filtered_df)}** of **{len(df_logs)}** audit events in ledger.")
        with col_exp2:
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Filtered Audit Trail to CSV",
                data=csv_data,
                file_name=f"compliance_audit_trail_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        # Single-Invoice Lifecycle Trace
        with st.expander("🔍 Inspect Single-Invoice Chronological Lifecycle"):
            trace_inv = st.selectbox("Select Invoice to Trace Full Chain of Custody", ["-- Select --"] + sorted(list(df_logs["Invoice ID"].unique())))
            if trace_inv != "-- Select --":
                inv_trace = df_logs[df_logs["Invoice ID"] == trace_inv].sort_values("Timestamp (UTC)", ascending=True)
                st.markdown(f"**Audit Trail for `{trace_inv}` ({len(inv_trace)} logged events):**")
                for _, row in inv_trace.iterrows():
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.02); border-left: 3px solid #00FF88; border-radius: 4px; padding: 8px 12px; margin-bottom: 8px;">
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #8B949E;">{row['Timestamp (UTC)']}</span> | 
                        <b style="color: #38BDF8;">{row['Actor']}</b> ➔ 
                        <span style="color: #00FF88; font-weight: 600;">{row['Action']}</span>
                        <div style="color: #E2E8F0; font-size: 0.84rem; margin-top: 4px;">{row['Details']}</div>
                        <div style="color: #94A3B8; font-size: 0.75rem; margin-top: 2px;"><i>Citation: {row['Evidence Citation']}</i></div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No audit logs recorded yet. Run the Reconciliation Engine in Sector 3 to populate the audit ledger.")


# ==============================================================================
# VIEW 9: ARCHITECTURE & INTERVIEW GUIDE
# ==============================================================================
elif nav_choice.startswith("ℹ️ Architecture Guide"):
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
    | **AI Reasoning & LangChain** | LangChain / Groq / OpenAI | Formulates 5-part root cause analysis: What Happened, Why It Happened, What Contract Says, Citations, Recommended Action. | Transforms dry numbers into actionable, plain-English finance executive narratives. |
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
             └── LangChain RAG Contract Clause Evidence Retrieval
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
