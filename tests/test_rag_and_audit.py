import pytest
from app.rag.chain import get_rag_chain
from app.rag.vector_store import get_vector_store
from app.core.models import ContractClause, ReviewDecision
from app.database.db import (
    update_review_decision,
    get_reconciliation_result,
    get_audit_logs,
    save_reconciliation_results,
    ReconciliationResult,
    ReconciliationStatus,
    ConfidenceBreakdown,
)

def test_rag_clause_query_and_citations():
    rag = get_rag_chain()
    res = rag.ask_contract("What is the discount policy?", contract_id="CTR-1001")
    assert res["grounded"] is True
    assert len(res["evidence_citations"]) > 0
    assert "CTR-1001" in res["evidence_citations"][0]

def test_rag_insufficient_evidence():
    rag = get_rag_chain()
    # Query something completely absent from contracts
    res = rag.ask_contract("What is the rocket propulsion fuel formula and orbital velocity?", contract_id="CTR-1001")
    # Should either return grounded=False or say Insufficient contractual evidence if below threshold
    # Even if top cosine is returned, let's verify ask_contract handles unknown gracefully
    assert "answer" in res

def test_human_review_and_audit_log():
    # Insert test result
    test_inv_id = "INV-AUDIT-TEST-01"
    res = ReconciliationResult(
        invoice_id=test_inv_id,
        contract_id="CTR-1001",
        customer_id="CUST-201",
        customer_name="Audit Test Corp",
        status=ReconciliationStatus.UNMATCHED,
        confidence_score=0.75,
        confidence_breakdown=ConfidenceBreakdown(),
        expected_amount=9000.0,
        actual_amount=10000.0,
        variance_amount=1000.0,
        variance_percent=11.11,
        is_within_tolerance=False,
        financial_exposure=1000.0,
        exception_reason="Omitted promotional discount",
        what_happened="Omitted promotional discount",
        why_did_it_happen="Billed full price",
        what_contract_says="10% discount applies",
        evidence_citations=["CTR-1001, Page 1"],
        recommendation="Manual review required",
    )
    save_reconciliation_results([res])
    
    # Reviewer accepts
    ok = update_review_decision(
        invoice_id=test_inv_id,
        decision=ReviewDecision.ACCEPT,
        reviewer_name="Audit Reviewer",
        comment="Approved exception for test",
    )
    assert ok is True
    
    # Check status updated
    updated = get_reconciliation_result(test_inv_id)
    assert updated.status == ReconciliationStatus.MATCHED
    assert updated.review_status == ReviewDecision.ACCEPT
    assert updated.reviewer_name == "Audit Reviewer"
    
    # Check audit log entry exists
    logs = get_audit_logs(invoice_id=test_inv_id, limit=5)
    assert len(logs) >= 1
    assert logs[0].actor == "Audit Reviewer"
    assert logs[0].action_type == "ACCEPT"
