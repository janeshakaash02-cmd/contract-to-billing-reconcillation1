from typing import Optional, Dict, Any
from app.core.models import NormalizedInvoice, ContractTerms

def evaluate_exact_match(invoice: NormalizedInvoice, contract: Optional[ContractTerms]) -> Dict[str, Any]:
    """
    Evaluates exact deterministic matching between an invoice and contract.
    Returns individual field match statuses and overall exact match score.
    """
    if not contract:
        return {
            "has_contract": False,
            "contract_id_match": False,
            "customer_id_match": False,
            "currency_match": False,
            "is_exact_match": False,
            "score": 0.0,
            "notes": "No matching contract provided or found."
        }
    
    contract_id_match = (
        bool(invoice.contract_id) and 
        invoice.contract_id.upper() == contract.contract_id.upper()
    )
    
    customer_id_match = (
        bool(invoice.customer_id) and 
        invoice.customer_id.upper() == contract.customer_id.upper()
    )
    
    currency_match = (
        invoice.currency.upper() == contract.currency.upper()
    )
    
    # Identifier score: contract_id (0.6) + customer_id (0.4) if both present
    id_score = 0.0
    if contract_id_match:
        id_score += 0.65
    if customer_id_match:
        id_score += 0.35
        
    return {
        "has_contract": True,
        "contract_id_match": contract_id_match,
        "customer_id_match": customer_id_match,
        "currency_match": currency_match,
        "is_exact_id_match": contract_id_match,
        "score": round(id_score, 2),
        "notes": "Exact contract ID and customer ID matched." if (contract_id_match and customer_id_match) else "Partial or missing exact identifier match."
    }
