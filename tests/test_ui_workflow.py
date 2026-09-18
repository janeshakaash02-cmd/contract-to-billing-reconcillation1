import pytest
from streamlit.testing.v1 import AppTest
from app.database.db import get_all_contracts, get_all_invoices, get_reconciliation_results

def test_app_navigation_and_order():
    """Verify sidebar navigation has exact 10 options in exact order."""
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()
    assert not at.exception
    
    # Check sidebar radio options
    radios = at.sidebar.radio
    assert len(radios) >= 1
    nav_radio = radios[0]
    options = nav_radio.options
    
    expected_prefixes = [
        "📊 Executive Dashboard",
        "🔎 Single Invoice Reconciliation",
        "⚡ Batch Reconciliation Engine",
        "🧪 What-If Sandbox",
        "📋 Exception Queue",
        "🔍 Visual Diff & Review",
        "📑 Contract Explorer",
        "💰 ROI Simulator",
        "📜 Compliance Audit",
        "ℹ️ Architecture Guide",
    ]
    
    assert len(options) == 10
    for i, prefix in enumerate(expected_prefixes):
        assert options[i].startswith(prefix), f"Expected option {i} to start with '{prefix}', got '{options[i]}'"

def test_single_invoice_reconciliation_workflow():
    """Test Contract -> Invoice -> Reconcile -> Explanation -> Human Review -> Audit Trail."""
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()
    assert not at.exception
    
    # Select Single Invoice Reconciliation
    nav_radio = at.sidebar.radio[0]
    single_recon_opt = [o for o in nav_radio.options if "Single Invoice Reconciliation" in o][0]
    nav_radio.set_value(single_recon_opt).run()
    assert not at.exception
    
    # Verify Step 1: Contract Selectbox
    contract_select = at.selectbox(key="single_recon_contract_select")
    assert contract_select is not None
    assert len(contract_select.options) > 0
    
    # Select first contract
    contract_select.select_index(0).run()
    assert not at.exception
    
    # Verify Step 2: Invoice Selectbox (or no invoices warning)
    inv_select = at.selectbox(key="single_recon_invoice_select")
    assert inv_select is not None
    assert len(inv_select.options) > 0
    
    # Step 3: Click Reconcile Selected Invoice button
    recon_btn = [b for b in at.button if "Reconcile Selected Invoice" in b.label]
    assert len(recon_btn) == 1
    recon_btn[0].click().run()
    assert not at.exception
    
    # Verify Step 4: Explanation text exists
    exp_markdown = [m for m in at.markdown if "Why did this result occur?" in m.value or "WHAT HAPPENED" in m.value]
    assert len(exp_markdown) > 0
    
    # Verify Step 5: Human Review Form
    at.text_input(key="sr_reviewer_name").set_value("Lead Compliance Auditor")
    at.text_area(key="sr_comment").set_value("Approved under standard contractual terms verification.")
    submit_btn = [b for b in at.button if "Submit Review Decision" in b.label]
    assert len(submit_btn) == 1
    submit_btn[0].click().run()
    assert not at.exception

def test_cross_module_navigation_dashboard():
    """Test Executive Dashboard action buttons."""
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()
    assert not at.exception
    
    # Click 'Run Single Reconciliation' button
    btn_single = [b for b in at.button if "Run Single Reconciliation" in b.label]
    assert len(btn_single) == 1
    btn_single[0].click().run()
    assert not at.exception
    
    # Verify radio navigated to Single Invoice Reconciliation
    assert "Single Invoice Reconciliation" in at.sidebar.radio[0].value

def test_cross_module_navigation_contract_explorer():
    """Test Contract Explorer -> Open in Single Invoice Reconciliation."""
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()
    
    # Navigate to Contract Explorer
    nav_radio = at.sidebar.radio[0]
    ce_opt = [o for o in nav_radio.options if "Contract Explorer" in o][0]
    nav_radio.set_value(ce_opt).run()
    assert not at.exception
    
    # Click 'Open in Single Invoice Reconciliation' button if related invoices exist
    btn_open = [b for b in at.button if "Open in Single Invoice Reconciliation" in b.label]
    if btn_open:
        btn_open[0].click().run()
        assert not at.exception
        assert "Single Invoice Reconciliation" in at.sidebar.radio[0].value

def test_what_if_sandbox_labels():
    """Verify What-If Sandbox simulation explanation and Hypothetical Invoice label."""
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()
    
    nav_radio = at.sidebar.radio[0]
    wi_opt = [o for o in nav_radio.options if "What-If Sandbox" in o][0]
    nav_radio.set_value(wi_opt).run()
    assert not at.exception
    
    # Check notice and label
    all_markdown = " ".join(m.value for m in at.markdown)
    assert "This is a simulation environment" in all_markdown
    assert "Hypothetical Invoice" in all_markdown

def test_batch_engine_notice():
    """Verify Batch Reconciliation Engine has the required top notice."""
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()
    
    nav_radio = at.sidebar.radio[0]
    be_opt = [o for o in nav_radio.options if "Batch Reconciliation Engine" in o][0]
    nav_radio.set_value(be_opt).run()
    assert not at.exception
    
    all_markdown = " ".join(m.value for m in at.markdown)
    assert "This page reconciles multiple invoices against their associated contracts" in all_markdown

def test_exception_queue_investigate_invoice():
    """Verify Exception Queue has Investigate Invoice button that navigates to Single Recon."""
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()
    
    nav_radio = at.sidebar.radio[0]
    eq_opt = [o for o in nav_radio.options if "Exception Queue" in o][0]
    nav_radio.set_value(eq_opt).run()
    assert not at.exception
    
    # Check Investigate Invoice button
    inv_btn = [b for b in at.button if "Investigate Invoice" in b.label]
    if inv_btn:
        inv_btn[0].click().run()
        assert not at.exception
        assert "Single Invoice Reconciliation" in at.sidebar.radio[0].value

def test_visual_diff_inspection():
    """Verify Visual Diff automatically identifies contract and displays side-by-side comparison."""
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()
    
    nav_radio = at.sidebar.radio[0]
    vd_opt = [o for o in nav_radio.options if "Visual Diff" in o][0]
    nav_radio.set_value(vd_opt).run()
    assert not at.exception
    
    all_markdown = " ".join(m.value for m in at.markdown)
    assert "ASSOCIATED CONTRACT DETECTED" in all_markdown
    assert "CONTRACT BASELINE" in all_markdown
    assert "ACTUAL INVOICE" in all_markdown
    
    # Check action buttons
    button_labels = [b.label for b in at.button]
    assert any("Go to Human Review" in lbl for lbl in button_labels)
    assert any("View Contract Evidence" in lbl for lbl in button_labels)
    assert any("View Audit History" in lbl for lbl in button_labels)

