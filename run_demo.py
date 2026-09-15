import os
import sys
from typing import List

from app.database.db import (
    get_all_contracts,
    get_all_invoices,
    get_reconciliation_results,
    update_review_decision,
    get_audit_logs,
    get_dashboard_summary_metrics,
)
from app.core.models import ReviewDecision
from app.reconciliation.engine import ReconciliationEngine
from generate_data import generate_all_data

def run_cli_demo():
    print("================================================================================")
    print("AI-ASSISTED CONTRACT-TO-BILLING RECONCILIATION ENGINE - DEMO WALKTHROUGH")
    print("================================================================================")
    
    # Check if contracts exist; if not, generate
    contracts = get_all_contracts()
    if not contracts:
        print("[*] No contracts found in database. Generating synthetic datasets first...")
        generate_all_data()
        contracts = get_all_contracts()
        
    invoices = get_all_invoices()
    print(f"\n[+] Loaded {len(contracts)} executed customer contracts.")
    print(f"[+] Loaded {len(invoices)} billing invoices.")
    
    # Run Reconciliation Engine
    print("\n[+] Running Reconciliation Engine across all invoices...")
    engine = ReconciliationEngine(contracts)
    results = engine.reconcile_batch(invoices, persist_to_db=True)
    
    # Display Dashboard Summary
    metrics = get_dashboard_summary_metrics()
    print("\n================================================================================")
    print("                       EXECUTIVE RECONCILIATION SUMMARY                         ")
    print("================================================================================")
    print(f" Total Invoices Processed:        {metrics['total_reconciled']}")
    print(f" Auto-Matched (Zero Discrepancy): {metrics['matched']}")
    print(f" Probable Matches (In Tolerance): {metrics['probable_matches']}")
    print(f" Exceptions (Requiring Review):   {metrics['unmatched'] + metrics['duplicates'] + metrics['data_quality_exceptions']}")
    print(f"   - Duplicate Invoices:          {metrics['duplicates']}")
    print(f"   - Material Variances:          {metrics['unmatched']}")
    print(f"   - Data Quality Anomalies:      {metrics['data_quality_exceptions']}")
    print("--------------------------------------------------------------------------------")
    print(f" Auto-Match Rate:                 {metrics['auto_match_rate']}%")
    print(f" Total Financial Risk Exposure:   ${metrics['total_financial_exposure']:,.2f}")
    print(f" Estimated Manual Hours Saved:    {metrics['hours_saved']} hours (at $45/hr = ${metrics['cost_saved']:,.2f})")
    print("================================================================================")
    
    # Pick a high-priority exception to demonstrate deep reasoning & evidence
    exceptions = [r for r in results if r.status.value != "MATCHED"]
    if exceptions:
        demo_ex = exceptions[0]
        print("\n================================================================================")
        print(f" EXCEPTION DEEP-DIVE: Invoice {demo_ex.invoice_id} ({demo_ex.customer_name})")
        print("================================================================================")
        print(f" Status:             {demo_ex.status.value} [Priority: {demo_ex.priority.value}]")
        print(f" Contract Ref:       {demo_ex.contract_id}")
        print(f" Expected Amount:    ${demo_ex.expected_amount:,.2f}")
        print(f" Actual Billed:      ${demo_ex.actual_amount:,.2f}")
        print(f" Financial Variance: ${demo_ex.variance_amount:,.2f} ({demo_ex.variance_percent:.2f}%)")
        print(f" Financial Exposure: ${demo_ex.financial_exposure:,.2f}")
        print(f" Confidence Score:   {int(demo_ex.confidence_score * 100)}% (Explainable Score)")
        print("\n Confidence Score Breakdown:")
        for factor in demo_ex.confidence_breakdown.factors:
            print(f"   * {factor}")
            
        print("\n AI & RAG Root Cause Analysis:")
        print(f" 1. WHAT HAPPENED?\n    {demo_ex.what_happened}")
        print(f"\n 2. WHY DID IT HAPPEN?\n    {demo_ex.why_did_it_happen}")
        print(f"\n 3. WHAT DOES THE CONTRACT SAY?\n    {demo_ex.what_contract_says}")
        print(f"\n 4. RETRIEVED EVIDENCE CITATIONS:")
        for cite in demo_ex.evidence_citations:
            print(f"    - {cite}")
        print(f"\n 5. WHAT SHOULD THE FINANCE REVIEWER DO?\n    {demo_ex.recommendation}")
        
        # Demonstrate Human Review Action
        print("\n================================================================================")
        print(" HUMAN-IN-THE-LOOP REVIEW WORKFLOW")
        print("================================================================================")
        print(f" Executing simulated Reviewer Action: OVERRIDE on {demo_ex.invoice_id}...")
        update_review_decision(
            invoice_id=demo_ex.invoice_id,
            decision=ReviewDecision.OVERRIDE,
            reviewer_name="Sarah Jenkins (Senior Controller)",
            comment="Approved partial discount offset per customer Q3 renewal concession email.",
            override_amount=demo_ex.expected_amount
        )
        print(" [OK] Decision successfully committed with immutable audit logging.")
        
        # Inspect Audit Trail
        print("\n================================================================================")
        print(" AUDIT TRAIL LOG ENTRY")
        print("================================================================================")
        recent_logs = get_audit_logs(invoice_id=demo_ex.invoice_id, limit=2)
        for log in recent_logs:
            print(f" [{log.timestamp}] Actor: {log.actor} | Action: {log.action_type}")
            print(f"   Status: {log.previous_status} -> {log.new_status}")
            print(f"   Details: {log.details}")
            print(f"   Citation: {log.evidence_citation}")
            print("--------------------------------------------------------------------------------")
            
    print("\n[+] Demo completed successfully. Launch Streamlit UI for the full interactive dashboard:")
    print("    streamlit run streamlit_app.py\n")

if __name__ == "__main__":
    run_cli_demo()
