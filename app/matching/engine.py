from typing import List, Optional, Dict, Any, Tuple
from app.core.models import NormalizedInvoice, ContractTerms, RawInvoice
from app.matching.normalizer import normalize_invoice
from app.matching.exact_matcher import evaluate_exact_match
from app.matching.tolerance_matcher import evaluate_tolerance_match
from app.matching.fuzzy_matcher import evaluate_fuzzy_match

class MatchingEngine:
    """
    Coordinates multi-strategy matching:
    - Exact matching (IDs, currency)
    - Tolerance matching (amounts, quantities, dates)
    - Fuzzy matching (names, descriptions)
    - Candidate contract resolution (when contract ID is missing or misspelled)
    - Duplicate detection
    """
    
    def __init__(self, contracts: List[ContractTerms]):
        self.contracts = contracts
        self.contract_map = {c.contract_id.upper(): c for c in contracts}
        self.customer_map = {c.customer_id.upper(): c for c in contracts}
        
    def resolve_contract(self, invoice: NormalizedInvoice) -> Tuple[Optional[ContractTerms], str]:
        """
        Attempts to resolve the target contract for an invoice using:
        1. Exact contract_id lookup
        2. Exact customer_id lookup
        3. Fuzzy customer name matching across all contracts
        """
        if invoice.contract_id and invoice.contract_id.upper() in self.contract_map:
            return self.contract_map[invoice.contract_id.upper()], "EXACT_CONTRACT_ID"
            
        if invoice.customer_id and invoice.customer_id.upper() in self.customer_map:
            return self.customer_map[invoice.customer_id.upper()], "EXACT_CUSTOMER_ID"
            
        # Try best fuzzy match across contracts
        best_contract = None
        best_score = 0.0
        for c in self.contracts:
            fuzzy_res = evaluate_fuzzy_match(invoice, c)
            score = fuzzy_res["name_similarity"]
            if score > best_score:
                best_score = score
                best_contract = c
                
        if best_contract and best_score >= 0.75:
            return best_contract, f"FUZZY_CUSTOMER_NAME ({int(best_score*100)}%)"
            
        return None, "NONE"

    def match(
        self,
        raw_invoice: RawInvoice,
        existing_invoices: Optional[List[RawInvoice]] = None
    ) -> Dict[str, Any]:
        """
        Executes all matching strategies for a single invoice.
        """
        norm_inv = normalize_invoice(raw_invoice)
        
        # 1. Duplicate Detection
        is_duplicate = False
        duplicate_ref = None
        if existing_invoices:
            for past_inv in existing_invoices:
                # Same invoice ID or same customer + same billing period + same amount (excluding itself)
                if past_inv.invoice_id == raw_invoice.invoice_id:
                    continue
                same_customer = (past_inv.customer_id == raw_invoice.customer_id or past_inv.customer_name.strip().lower() == raw_invoice.customer_name.strip().lower())
                same_period = bool(past_inv.billing_period and past_inv.billing_period == raw_invoice.billing_period)
                same_amount = abs(past_inv.total_amount - raw_invoice.total_amount) < 0.01
                if same_customer and same_period and same_amount:
                    is_duplicate = True
                    duplicate_ref = past_inv.invoice_id
                    break

        # 2. Resolve Contract
        contract, resolution_method = self.resolve_contract(norm_inv)
        
        # 3. Exact Matching
        exact_res = evaluate_exact_match(norm_inv, contract)
        
        # 4. Tolerance Matching
        tolerance_res = evaluate_tolerance_match(norm_inv, contract)
        
        # 5. Fuzzy Matching
        fuzzy_res = evaluate_fuzzy_match(norm_inv, contract)
        
        methods_used = []
        if resolution_method != "NONE":
            methods_used.append(f"Resolution: {resolution_method}")
        if exact_res["has_contract"]:
            methods_used.append("Exact Matching")
        methods_used.append("Tolerance & Variance Math")
        methods_used.append("Fuzzy Entity Similarity")
        
        return {
            "normalized_invoice": norm_inv,
            "contract": contract,
            "resolution_method": resolution_method,
            "is_duplicate": is_duplicate,
            "duplicate_ref": duplicate_ref,
            "exact": exact_res,
            "tolerance": tolerance_res,
            "fuzzy": fuzzy_res,
            "methods_used": methods_used,
        }
