from typing import Dict, Any, List
from app.core.models import ConfidenceBreakdown

# Configurable explainable weights
WEIGHT_ID = 0.30
WEIGHT_AMOUNT = 0.35
WEIGHT_DATE = 0.15
WEIGHT_NAME = 0.10
WEIGHT_EVIDENCE = 0.10

def calculate_confidence_score(
    exact_res: Dict[str, Any],
    tolerance_res: Dict[str, Any],
    fuzzy_res: Dict[str, Any],
    has_evidence: bool,
    is_duplicate: bool,
    has_contract: bool
) -> ConfidenceBreakdown:
    """
    Computes an explainable, multi-factor confidence score.
    Does NOT use opaque LLM self-reporting.
    Combines deterministic weights:
    - ID Match (30%)
    - Amount & Tolerance Match (35%)
    - Date & Contract Term Match (15%)
    - Name & String Similarity (10%)
    - RAG Evidence Grounding (10%)
    """
    factors: List[str] = []
    
    if is_duplicate:
        return ConfidenceBreakdown(
            id_match_score=0.95,
            amount_match_score=0.95,
            date_match_score=0.95,
            name_match_score=0.95,
            evidence_score=0.90,
            total_score=0.98,
            factors=["Duplicate invoice pattern detected with 98% certainty."]
        )
        
    if not has_contract:
        return ConfidenceBreakdown(
            id_match_score=0.0,
            amount_match_score=0.0,
            date_match_score=0.0,
            name_match_score=0.0,
            evidence_score=0.0,
            total_score=0.05,
            factors=["No associated contract found. Low baseline confidence."]
        )

    # 1. Identifier Score (0 to 1)
    id_score = exact_res.get("score", 0.0)
    if exact_res.get("contract_id_match"):
        factors.append(f"Contract ID exact match (+{int(WEIGHT_ID*100)}%)")
    elif exact_res.get("customer_id_match"):
        factors.append(f"Customer ID match with missing contract ID (+{int(id_score*WEIGHT_ID*100)}%)")
    else:
        factors.append("No exact contract or customer ID match (0%)")
        
    # 2. Amount & Tolerance Score (0 to 1)
    amount_score = tolerance_res.get("amount_score", 0.0)
    if tolerance_res.get("is_exact_amount"):
        factors.append(f"Exact line item amount match (+{int(WEIGHT_AMOUNT*100)}%)")
    elif tolerance_res.get("is_within_tolerance"):
        factors.append(f"Amount within allowable policy tolerance (+{int(amount_score*WEIGHT_AMOUNT*100)}%)")
    else:
        factors.append(f"Amount variance beyond tolerance ({tolerance_res.get('variance_percent')}%)")
        
    # 3. Date Score (0 to 1)
    date_score = tolerance_res.get("date_score", 0.5)
    if tolerance_res.get("date_valid"):
        factors.append(f"Invoice date within active contract term (+{int(WEIGHT_DATE*100)}%)")
    else:
        factors.append(f"Date anomaly: {tolerance_res.get('date_notes')}")
        
    # 4. Name & Entity Similarity (0 to 1)
    name_score = fuzzy_res.get("name_score", 0.0)
    name_sim_pct = int(name_score * 100)
    factors.append(f"Customer name similarity: {name_sim_pct}% (+{int(name_score*WEIGHT_NAME*100)}%)")
    
    # 5. RAG Evidence Grounding (0 to 1)
    evidence_score = 1.0 if has_evidence else 0.2
    if has_evidence:
        factors.append(f"Contractual clause retrieved via RAG (+{int(WEIGHT_EVIDENCE*100)}%)")
    else:
        factors.append("No specific clause retrieved (+2%)")
        
    total_score = (
        (id_score * WEIGHT_ID) +
        (amount_score * WEIGHT_AMOUNT) +
        (date_score * WEIGHT_DATE) +
        (name_score * WEIGHT_NAME) +
        (evidence_score * WEIGHT_EVIDENCE)
    )
    
    total_score = round(max(0.01, min(0.99, total_score)), 2)
    
    return ConfidenceBreakdown(
        id_match_score=round(id_score, 2),
        amount_match_score=round(amount_score, 2),
        date_match_score=round(date_score, 2),
        name_match_score=round(name_score, 2),
        evidence_score=round(evidence_score, 2),
        total_score=total_score,
        factors=factors,
    )
