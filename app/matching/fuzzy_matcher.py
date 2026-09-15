from typing import Optional, Dict, Any
from rapidfuzz import fuzz
from app.core.models import NormalizedInvoice, ContractTerms
from app.matching.normalizer import normalize_customer_name

def evaluate_fuzzy_match(
    invoice: NormalizedInvoice,
    contract: Optional[ContractTerms]
) -> Dict[str, Any]:
    """
    Evaluates fuzzy string similarity between invoice metadata and contract terms.
    Handles variations in company legal suffixes, abbreviations, and word orders.
    """
    if not contract:
        return {
            "name_similarity": 0.0,
            "name_score": 0.0,
            "is_name_match": False,
            "product_similarity": 0.0,
            "notes": "No contract to perform fuzzy comparison against."
        }
        
    inv_clean_name = invoice.clean_customer_name
    contract_clean_name = normalize_customer_name(contract.customer_name)
    
    # Calculate token sort ratio (robust to word order differences)
    token_sort = fuzz.token_sort_ratio(inv_clean_name, contract_clean_name) / 100.0
    token_set = fuzz.token_set_ratio(inv_clean_name, contract_clean_name) / 100.0
    ratio = fuzz.ratio(inv_clean_name, contract_clean_name) / 100.0
    
    # Combined similarity
    name_similarity = max(token_sort, token_set, ratio)
    
    # Evaluate product similarity if reference or description is available
    product_similarity = 0.0
    if invoice.reference_number:
        clean_ref = invoice.reference_number.lower()
        clean_prod = contract.product_service.lower()
        product_similarity = fuzz.partial_ratio(clean_ref, clean_prod) / 100.0
        
    is_name_match = name_similarity >= 0.75
    
    return {
        "name_similarity": round(name_similarity, 2),
        "name_score": round(name_similarity, 2),
        "is_name_match": is_name_match,
        "product_similarity": round(product_similarity, 2),
        "notes": f"Fuzzy name similarity: {int(name_similarity * 100)}% ('{invoice.customer_name}' vs '{contract.customer_name}')"
    }
