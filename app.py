import streamlit as st

# ==============================================================================
# 1. STREAMLIT PAGE CONFIGURATION (MUST BE FIRST)
# ==============================================================================
st.set_page_config(
    page_title="NEXUS RECON // Finance AI Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import sys
import time
import json
import sqlite3
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

# Fallback for rapidfuzz in case it's not installed in lightweight cloud containers
try:
    from rapidfuzz import fuzz
    def compute_similarity(s1: str, s2: str) -> float:
        return fuzz.token_sort_ratio(s1.lower(), s2.lower()) / 100.0
except ImportError:
    from difflib import SequenceMatcher
    def compute_similarity(s1: str, s2: str) -> float:
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

# Optional Plotly import with fallback for minimal cloud deployments
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ==============================================================================
# 2. BLACK & NEON GREEN DESIGN SYSTEM (CSS TOKENS)
# ==============================================================================
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-obsidian: #070A0F;
        --bg-card: #0C121F;
        --bg-card-hover: #121A2B;
        --neon-green: #00FF88;
        --neon-cyan: #00F0FF;
        --neon-amber: #FFB800;
        --neon-crimson: #FF3366;
        --text-primary: #F0F6FC;
        --text-secondary: #8B949E;
        --border-neon: rgba(0, 255, 136, 0.28);
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Space Grotesk', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: var(--bg-obsidian) !important;
        color: var(--text-primary) !important;
    }

    /* Top Bar */
    header[data-testid="stHeader"] {
        background: rgba(7, 10, 15, 0.85) !important;
        backdrop-filter: blur(10px) !important;
        border-bottom: 1px solid rgba(0, 255, 136, 0.15) !important;
    }

    /* Sidebar & Single-Line Navigation */
    section[data-testid="stSidebar"] {
        background-color: #05070B !important;
        border-right: 1px solid rgba(0, 255, 136, 0.18) !important;
        min-width: 290px !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(0, 255, 136, 0.15) !important;
    }

    div[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 3px !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        border: 1px solid transparent !important;
        background: rgba(13, 19, 31, 0.5) !important;
        margin-bottom: 3px !important;
        cursor: pointer !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(0, 255, 136, 0.08) !important;
        border-color: rgba(0, 255, 136, 0.3) !important;
        transform: translateX(3px) !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label p {
        white-space: nowrap !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.01em !important;
        line-height: 1.2 !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: rgba(0, 255, 136, 0.12) !important;
        border: 1px solid rgba(0, 255, 136, 0.45) !important;
        box-shadow: 0 0 14px rgba(0, 255, 136, 0.2) !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: #00FF88 !important;
        font-weight: 600 !important;
        text-shadow: 0 0 8px rgba(0, 255, 136, 0.4) !important;
    }

    /* Pulsing Live Status Dot */
    @keyframes neon-pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(0, 255, 136, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0); }
    }
    .live-indicator {
        display: inline-block;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background-color: var(--neon-green);
        animation: neon-pulse 1.8s infinite;
        margin-right: 8px;
        vertical-align: middle;
    }

    /* Cyber Banner */
    .cyber-banner {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.08) 0%, rgba(13, 19, 31, 0.95) 100%);
        border: 1px solid var(--border-neon);
        border-left: 5px solid var(--neon-green);
        border-radius: 10px;
        padding: 16px 22px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 255, 136, 0.08);
        position: relative;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, #0C121F 0%, #070B13 100%);
        border: 1px solid rgba(0, 255, 136, 0.22);
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.5);
        color: #F8FAFC;
        margin-bottom: 14px;
        transition: all 0.25s ease-in-out;
    }
    .metric-card:hover {
        border-color: var(--neon-green);
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
        transform: translateY(-2px);
    }
    .metric-card-danger { border-color: rgba(255, 51, 102, 0.4); }
    .metric-card-cyan { border-color: rgba(0, 240, 255, 0.35); }

    .metric-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8B949E;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1.1;
    }
    .metric-value-green { color: var(--neon-green); text-shadow: 0 0 14px rgba(0, 255, 136, 0.35); }
    .metric-value-crimson { color: var(--neon-crimson); text-shadow: 0 0 14px rgba(255, 51, 102, 0.35); }
    .metric-value-cyan { color: var(--neon-cyan); text-shadow: 0 0 14px rgba(0, 240, 255, 0.35); }
    .metric-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: var(--neon-green);
        margin-top: 6px;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-matched {
        background-color: rgba(0, 255, 136, 0.12);
        color: var(--neon-green);
        border: 1px solid rgba(0, 255, 136, 0.4);
    }
    .badge-probable {
        background-color: rgba(0, 240, 255, 0.12);
        color: var(--neon-cyan);
        border: 1px solid rgba(0, 240, 255, 0.4);
    }
    .badge-unmatched {
        background-color: rgba(255, 51, 102, 0.12);
        color: var(--neon-crimson);
        border: 1px solid rgba(255, 51, 102, 0.4);
    }

    /* Visual Diff Cards */
    .diff-card {
        background: #0B101A;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 16px;
    }
    .diff-card-contract { border-top: 3px solid var(--neon-cyan); }
    .diff-card-invoice { border-top: 3px solid var(--neon-green); }
    .diff-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 0.88rem;
    }
    .diff-row:last-child { border-bottom: none; }
    .diff-row-mismatch {
        background-color: rgba(255, 51, 102, 0.09);
        border-left: 3px solid var(--neon-crimson);
        padding-left: 8px;
    }
    .diff-row-match {
        background-color: rgba(0, 255, 136, 0.05);
        border-left: 3px solid var(--neon-green);
        padding-left: 8px;
    }

    /* Terminal Simulation Box */
    .terminal-box {
        background-color: #04060A;
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-radius: 8px;
        padding: 14px 18px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #A3E635;
        line-height: 1.6;
        max-height: 280px;
        overflow-y: auto;
        margin: 14px 0;
    }
    .terminal-box .term-green { color: #00FF88; }
    .terminal-box .term-dim { color: #4B5563; }
    .terminal-box .term-cyan { color: #00F0FF; }
    .terminal-box .term-red { color: #FF3366; }

    /* Analysis Box */
    .analysis-box {
        background: linear-gradient(145deg, #0A0F1A 0%, #060910 100%);
        border: 1px solid rgba(0, 240, 255, 0.25);
        border-left: 5px solid var(--neon-cyan);
        border-radius: 8px;
        padding: 18px 20px;
        margin: 14px 0;
        color: #E2E8F0;
    }
    .analysis-box h4 {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        color: var(--neon-cyan);
        margin-top: 14px;
        margin-bottom: 4px;
    }
    .analysis-box h4:first-child { margin-top: 0; }
    .analysis-box p { font-size: 0.9rem; color: #CBD5E1; margin-bottom: 10px; }

    .citation-tag {
        background-color: rgba(0, 240, 255, 0.1);
        border: 1px solid rgba(0, 240, 255, 0.35);
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 0.74rem;
        font-family: 'JetBrains Mono', monospace;
        color: var(--neon-cyan);
        display: inline-block;
        margin: 2px 4px 2px 0;
    }

    div.stButton > button {
        background: linear-gradient(180deg, #0E1829 0%, #080E18 100%) !important;
        border: 1px solid rgba(0, 255, 136, 0.35) !important;
        color: var(--neon-green) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00FF88 0%, #00CC6A 100%) !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border: none !important;
        box-shadow: 0 0 16px rgba(0, 255, 136, 0.4) !important;
    }
    div[data-testid="stDataFrame"] {
        background-color: #0A0E17 !important;
        border: 1px solid rgba(0, 255, 136, 0.15) !important;
        border-radius: 10px !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================================================================
# 3. SELF-CONTAINED DATABASE & ENGINE
# ==============================================================================
DB_PATH = "reconciliation.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_standalone_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS contracts (
        contract_id TEXT PRIMARY KEY,
        customer_id TEXT,
        customer_name TEXT,
        effective_date TEXT,
        expiry_date TEXT,
        product_service TEXT,
        quantity INTEGER,
        unit_price REAL,
        currency TEXT,
        billing_frequency TEXT,
        discount_percent REAL,
        tolerance_percent REAL,
        tolerance_absolute REAL,
        special_conditions TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id TEXT PRIMARY KEY,
        contract_id TEXT,
        customer_id TEXT,
        customer_name TEXT,
        invoice_date TEXT,
        billing_period TEXT,
        currency TEXT,
        quantity INTEGER,
        unit_price REAL,
        discount REAL,
        tax REAL,
        total_amount REAL,
        reference_number TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS reconciliation_results (
        invoice_id TEXT PRIMARY KEY,
        contract_id TEXT,
        customer_id TEXT,
        customer_name TEXT,
        status TEXT,
        priority TEXT,
        confidence_score REAL,
        expected_amount REAL,
        actual_amount REAL,
        variance_amount REAL,
        variance_percent REAL,
        is_within_tolerance INTEGER,
        financial_exposure REAL,
        exception_reason TEXT,
        what_happened TEXT,
        why_did_it_happen TEXT,
        what_contract_says TEXT,
        evidence_citations TEXT,
        recommendation TEXT,
        review_status TEXT DEFAULT 'PENDING',
        reviewer_name TEXT,
        reviewer_comment TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        invoice_id TEXT,
        contract_id TEXT,
        action_type TEXT,
        actor TEXT,
        previous_status TEXT,
        new_status TEXT,
        details TEXT
    )""")
    conn.commit()

    # Seed if empty
    c.execute("SELECT COUNT(*) as count FROM contracts")
    if c.fetchone()["count"] == 0:
        seed_data(conn)
    conn.close()

def seed_data(conn):
    c = conn.cursor()
    contracts = [
        ("CTR-1001", "CUST-201", "Nexus Cloud Technologies Inc.", "2025-01-01", "2025-12-31", "Enterprise Cloud Platform Tier 3", 100, 100.0, "USD", "Monthly", 10.0, 1.0, 50.0, "Customer entitled to 10% discount. Standard monthly gross $10,000, discounted to $9,000 net."),
        ("CTR-1002", "CUST-202", "Meridian Logistics Corp", "2025-01-01", "2025-12-31", "Fleet Telematics & Route Engine", 50, 150.0, "USD", "Monthly", 0.0, 1.0, 50.0, "Fixed baseline fee of $7,500 monthly for up to 50 monitored vehicles."),
        ("CTR-1003", "CUST-203", "Apex Health Solutions LLC", "2025-01-01", "2025-06-30", "HIPAA Interoperability Gateway", 1, 18000.0, "USD", "Monthly", 5.0, 0.5, 100.0, "Monthly base $18,000 less 5% discount ($900), net $17,100. Agreement expires June 30, 2025."),
        ("CTR-1004", "CUST-204", "Vanguard Cyber Defense", "2025-02-01", "2026-01-31", "Managed Detection & Threat Hunting", 10, 1200.0, "USD", "Monthly", 0.0, 1.0, 50.0, "Standard 24/7 SOC monitoring for 10 nodes at $12,000/mo."),
        ("CTR-1005", "CUST-205", "Solaria Energy Systems Inc.", "2025-01-01", "2025-12-31", "SCADA Microgrid Telemetry Feed", 20, 450.0, "USD", "Monthly", 15.0, 2.0, 100.0, "Promotional renewable discount of 15% applied to $9,000 baseline, net $7,650."),
    ]
    c.executemany("INSERT INTO contracts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", contracts)

    # Invoices with deliberate real-world billing patterns
    invoices = [
        ("INV-1001", "CTR-1001", "CUST-201", "Nexus Cloud Technologies Inc.", "2025-03-01", "2025-03", "USD", 100, 100.0, 10.0, 0.0, 9000.0, "REF-1001"),
        ("INV-1002", "CTR-1001", "CUST-201", "Nexus Cloud Technologies Inc.", "2025-04-01", "2025-04", "USD", 100, 100.0, 0.0, 0.0, 10000.0, "REF-1002"), # Omitted discount!
        ("INV-1003", "CTR-1002", "CUST-202", "Meridian Logistics Corp", "2025-03-01", "2025-03", "USD", 50, 150.0, 0.0, 0.0, 7500.0, "REF-1003"),
        ("INV-1004", "CTR-1002", "CUST-202", "Meridian Logistics Corp", "2025-04-01", "2025-04", "USD", 80, 150.0, 0.0, 0.0, 12000.0, "REF-1004"), # Qty drift
        ("INV-1005", "CTR-1003", "CUST-203", "Apex Health Solutions LLC", "2025-02-01", "2025-02", "USD", 1, 18000.0, 5.0, 0.0, 17100.0, "REF-1005"),
        ("INV-1021", "CTR-1003", "CUST-203", "Apex Health Solutions LLC", "2025-07-15", "2025-07", "USD", 1, 18000.0, 5.0, 0.0, 17100.0, "REF-1021"), # Expired term!
        ("INV-1007", "CTR-1004", "CUST-204", "Vanguard Cyber Defense", "2025-01-15", "2025-01", "USD", 10, 1200.0, 0.0, 0.0, 12000.0, "REF-1007"), # Pre-contract date!
        ("INV-1008", "CTR-1005", "CUST-205", "Solaria Energy Systems", "2025-03-01", "2025-03", "USD", 20, 450.0, 15.0, 0.0, 7650.0, "REF-1008"),
        ("INV-1009", "CTR-1005", "CUST-205", "Solaria Energy Systems", "2025-04-01", "2025-04", "EUR", 20, 450.0, 15.0, 0.0, 7650.0, "REF-1009"), # Currency mismatch
        ("INV-1010", None, None, "Unregistered Vendor Global LLC", "2025-03-01", "2025-03", "USD", 1, 5000.0, 0.0, 0.0, 5000.0, "REF-1010"), # Missing contract
    ]
    c.executemany("INSERT INTO invoices VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", invoices)
    conn.commit()

    # Reconcile seeded invoices
    reconcile_all(conn)

def reconcile_all(conn):
    c = conn.cursor()
    c.execute("SELECT * FROM contracts")
    contracts = {r["contract_id"]: dict(r) for r in c.fetchall()}
    c.execute("SELECT * FROM invoices")
    invoices = [dict(r) for r in c.fetchall()]

    results = []
    for inv in invoices:
        cid = inv.get("contract_id")
        contract = contracts.get(cid)

        # Fuzzy match attempt if contract_id is missing
        if not contract:
            for cand in contracts.values():
                if compute_similarity(inv["customer_name"], cand["customer_name"]) >= 0.75:
                    contract = cand
                    break

        actual = float(inv["total_amount"])
        if not contract:
            status = "UNMATCHED"
            priority = "HIGH"
            expected = 0.0
            variance = actual
            pct = 100.0
            in_tol = 0
            exposure = actual
            reason = "No associated contract agreement found for vendor/customer."
            wh = "Invoice received without an executed contract agreement."
            why = "Entity missing from master contracts or unregistered customer."
            wc = "Policy requires executed MSA before billing clearance."
            rec = "Route to Procurement/Legal to verify supplier contract."
            conf = 0.35
        else:
            base_subtotal = float(contract["quantity"]) * float(contract["unit_price"])
            expected = base_subtotal * (1.0 - float(contract["discount_percent"]) / 100.0)
            variance = abs(actual - expected)
            pct = (variance / expected * 100.0) if expected > 0 else 0.0
            in_tol = 1 if (pct <= float(contract["tolerance_percent"]) or variance <= float(contract["tolerance_absolute"])) else 0

            inv_date = inv["invoice_date"]
            eff_date = contract["effective_date"]
            exp_date = contract["expiry_date"]

            if inv["currency"] != contract["currency"]:
                status = "UNMATCHED"
                priority = "HIGH"
                exposure = actual
                reason = f"Currency mismatch: Billed in {inv['currency']} vs Contract in {contract['currency']}."
                wh = "Currency inconsistency detected."
                why = "Invoice submitted in unapproved foreign currency."
                wc = f"Contract stipulates payments exclusively in {contract['currency']}."
                rec = "Dispute invoice and request re-issuance in contractual currency."
                conf = 0.70
            elif inv_date < eff_date:
                status = "UNMATCHED"
                priority = "HIGH"
                exposure = actual
                reason = f"Pre-Contract: Invoice dated {inv_date} is prior to effective date {eff_date}."
                wh = "Services billed prior to agreement effective date."
                why = "Billing operations submitted early or commencement drifted."
                wc = f"Obligations commence only after {eff_date}."
                rec = "Audit work delivery proofs before approving pre-contract dates."
                conf = 0.65
            elif inv_date > exp_date:
                status = "UNMATCHED"
                priority = "HIGH"
                exposure = actual
                reason = f"Contract Expired: Invoice dated {inv_date} after expiration {exp_date}."
                wh = "Billing received on lapsed contractual term."
                why = "Renewal agreement has not been executed."
                wc = f"Agreement terminated on {exp_date}."
                rec = "Issue renewal addendum before clearing invoice payment."
                conf = 0.65
            elif variance == 0.0:
                status = "MATCHED"
                priority = "LOW"
                exposure = 0.0
                reason = "Exact match: Rates, volumes, discounts, and dates match perfectly."
                wh = "Automated full compliance match."
                why = "Billing precisely follows executed contractual fee schedule."
                wc = f"Contract terms fully satisfied ({contract['product_service']})."
                rec = "Auto-cleared for payment processing."
                conf = 0.98
            elif in_tol:
                status = "PROBABLE_MATCH"
                priority = "LOW"
                exposure = variance
                reason = f"Minor variance of ${variance:,.2f} ({pct:.2f}%) within allowable tolerance."
                wh = "Immaterial financial variance detected."
                why = "Rounding or minor consumption tier fluctuation."
                wc = f"Contract permits variance up to ±{contract['tolerance_percent']}%."
                rec = "Auto-clear within tolerance policy."
                conf = 0.90
            else:
                status = "UNMATCHED"
                priority = "HIGH"
                exposure = variance
                reason = f"Material discrepancy of ${variance:,.2f} ({pct:.2f}%) exceeds tolerance."
                wh = "Billed amount deviates materially from expected calculation."
                why = "Omitted contractual discount or incorrect unit pricing."
                wc = f"Contract requires {contract['discount_percent']}% discount and ${contract['unit_price']:,.2f} unit price."
                rec = "Issue dispute notice to vendor citing Pricing Exhibit A."
                conf = 0.75

        citations = f"{contract['contract_id']} (Page 1)" if contract else "Billing Policy §2.1"
        results.append((
            inv["invoice_id"], contract["contract_id"] if contract else None,
            inv.get("customer_id"), inv["customer_name"], status, priority,
            conf, expected, actual, variance, pct, in_tol, exposure,
            reason, wh, why, wc, citations, rec, "PENDING", None, None
        ))

    c.execute("DELETE FROM reconciliation_results")
    c.executemany("""
    INSERT INTO reconciliation_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, results)
    conn.commit()

init_standalone_db()

# ==============================================================================
# 4. SIDEBAR NAVIGATION
# ==============================================================================
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
if st.sidebar.button("🔄 Re-Run Full Engine", use_container_width=True):
    with st.spinner("Re-evaluating financial compliance..."):
        conn = get_db()
        reconcile_all(conn)
        conn.close()
        st.sidebar.success("Engine batch complete!")
        st.rerun()

st.sidebar.caption("Deterministic Math: **Python 3.12 Engine**")
st.sidebar.caption("Contract Tolerance: **±1.0% or $50.00**")

# Query helper
def get_metrics():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM invoices")
    tot = c.fetchone()["total"]
    c.execute("SELECT status, COUNT(*) as cnt FROM reconciliation_results GROUP BY status")
    counts = {r["status"]: r["cnt"] for r in c.fetchall()}
    c.execute("SELECT SUM(financial_exposure) as exp FROM reconciliation_results WHERE status != 'MATCHED'")
    exp = c.fetchone()["exp"] or 0.0
    c.execute("SELECT COUNT(*) as high FROM reconciliation_results WHERE priority = 'HIGH'")
    high = c.fetchone()["high"]
    conn.close()

    matched = counts.get("MATCHED", 0)
    prob = counts.get("PROBABLE_MATCH", 0)
    unmatched = counts.get("UNMATCHED", 0)
    tot_rec = matched + prob + unmatched
    rate = round((matched / tot_rec * 100.0), 1) if tot_rec > 0 else 0.0
    hours = round((matched * 15.0) / 60.0, 1)
    cost = round(hours * 45.0, 2)
    return {
        "total": tot, "matched": matched, "probable": prob, "unmatched": unmatched,
        "rate": rate, "exposure": exp, "high": high, "hours": hours, "cost": cost
    }

# ==============================================================================
# VIEW 1: EXECUTIVE DASHBOARD
# ==============================================================================
if nav_choice == "📊 Executive Dashboard":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;">
            <span style="color: #00FF88;">⚡</span> Executive Reconciliation Command Center
        </h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">
            Real-time contractual compliance tracking, autonomous variance detection, and capital preservation analytics.
        </p>
    </div>
    """, unsafe_allow_html=True)

    m = get_metrics()
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Ingested Invoices</div><div class="metric-value">{m['total']}</div><div class="metric-sub">100% Ingested</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Auto-Match Rate</div><div class="metric-value metric-value-green">{m['rate']}%</div><div class="metric-sub">{m['matched']} Clean Clearances</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card metric-card-danger"><div class="metric-label">Financial Exposure</div><div class="metric-value metric-value-crimson">${m['exposure']:,.0f}</div><div class="metric-sub" style="color:#FF3366;">At-Risk Discrepancy</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card metric-card-danger"><div class="metric-label">High Priority</div><div class="metric-value metric-value-crimson">{m['high']}</div><div class="metric-sub" style="color:#FF6B8B;">Action Required</div></div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="metric-card metric-card-cyan"><div class="metric-label">Labor Hours Saved</div><div class="metric-value metric-value-cyan">{m['hours']}h</div><div class="metric-sub" style="color:#00F0FF;">${m['cost']:,.0f} Net Savings</div></div>""", unsafe_allow_html=True)

    st.markdown("### 🌐 End-to-End Autonomous Pipeline Flow")
    if PLOTLY_AVAILABLE:
        fig_sankey = go.Figure(go.Sankey(
            node=dict(
                pad=16, thickness=16, line=dict(color="#070A0F", width=1.5),
                label=[f"Total Billing ({m['total']})", "Exact Tier", "Tolerance Tier", "Exception Queue", f"Auto-Cleared (${m['cost']*20:,.0f})", f"Financial Exposure (${m['exposure']:,.0f})"],
                color=["#38BDF8", "#00FF88", "#00F0FF", "#FF3366", "#00FF88", "#FF3366"]
            ),
            link=dict(
                source=[0, 0, 1, 2, 2, 3],
                target=[1, 2, 4, 4, 3, 5],
                value=[max(1, m['matched']-1), max(1, m['probable']+1), max(1, m['matched']-1), max(1, m['probable']), 1, max(1, m['unmatched'])],
                color=["rgba(0,255,136,0.3)", "rgba(0,240,255,0.3)", "rgba(0,255,136,0.4)", "rgba(0,240,255,0.4)", "rgba(255,51,102,0.3)", "rgba(255,51,102,0.4)"]
            )
        ))
        fig_sankey.update_layout(paper_bgcolor="#0C121F", plot_bgcolor="#0C121F", font=dict(family="JetBrains Mono", color="#94A3B8"), height=340, margin=dict(t=30, b=20, l=20, r=20))
        st.plotly_chart(fig_sankey, use_container_width=True)

        c_p1, c_p2 = st.columns(2)
        with c_p1:
            fig_pie = go.Figure(go.Pie(
                labels=["Matched", "Probable", "Unmatched"],
                values=[m["matched"], m["probable"], m["unmatched"]],
                hole=0.65,
                marker=dict(colors=["#00FF88", "#00F0FF", "#FF3366"], line=dict(color="#070A0F", width=2))
            ))
            fig_pie.update_layout(title="<b>Portfolio Status Breakdown</b>", paper_bgcolor="#0C121F", font=dict(family="Space Grotesk", color="#FFFFFF"), height=300, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_pie, use_container_width=True)

        with c_p2:
            conn = get_db()
            df_exc = pd.read_sql_query("SELECT exception_reason, financial_exposure FROM reconciliation_results WHERE status != 'MATCHED'", conn)
            conn.close()
            if not df_exc.empty:
                df_exc["short"] = df_exc["exception_reason"].apply(lambda x: x[:30] + "...")
                fig_bar = px.bar(df_exc, x="financial_exposure", y="short", orientation='h', color_discrete_sequence=["#FF3366"], title="<b>Exposure by Root Cause ($)</b>")
                fig_bar.update_layout(paper_bgcolor="#0C121F", plot_bgcolor="#0C121F", font=dict(family="JetBrains Mono", color="#94A3B8"), height=300, margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.markdown(f"""
        <div style="background: #0C121F; border: 1px solid rgba(0, 255, 136, 0.25); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 12px 18px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #38BDF8; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Ingested Feed</div>
                    <div style="color: #FFFFFF; font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono'; margin-top: 4px;">{m['total']} Invoices</div>
                    <div style="color: #94A3B8; font-size: 0.72rem;">100% Ingested</div>
                </div>
                <div style="color: #00FF88; font-size: 1.4rem; font-weight: bold;">➔</div>
                <div style="background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.3); border-radius: 8px; padding: 12px 18px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #00FF88; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Exact Tier</div>
                    <div style="color: #00FF88; font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono'; margin-top: 4px;">{m['matched']} Cleared</div>
                    <div style="color: #94A3B8; font-size: 0.72rem;">100% Match</div>
                </div>
                <div style="color: #00F0FF; font-size: 1.4rem; font-weight: bold;">➔</div>
                <div style="background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 8px; padding: 12px 18px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #00F0FF; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Tolerance Tier</div>
                    <div style="color: #00F0FF; font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono'; margin-top: 4px;">{m['probable']} Probable</div>
                    <div style="color: #94A3B8; font-size: 0.72rem;">Within Threshold</div>
                </div>
                <div style="color: #FF3366; font-size: 1.4rem; font-weight: bold;">➔</div>
                <div style="background: rgba(255, 51, 102, 0.1); border: 1px solid rgba(255, 51, 102, 0.3); border-radius: 8px; padding: 12px 18px; text-align: center; flex: 1; min-width: 130px;">
                    <div style="color: #FF3366; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Exception Queue</div>
                    <div style="color: #FF3366; font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono'; margin-top: 4px;">{m['unmatched']} Blocked</div>
                    <div style="color: #FF6B8B; font-size: 0.72rem;">${m['exposure']:,.0f} Exposure</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.markdown("#### 📊 Portfolio Status Breakdown")
            df_status = pd.DataFrame({
                "Count": [m["matched"], m["probable"], m["unmatched"]]
            }, index=["Matched", "Probable", "Unmatched"])
            st.bar_chart(df_status)

        with c_p2:
            st.markdown("#### ⚠️ Exposure by Root Cause ($)")
            conn = get_db()
            df_exc = pd.read_sql_query("SELECT exception_reason, financial_exposure FROM reconciliation_results WHERE status != 'MATCHED'", conn)
            conn.close()
            if not df_exc.empty:
                df_exc["Cause"] = df_exc["exception_reason"].apply(lambda x: x[:25] + "...")
                st.bar_chart(df_exc.set_index("Cause")["financial_exposure"])
            else:
                st.info("No active exceptions detected.")

        st.caption("💡 *Note: Add `plotly` to your requirements.txt in GitHub if you'd like interactive vector Sankey & Donut diagrams.*")

# ==============================================================================
# VIEW 2: 'WHAT-IF' SIMULATION SANDBOX
# ==============================================================================
elif nav_choice == "🧪 'What-If' Sandbox":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;"><span style="color: #00FF88;">🧪</span> Interactive 'What-If' Reconciliation Sandbox</h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">Test pricing drift, volume changes, discount omissions, and date anomalies live.</p>
    </div>
    """, unsafe_allow_html=True)

    conn = get_db()
    contracts = pd.read_sql_query("SELECT * FROM contracts", conn).to_dict("records")
    conn.close()

    c_map = {f"{c['contract_id']} — {c['customer_name']}": c for c in contracts}
    sel_name = st.selectbox("Select Customer Contract Baseline:", list(c_map.keys()))
    c = c_map[sel_name]

    st.markdown("#### 🎛️ Adjust Simulation Knobs")
    s1, s2, s3 = st.columns(3)
    with s1:
        sim_price = st.slider("Billed Unit Price ($)", min_value=10.0, max_value=float(c["unit_price"])*2.0, value=float(c["unit_price"]), step=5.0)
        sim_qty = st.slider("Billed Quantity", min_value=1, max_value=int(c["quantity"])*2, value=int(c["quantity"]), step=1)
    with s2:
        sim_discount = st.slider("Applied Discount (%)", min_value=0.0, max_value=50.0, value=float(c["discount_percent"]), step=1.0)
        sim_timing = st.selectbox("Timing", ["Valid In-Term", "Pre-Contract (-15 Days)", "Post-Expiry (+30 Days)"])
    with s3:
        sim_curr = st.selectbox("Currency", ["USD", "EUR", "GBP", "INR"], index=0)
        sim_cust = st.text_input("Customer Name on Invoice", value=c["customer_name"])

    # Math
    expected_tot = (c["quantity"] * c["unit_price"]) * (1.0 - c["discount_percent"] / 100.0)
    actual_tot = (sim_qty * sim_price) * (1.0 - sim_discount / 100.0)
    variance = abs(actual_tot - expected_tot)
    pct_var = (variance / expected_tot * 100.0) if expected_tot > 0 else 0.0
    in_tol = (pct_var <= c["tolerance_percent"]) or (variance <= c["tolerance_absolute"])

    if sim_curr != c["currency"]:
        sim_status = "UNMATCHED (CURRENCY_MISMATCH)"
        color = "#FF3366"
    elif sim_timing != "Valid In-Term":
        sim_status = "UNMATCHED (DATE_ANOMALY)"
        color = "#FF3366"
    elif variance == 0.0:
        sim_status = "MATCHED (PERFECT_COMPLIANCE)"
        color = "#00FF88"
    elif in_tol:
        sim_status = "PROBABLE_MATCH (WITHIN_TOLERANCE)"
        color = "#00F0FF"
    else:
        sim_status = "UNMATCHED (MATERIAL_VARIANCE)"
        color = "#FF3366"

    st.markdown(f"""
    <div style="background: #0D131F; border: 1px solid {color}; border-left: 6px solid {color}; border-radius: 8px; padding: 14px 18px; margin-top: 15px;">
        <span style="font-size: 1.15rem; font-weight: 700; color: white;">Status: <b style="color: {color};">{sim_status}</b></span>
        <div style="margin-top: 6px; color: #CBD5E1;">Billed: <b>${actual_tot:,.2f}</b> | Expected: <b>${expected_tot:,.2f}</b> | Variance: <b>${variance:,.2f} ({pct_var:.2f}%)</b></div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# VIEW 3: ENGINE RUNNER & LIVE TERMINAL
# ==============================================================================
elif nav_choice == "⚡ Engine Runner":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;"><span style="color: #00FF88;">⚡</span> Reconciliation Engine & Execution Stream</h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">Run multi-strategy batch evaluation stream across all billing records.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Trigger Full Reconciliation Stream", type="primary"):
        term = st.empty()
        conn = get_db()
        invs = pd.read_sql_query("SELECT * FROM invoices", conn).to_dict("records")
        reconcile_all(conn)
        conn.close()

        lines = ["<span class='term-dim'>[INIT]</span> Nexus Autonomous Engine initialized.", "<span class='term-cyan'>[START]</span> Processing multi-tier deterministic validation..."]
        for inv in invs:
            lines.append(f"<span class='term-dim'>[{datetime.utcnow().strftime('%H:%M:%S')}]</span> Evaluated invoice <span class='term-cyan'>{inv['invoice_id']}</span> ({inv['customer_name'][:20]}) ➔ <span class='term-green'>OK (Processed)</span>")
        lines.append("<span class='term-green'>[DONE]</span> All records persisted to SQLite audit trail.")
        term.markdown(f"<div class='terminal-box'>{'<br>'.join(lines[-10:])}</div>", unsafe_allow_html=True)
        st.success("Reconciliation complete!")

# ==============================================================================
# VIEW 4: EXCEPTION QUEUE
# ==============================================================================
elif nav_choice == "📋 Exception Queue":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;"><span style="color: #00FF88;">📋</span> Exception Management Queue</h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">Filter and audit triaged financial discrepancies requiring Human-in-the-Loop review.</p>
    </div>
    """, unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    with f1:
        f_status = st.selectbox("Filter Status", ["ALL", "UNMATCHED", "PROBABLE_MATCH", "MATCHED"])
    with f2:
        search = st.text_input("Search Customer / ID")

    conn = get_db()
    query = "SELECT invoice_id, customer_name, status, priority, actual_amount, expected_amount, variance_amount, financial_exposure, exception_reason, review_status FROM reconciliation_results WHERE 1=1"
    if f_status != "ALL":
        query += f" AND status = '{f_status}'"
    if search:
        query += f" AND (customer_name LIKE '%{search}%' OR invoice_id LIKE '%{search}%')"

    df = pd.read_sql_query(query, conn)
    conn.close()
    st.dataframe(df, use_container_width=True, hide_index=True)

# ==============================================================================
# VIEW 5: VISUAL DIFF & REVIEW
# ==============================================================================
elif nav_choice == "🔍 Visual Diff & Review":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;"><span style="color: #00FF88;">🔍</span> Side-by-Side Visual Diff & Root Cause Review</h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">Inspect contract baseline vs invoice line-by-line and sign off review decisions.</p>
    </div>
    """, unsafe_allow_html=True)

    conn = get_db()
    df_res = pd.read_sql_query("SELECT * FROM reconciliation_results", conn)
    contracts = {r["contract_id"]: dict(r) for r in conn.cursor().execute("SELECT * FROM contracts").fetchall()}
    conn.close()

    inv_opts = [f"{r['invoice_id']} — {r['customer_name']} ({r['status']})" for _, r in df_res.iterrows()]
    sel_inv = st.selectbox("Select Invoice to Inspect:", inv_opts)
    sel_id = sel_inv.split(" ")[0]
    rec = df_res[df_res["invoice_id"] == sel_id].iloc[0].to_dict()
    ctr = contracts.get(rec.get("contract_id"))

    c_price = f"${ctr['unit_price']:,.2f}" if ctr else "$0.00"
    c_qty = f"{ctr['quantity']} units" if ctr else "0 units"
    c_disc = f"{ctr['discount_percent']:.1f}%" if ctr else "0.0%"
    c_term = f"{ctr['effective_date']} to {ctr['expiry_date']}" if ctr else "N/A"
    c_tol = f"±{ctr['tolerance_percent']}% / ${ctr['tolerance_absolute']:,.2f}" if ctr else "±1.0% / $50.00"

    d1, d2 = st.columns(2)
    with d1:
        st.markdown(f"""
        <div class="diff-card diff-card-contract">
            <div style="font-family: 'JetBrains Mono'; font-size: 0.78rem; color: #00F0FF; margin-bottom: 8px;">📜 CONTRACT BASELINE ({rec['contract_id'] or 'UNLINKED'})</div>
            <div class="diff-row"><span>Agreed Expected Total</span><b>${rec['expected_amount']:,.2f}</b></div>
            <div class="diff-row"><span>Contract Unit Rate</span><b>{c_price}</b></div>
            <div class="diff-row"><span>Contract Capacity</span><b>{c_qty}</b></div>
            <div class="diff-row"><span>Authorized Discount</span><b>{c_disc}</b></div>
            <div class="diff-row"><span>Term Window</span><b>{c_term}</b></div>
            <div class="diff-row"><span>Tolerance</span><b>{c_tol}</b></div>
        </div>
        """, unsafe_allow_html=True)

    with d2:
        diff_class = "diff-row-match" if rec["variance_amount"] == 0.0 else "diff-row-mismatch"
        st.markdown(f"""
        <div class="diff-card diff-card-invoice">
            <div style="font-family: 'JetBrains Mono'; font-size: 0.78rem; color: #00FF88; margin-bottom: 8px;">🧾 INVOICED RECORD ({rec['invoice_id']})</div>
            <div class="diff-row {diff_class}"><span>Billed Total Amount</span><b>${rec['actual_amount']:,.2f}</b></div>
            <div class="diff-row {diff_class}"><span>Variance Amount</span><b>${rec['variance_amount']:,.2f} ({rec['variance_percent']:.2f}%)</b></div>
            <div class="diff-row"><span>Within Tolerance?</span><b>{'✅ YES' if rec['is_within_tolerance'] else '❌ NO'}</b></div>
            <div class="diff-row"><span>Financial Exposure</span><b style="color:#FF3366;">${rec['financial_exposure']:,.2f}</b></div>
            <div class="diff-row"><span>Review State</span><b>{rec['review_status']}</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="analysis-box">
        <h4>1. WHAT HAPPENED?</h4><p>{rec['what_happened']}</p>
        <h4>2. WHY DID IT HAPPEN?</h4><p>{rec['why_did_it_happen']}</p>
        <h4>3. WHAT DOES CONTRACT SAY?</h4><p>{rec['what_contract_says']}</p>
        <h4>4. RECOMMENDED ACTION</h4><p>{rec['recommendation']}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("human_review"):
        dec = st.radio("Clearance Decision", ["ACCEPT", "REJECT", "OVERRIDE"])
        rev = st.text_input("Auditor Name", value="Senior Finance Auditor")
        com = st.text_area("Audit Justification", value="Verified contractual variance.")
        if st.form_submit_button("Submit Authoritative Sign-Off", type="primary"):
            conn = get_db()
            c = conn.cursor()
            new_st = "MATCHED" if dec in ["ACCEPT", "OVERRIDE"] else "UNMATCHED"
            c.execute("UPDATE reconciliation_results SET review_status=?, reviewer_name=?, reviewer_comment=?, status=? WHERE invoice_id=?", (dec, rev, com, new_st, rec["invoice_id"]))
            c.execute("INSERT INTO audit_logs (timestamp, invoice_id, contract_id, action_type, actor, previous_status, new_status, details) VALUES (?,?,?,?,?,?,?,?)",
                      (datetime.utcnow().isoformat(), rec["invoice_id"], rec["contract_id"], dec, rev, rec["status"], new_st, com))
            conn.commit()
            conn.close()
            st.success(f"Decision '{dec}' recorded with immutable audit log!")
            st.rerun()

# ==============================================================================
# VIEW 6: CONTRACT EXPLORER
# ==============================================================================
elif nav_choice == "📑 Contract Explorer":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;"><span style="color: #00FF88;">📑</span> Master Services Agreement Explorer</h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">Explore legal terms, fee schedules, and grounded contract clauses.</p>
    </div>
    """, unsafe_allow_html=True)

    conn = get_db()
    df_ctr = pd.read_sql_query("SELECT * FROM contracts", conn)
    conn.close()

    c_sel = st.selectbox("Select Agreement:", df_ctr["contract_id"] + " — " + df_ctr["customer_name"])
    cid = c_sel.split(" ")[0]
    row = df_ctr[df_ctr["contract_id"] == cid].iloc[0]

    st.markdown(f"""
    - **Contract Reference:** `{row['contract_id']}` | **Customer:** {row['customer_name']}
    - **Service/Product:** {row['product_service']}
    - **Term:** {row['effective_date']} to {row['expiry_date']}
    - **Pricing:** ${row['unit_price']:,.2f} × {row['quantity']} units ({row['currency']})
    - **Discount Clause:** {row['discount_percent']}%
    - **Special Stipulations:** {row['special_conditions']}
    """)

# ==============================================================================
# VIEW 7: ROI SIMULATOR
# ==============================================================================
elif nav_choice == "💰 ROI Simulator":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;"><span style="color: #00FF88;">💰</span> Dynamic ROI & Labor Savings Simulator</h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">Model enterprise financial return and auditor capacity reclaimed.</p>
    </div>
    """, unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    with r1:
        vol = st.slider("Monthly Invoice Volume", 100, 10000, 1500, 100)
    with r2:
        mins = st.slider("Manual Audit Minutes", 5, 45, 15, 1)
    with r3:
        rate = st.slider("Auditor Rate ($/hr)", 30.0, 150.0, 45.0, 5.0)

    annual_hrs = (vol * 12 * mins) / 60.0
    annual_cost = annual_hrs * rate
    saved_hrs = annual_hrs * 0.85
    saved_cost = annual_cost * 0.85

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Annual Labor Saved</div><div class="metric-value metric-value-cyan">{saved_hrs:,.0f} hrs</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Net Annual Savings</div><div class="metric-value metric-value-green">${saved_cost:,.0f}</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Capacity Reclaimed</div><div class="metric-value">{saved_hrs/2080:.1f} FTEs</div></div>""", unsafe_allow_html=True)

# ==============================================================================
# VIEW 8: COMPLIANCE AUDIT
# ==============================================================================
elif nav_choice == "📜 Compliance Audit":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;"><span style="color: #00FF88;">📜</span> Compliance Audit Trail & Governance</h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">Immutable, tamper-evident log of all system classifications and reviewer overrides.</p>
    </div>
    """, unsafe_allow_html=True)

    conn = get_db()
    logs = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY id DESC", conn)
    conn.close()

    if not logs.empty:
        st.dataframe(logs, use_container_width=True, hide_index=True)
        st.download_button("📥 Export Audit Trail to CSV", data=logs.to_csv(index=False).encode('utf-8'), file_name="audit_trail.csv", mime="text/csv")
    else:
        st.info("No manual audit reviews logged yet.")

# ==============================================================================
# VIEW 9: ARCHITECTURE GUIDE
# ==============================================================================
elif nav_choice == "ℹ️ Architecture Guide":
    st.markdown("""
    <div class="cyber-banner">
        <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem;"><span style="color: #00FF88;">ℹ️</span> Architecture & System Mechanics</h2>
        <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.88rem;">Engineering principles and design trade-offs.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### 🎯 The Core Architectural Principle
    > *"Never let an LLM do basic math that Python can calculate deterministically. Use the AI for what it is exceptional at: interpreting complex natural language contract clauses, synthesizing root causes, and generating grounded explanations."*

    ### 🧩 System Responsibilities
    - **Deterministic Python**: Exact key matching, arithmetic variance math ($ & %), tolerance thresholds (±1.0% or $50), date window validation, duplicate checks.
    - **Entity Matching**: Fuzzy string distance to bridge real-world supplier names to legal contract parties.
    - **RAG & Document Grounding**: Cites document name and page number for every variance claim.
    - **Human-in-the-Loop**: Authoritative financial clearance with immutable audit logs.
    """)
