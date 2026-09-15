from datetime import datetime, date
from typing import Optional, Dict, Any
from app.core.models import NormalizedInvoice, ContractTerms
from app.config import DEFAULT_TOLERANCE_PERCENT, DEFAULT_TOLERANCE_ABSOLUTE, DATE_TOLERANCE_DAYS

def evaluate_tolerance_match(
    invoice: NormalizedInvoice,
    contract: Optional[ContractTerms]
) -> Dict[str, Any]:
    """
    Deterministically computes financial amounts, variances, tolerances, and date validity.
    """
    if not contract:
        return {
            "expected_amount": 0.0,
            "actual_amount": invoice.total_amount,
            "variance_amount": invoice.total_amount,
            "variance_percent": 100.0,
            "is_within_tolerance": False,
            "amount_score": 0.0,
            "date_valid": False,
            "date_score": 0.0,
            "quantity_match": False,
            "discount_match": False,
            "notes": "Missing contract terms for comparison."
        }
    
    # 1. Deterministic Financial Math
    # Calculate base expected from contract quantity & unit price
    base_qty = contract.quantity if contract.quantity > 0 else 1
    unit_price = contract.unit_price
    gross_amount = base_qty * unit_price
    
    # Apply contractual discount
    discount_pct = contract.discount_percent
    discount_amount = gross_amount * (discount_pct / 100.0)
    expected_amount = round(gross_amount - discount_amount, 2)
    
    actual_amount = round(invoice.total_amount, 2)
    variance_amount = round(actual_amount - expected_amount, 2)
    abs_variance = abs(variance_amount)
    
    if expected_amount > 0:
        variance_percent = round((abs_variance / expected_amount) * 100.0, 2)
    else:
        variance_percent = 0.0 if actual_amount == 0 else 100.0
        
    tol_pct = contract.tolerance_percent if contract.tolerance_percent is not None else DEFAULT_TOLERANCE_PERCENT
    tol_abs = contract.tolerance_absolute if contract.tolerance_absolute is not None else DEFAULT_TOLERANCE_ABSOLUTE
    
    # Within tolerance if within percent margin OR within absolute floor
    is_exact_amount = abs_variance < 0.01
    is_within_tolerance = is_exact_amount or (variance_percent <= tol_pct) or (abs_variance <= tol_abs)
    
    # Amount match scoring
    if is_exact_amount:
        amount_score = 1.0
    elif is_within_tolerance:
        # Scaled between 0.70 and 0.90 depending on proximity
        amount_score = max(0.70, 0.90 - (variance_percent / tol_pct) * 0.20)
    else:
        # Rapidly decays if far beyond tolerance
        amount_score = max(0.0, 0.30 - (variance_percent / 100.0))
    amount_score = round(amount_score, 2)
    
    # 2. Quantity & Discount Matching
    qty_match = (invoice.quantity == contract.quantity)
    # Check if invoice applied discount matches contract discount
    invoice_discount_val = invoice.discount
    expected_discount_val = round(discount_amount, 2)
    discount_match = abs(invoice_discount_val - expected_discount_val) < 1.0 or (discount_pct == 0 and invoice_discount_val == 0)
    
    # 3. Date / Period Validation
    date_valid = True
    date_notes = "Invoice date within active contract term."
    date_score = 1.0
    
    if invoice.parsed_date:
        inv_dt = invoice.parsed_date
        try:
            eff_dt = datetime.strptime(contract.effective_date, "%Y-%m-%d").date()
            exp_dt = datetime.strptime(contract.expiry_date, "%Y-%m-%d").date()
            
            if inv_dt > exp_dt:
                date_valid = False
                days_after = (inv_dt - exp_dt).days
                date_notes = f"Contract Expired: Invoice dated {inv_dt} is {days_after} days after expiry {exp_dt}."
                date_score = 0.0
            elif inv_dt < eff_dt:
                date_valid = False
                days_before = (eff_dt - inv_dt).days
                date_notes = f"Pre-Contract: Invoice dated {inv_dt} is {days_before} days prior to effective date {eff_dt}."
                date_score = 0.1
        except Exception:
            date_notes = "Could not parse contract effective/expiry dates."
            date_score = 0.5
    else:
        date_notes = "Invoice date could not be parsed."
        date_score = 0.5
        
    return {
        "expected_amount": expected_amount,
        "actual_amount": actual_amount,
        "variance_amount": variance_amount,
        "variance_percent": variance_percent,
        "is_within_tolerance": is_within_tolerance,
        "is_exact_amount": is_exact_amount,
        "amount_score": amount_score,
        "quantity_match": qty_match,
        "discount_match": discount_match,
        "date_valid": date_valid,
        "date_score": date_score,
        "date_notes": date_notes,
    }
