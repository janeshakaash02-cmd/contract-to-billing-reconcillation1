import pytest
from app.core.models import RawInvoice, ContractTerms
from app.matching.normalizer import (
    normalize_invoice,
    normalize_currency,
    normalize_customer_name,
    parse_flexible_date,
)
from app.matching.exact_matcher import evaluate_exact_match
from app.matching.tolerance_matcher import evaluate_tolerance_match
from app.matching.fuzzy_matcher import evaluate_fuzzy_match
from app.matching.engine import MatchingEngine

@pytest.fixture
def sample_contract():
    return ContractTerms(
        contract_id="CTR-TEST-01",
        customer_id="CUST-901",
        customer_name="Acme Global Corporation Inc.",
        effective_date="2025-01-01",
        expiry_date="2025-12-31",
        product_service="Cloud Infrastructure Suite",
        quantity=100,
        unit_price=50.0,
        currency="USD",
        billing_frequency="Monthly",
        discount_percent=10.0,
        tolerance_percent=1.0,
        tolerance_absolute=50.0,
    )

def test_currency_normalization():
    assert normalize_currency("USD") == "USD"
    assert normalize_currency("$") == "USD"
    assert normalize_currency("EUR") == "EUR"
    assert normalize_currency("€") == "EUR"
    assert normalize_currency("₹") == "INR"
    assert normalize_currency("INR") == "INR"
    assert normalize_currency("£") == "GBP"

def test_customer_name_cleaning():
    assert normalize_customer_name("Acme Global Corporation Inc.") == "acme"
    assert normalize_customer_name("Beta Technologies Pvt Ltd") == "beta"
    assert normalize_customer_name("Delta Solutions LLC") == "delta"

def test_flexible_date_parsing():
    iso_val, dt = parse_flexible_date("2025-04-15")
    assert iso_val == "2025-04-15"
    assert dt.year == 2025 and dt.month == 4 and dt.day == 15

    iso_val, dt = parse_flexible_date("15-04-2025")
    assert iso_val == "2025-04-15"

    iso_val, dt = parse_flexible_date("04/15/2025")
    assert iso_val == "2025-04-15"

def test_exact_match_success(sample_contract):
    raw = RawInvoice(
        invoice_id="INV-101",
        contract_id="CTR-TEST-01",
        customer_id="CUST-901",
        customer_name="Acme Global Corporation Inc.",
        invoice_date="2025-05-15",
        currency="USD",
        quantity=100,
        unit_price=50.0,
        total_amount=4500.0,
    )
    norm = normalize_invoice(raw)
    res = evaluate_exact_match(norm, sample_contract)
    assert res["is_exact_id_match"] is True
    assert res["currency_match"] is True
    assert res["score"] == 1.0

def test_exact_match_missing_contract():
    raw = RawInvoice(
        invoice_id="INV-102",
        contract_id=None,
        customer_id="CUST-999",
        customer_name="Unknown Entity",
        invoice_date="2025-05-15",
        currency="USD",
        quantity=1,
        unit_price=100.0,
        total_amount=100.0,
    )
    norm = normalize_invoice(raw)
    res = evaluate_exact_match(norm, None)
    assert res["has_contract"] is False
    assert res["score"] == 0.0

def test_tolerance_match_exact_amount(sample_contract):
    # 100 * 50 = 5000 - 10% = 4500
    raw = RawInvoice(
        invoice_id="INV-103",
        contract_id="CTR-TEST-01",
        customer_id="CUST-901",
        customer_name="Acme Global Corp",
        invoice_date="2025-05-15",
        currency="USD",
        quantity=100,
        unit_price=50.0,
        total_amount=4500.0,
    )
    norm = normalize_invoice(raw)
    res = evaluate_tolerance_match(norm, sample_contract)
    assert res["expected_amount"] == 4500.0
    assert res["variance_amount"] == 0.0
    assert res["is_exact_amount"] is True
    assert res["is_within_tolerance"] is True
    assert res["amount_score"] == 1.0

def test_tolerance_match_within_limit(sample_contract):
    # 4500 + 0.4% = 4518 (within 1% and within $50)
    raw = RawInvoice(
        invoice_id="INV-104",
        contract_id="CTR-TEST-01",
        customer_id="CUST-901",
        customer_name="Acme Global Corp",
        invoice_date="2025-05-15",
        currency="USD",
        quantity=100,
        unit_price=50.0,
        total_amount=4518.0,
    )
    norm = normalize_invoice(raw)
    res = evaluate_tolerance_match(norm, sample_contract)
    assert res["is_within_tolerance"] is True
    assert res["is_exact_amount"] is False
    assert res["variance_amount"] == 18.0
    assert res["variance_percent"] == 0.4

def test_tolerance_match_exceeds_limit(sample_contract):
    # 4500 + 10% = 4950 (exceeds 1% and $50)
    raw = RawInvoice(
        invoice_id="INV-105",
        contract_id="CTR-TEST-01",
        customer_id="CUST-901",
        customer_name="Acme Global Corp",
        invoice_date="2025-05-15",
        currency="USD",
        quantity=100,
        unit_price=50.0,
        total_amount=4950.0,
    )
    norm = normalize_invoice(raw)
    res = evaluate_tolerance_match(norm, sample_contract)
    assert res["is_within_tolerance"] is False
    assert res["variance_amount"] == 450.0
    assert res["variance_percent"] == 10.0

def test_fuzzy_customer_name_matching(sample_contract):
    raw = RawInvoice(
        invoice_id="INV-106",
        contract_id="CTR-TEST-01",
        customer_id="CUST-901",
        customer_name="Acme Global Corp",
        invoice_date="2025-05-15",
        currency="USD",
        quantity=100,
        unit_price=50.0,
        total_amount=4500.0,
    )
    norm = normalize_invoice(raw)
    res = evaluate_fuzzy_match(norm, sample_contract)
    assert res["name_similarity"] >= 0.80
    assert res["is_name_match"] is True

def test_duplicate_detection(sample_contract):
    engine = MatchingEngine([sample_contract])
    inv1 = RawInvoice(
        invoice_id="INV-201",
        contract_id="CTR-TEST-01",
        customer_id="CUST-901",
        customer_name="Acme Global Corp",
        invoice_date="2025-05-15",
        billing_period="2025-05",
        currency="USD",
        quantity=100,
        unit_price=50.0,
        total_amount=4500.0,
    )
    inv2 = RawInvoice(
        invoice_id="INV-202",
        contract_id="CTR-TEST-01",
        customer_id="CUST-901",
        customer_name="Acme Global Corp",
        invoice_date="2025-05-18",
        billing_period="2025-05",
        currency="USD",
        quantity=100,
        unit_price=50.0,
        total_amount=4500.0,
    )
    res = engine.match(inv2, existing_invoices=[inv1])
    assert res["is_duplicate"] is True
    assert res["duplicate_ref"] == "INV-201"
