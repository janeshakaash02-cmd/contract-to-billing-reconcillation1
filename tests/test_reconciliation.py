import pytest
from app.core.models import RawInvoice, ContractTerms, ReconciliationStatus, ExceptionPriority
from app.reconciliation.engine import ReconciliationEngine
from app.reconciliation.confidence import calculate_confidence_score

@pytest.fixture
def sample_contracts():
    return [
        ContractTerms(
            contract_id="CTR-REC-01",
            customer_id="CUST-801",
            customer_name="Starlight Media Group",
            effective_date="2025-01-01",
            expiry_date="2025-06-30",
            product_service="CDN Bandwidth Tier",
            quantity=1,
            unit_price=10000.0,
            currency="USD",
            billing_frequency="Monthly",
            discount_percent=10.0,
            tolerance_percent=1.0,
            tolerance_absolute=50.0,
        )
    ]

def test_reconciliation_exact_matched(sample_contracts):
    engine = ReconciliationEngine(sample_contracts)
    raw = RawInvoice(
        invoice_id="INV-R1",
        contract_id="CTR-REC-01",
        customer_id="CUST-801",
        customer_name="Starlight Media Group",
        invoice_date="2025-03-15",
        billing_period="2025-03",
        currency="USD",
        quantity=1,
        unit_price=10000.0,
        discount=1000.0,
        total_amount=9000.0,
    )
    res = engine.reconcile_invoice(raw)
    assert res.status == ReconciliationStatus.MATCHED
    assert res.variance_amount == 0.0
    assert res.financial_exposure == 0.0
    assert res.confidence_score >= 0.90

def test_reconciliation_discount_mismatch(sample_contracts):
    engine = ReconciliationEngine(sample_contracts)
    # Billed 10000 instead of 9000
    raw = RawInvoice(
        invoice_id="INV-R2",
        contract_id="CTR-REC-01",
        customer_id="CUST-801",
        customer_name="Starlight Media Group",
        invoice_date="2025-03-15",
        billing_period="2025-03",
        currency="USD",
        quantity=1,
        unit_price=10000.0,
        discount=0.0,
        total_amount=10000.0,
    )
    res = engine.reconcile_invoice(raw)
    assert res.status == ReconciliationStatus.UNMATCHED
    assert res.variance_amount == 1000.0
    assert res.financial_exposure == 1000.0
    assert "discount" in res.exception_reason.lower()

def test_reconciliation_contract_expired(sample_contracts):
    engine = ReconciliationEngine(sample_contracts)
    # Dated July 15 (contract expired June 30)
    raw = RawInvoice(
        invoice_id="INV-R3",
        contract_id="CTR-REC-01",
        customer_id="CUST-801",
        customer_name="Starlight Media Group",
        invoice_date="2025-07-15",
        billing_period="2025-07",
        currency="USD",
        quantity=1,
        unit_price=10000.0,
        total_amount=9000.0,
    )
    res = engine.reconcile_invoice(raw)
    assert res.status == ReconciliationStatus.UNMATCHED
    assert res.priority == ExceptionPriority.HIGH
    assert "expired" in res.exception_reason.lower()

def test_reconciliation_currency_mismatch(sample_contracts):
    engine = ReconciliationEngine(sample_contracts)
    raw = RawInvoice(
        invoice_id="INV-R4",
        contract_id="CTR-REC-01",
        customer_id="CUST-801",
        customer_name="Starlight Media Group",
        invoice_date="2025-03-15",
        billing_period="2025-03",
        currency="EUR",  # Contract is USD
        quantity=1,
        unit_price=10000.0,
        total_amount=9000.0,
    )
    res = engine.reconcile_invoice(raw)
    assert res.status == ReconciliationStatus.UNMATCHED
    assert res.priority == ExceptionPriority.HIGH
    assert "currency mismatch" in res.exception_reason.lower()

def test_reconciliation_missing_contract(sample_contracts):
    engine = ReconciliationEngine(sample_contracts)
    raw = RawInvoice(
        invoice_id="INV-R5",
        contract_id="NON_EXISTENT",
        customer_id="UNKNOWN_CUST",
        customer_name="Unknown Offshore Vendor LLC",
        invoice_date="2025-03-15",
        currency="USD",
        quantity=1,
        unit_price=3500.0,
        total_amount=3500.0,
    )
    res = engine.reconcile_invoice(raw)
    assert res.status == ReconciliationStatus.UNMATCHED
    assert res.priority == ExceptionPriority.HIGH
    assert res.financial_exposure == 3500.0

def test_reconciliation_data_quality_exception(sample_contracts):
    engine = ReconciliationEngine(sample_contracts)
    raw = RawInvoice(
        invoice_id="INV-R6",
        contract_id="CTR-REC-01",
        customer_id="CUST-801",
        customer_name="",  # Missing customer name
        invoice_date="2025-03-15",
        currency="USD",
        quantity=1,
        unit_price=0.0,
        total_amount=-250.0,  # Negative total
    )
    res = engine.reconcile_invoice(raw)
    assert res.status == ReconciliationStatus.DATA_QUALITY_EXCEPTION
    assert res.priority == ExceptionPriority.HIGH

def test_explainable_confidence_breakdown():
    exact = {"contract_id_match": True, "customer_id_match": True, "currency_match": True, "score": 1.0}
    tol = {"is_exact_amount": True, "amount_score": 1.0, "date_valid": True, "date_score": 1.0}
    fuzzy = {"name_score": 1.0}
    
    breakdown = calculate_confidence_score(
        exact_res=exact,
        tolerance_res=tol,
        fuzzy_res=fuzzy,
        has_evidence=True,
        is_duplicate=False,
        has_contract=True
    )
    
    # Weights: 0.30 + 0.35 + 0.15 + 0.10 + 0.10 = 1.00
    assert breakdown.total_score >= 0.95
    assert breakdown.id_match_score == 1.0
    assert breakdown.amount_match_score == 1.0
    assert len(breakdown.factors) >= 4
