from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from app.core.models import (
    RawInvoice,
    ContractTerms,
    ReconciliationResult,
    ReconciliationStatus,
    ExceptionPriority,
    ReviewDecision,
    AuditLogEntry,
)
from app.matching.engine import MatchingEngine
from app.matching.normalizer import normalize_invoice
from app.reconciliation.confidence import calculate_confidence_score
from app.rag.chain import get_rag_chain
from app.database.db import (
    save_reconciliation_results,
    log_audit_entry,
    get_all_invoices,
    get_all_contracts,
)

class ReconciliationEngine:
    """
    Central financial reconciliation orchestrator.
    Combines deterministic financial calculations, multi-strategy matching,
    RAG contractual evidence retrieval, explainable confidence scoring,
    and audit logging.
    """
    def __init__(self, contracts: Optional[List[ContractTerms]] = None):
        self.contracts = contracts or get_all_contracts()
        self.matching_engine = MatchingEngine(self.contracts)
        self.rag_chain = get_rag_chain()

    def reconcile_invoice(
        self,
        raw_invoice: RawInvoice,
        existing_invoices: Optional[List[RawInvoice]] = None
    ) -> ReconciliationResult:
        """
        Reconciles a single invoice against contractual terms and corporate policy.
        """
        norm_inv = normalize_invoice(raw_invoice)
        
        # 1. Data Quality Check
        if not norm_inv.customer_name or norm_inv.total_amount <= 0:
            conf = calculate_confidence_score({}, {}, {}, False, False, False)
            return ReconciliationResult(
                invoice_id=norm_inv.invoice_id,
                contract_id=norm_inv.contract_id,
                customer_id=norm_inv.customer_id,
                customer_name=norm_inv.customer_name or "UNKNOWN",
                status=ReconciliationStatus.DATA_QUALITY_EXCEPTION,
                priority=ExceptionPriority.HIGH,
                confidence_score=conf.total_score,
                confidence_breakdown=conf,
                expected_amount=0.0,
                actual_amount=norm_inv.total_amount,
                variance_amount=norm_inv.total_amount,
                variance_percent=100.0,
                is_within_tolerance=False,
                financial_exposure=norm_inv.total_amount,
                exception_reason="Data Quality Anomaly: Missing customer name or non-positive invoice total.",
                what_happened="Invoice failed input validation.",
                why_did_it_happen="Required financial or customer identifiers are empty or invalid.",
                what_contract_says="Standard billing guidelines require valid customer identity and positive billing amount.",
                evidence_citations=["System Validation Rule: DQ-001"],
                recommendation="Reject invoice or return to billing operations for correction.",
                matching_methods_used=["Data Quality Validation"],
            )

        # 2. Run Matching Engine (Deterministic + Fuzzy)
        match_data = self.matching_engine.match(raw_invoice, existing_invoices=existing_invoices)
        contract: Optional[ContractTerms] = match_data["contract"]
        exact_res = match_data["exact"]
        tolerance_res = match_data["tolerance"]
        fuzzy_res = match_data["fuzzy"]
        is_duplicate = match_data["is_duplicate"]
        duplicate_ref = match_data["duplicate_ref"]
        methods_used = match_data["methods_used"]

        # 3. Classify Financial Issue & Status
        status: ReconciliationStatus
        priority: ExceptionPriority = ExceptionPriority.LOW
        issue_type: str = "EXACT_MATCH"
        exception_reason: str = ""
        financial_exposure: float = 0.0

        if is_duplicate:
            status = ReconciliationStatus.DUPLICATE
            priority = ExceptionPriority.HIGH
            issue_type = "DUPLICATE"
            exception_reason = f"Duplicate of prior invoice {duplicate_ref}."
            financial_exposure = norm_inv.total_amount
            
        elif not contract:
            status = ReconciliationStatus.UNMATCHED
            priority = ExceptionPriority.HIGH
            issue_type = "MISSING_CONTRACT"
            exception_reason = "No matching contract could be resolved for this customer or reference."
            financial_exposure = norm_inv.total_amount
            
        elif not exact_res["currency_match"]:
            status = ReconciliationStatus.UNMATCHED
            priority = ExceptionPriority.HIGH
            issue_type = "CURRENCY_MISMATCH"
            exception_reason = f"Currency mismatch: Billed {norm_inv.currency} vs Contract {contract.currency}."
            financial_exposure = norm_inv.total_amount
            
        elif not tolerance_res["date_valid"]:
            status = ReconciliationStatus.UNMATCHED
            priority = ExceptionPriority.HIGH
            issue_type = "CONTRACT_EXPIRED"
            exception_reason = tolerance_res["date_notes"]
            financial_exposure = norm_inv.total_amount
            
        elif not tolerance_res["discount_match"] and contract.discount_percent > 0:
            status = ReconciliationStatus.UNMATCHED
            priority = ExceptionPriority.HIGH if abs(tolerance_res["variance_amount"]) >= 500 else ExceptionPriority.MEDIUM
            issue_type = "DISCOUNT_MISMATCH"
            exception_reason = f"Contractual {contract.discount_percent}% discount was not applied."
            financial_exposure = abs(tolerance_res["variance_amount"])
            
        elif not tolerance_res["quantity_match"]:
            status = ReconciliationStatus.UNMATCHED
            priority = ExceptionPriority.MEDIUM
            issue_type = "QUANTITY_MISMATCH"
            exception_reason = f"Quantity mismatch: Billed {norm_inv.quantity} units vs Contract {contract.quantity} units."
            financial_exposure = abs(tolerance_res["variance_amount"])
            
        elif not tolerance_res["is_within_tolerance"]:
            status = ReconciliationStatus.UNMATCHED
            priority = ExceptionPriority.HIGH if abs(tolerance_res["variance_amount"]) >= 1000 else ExceptionPriority.MEDIUM
            issue_type = "AMOUNT_VARIANCE"
            exception_reason = f"Amount variance of {norm_inv.currency} {abs(tolerance_res['variance_amount']):,.2f} ({tolerance_res['variance_percent']}%) exceeds tolerance."
            financial_exposure = abs(tolerance_res["variance_amount"])
            
        elif not tolerance_res["is_exact_amount"] and tolerance_res["is_within_tolerance"]:
            status = ReconciliationStatus.PROBABLE_MATCH
            priority = ExceptionPriority.LOW
            issue_type = "TOLERANCE_MATCH"
            exception_reason = f"Small amount variance ({tolerance_res['variance_percent']}%) within acceptable tolerance."
            financial_exposure = abs(tolerance_res["variance_amount"])
            
        elif match_data["resolution_method"].startswith("FUZZY"):
            status = ReconciliationStatus.PROBABLE_MATCH
            priority = ExceptionPriority.LOW
            issue_type = "FUZZY_NAME_MATCH"
            exception_reason = f"Customer matched via fuzzy name resolution: {fuzzy_res['notes']}"
            financial_exposure = 0.0
            
        else:
            status = ReconciliationStatus.MATCHED
            priority = ExceptionPriority.LOW
            issue_type = "EXACT_MATCH"
            exception_reason = "Fully compliant with contractual terms."
            financial_exposure = 0.0

        # 4. Generate RAG Explanations & Citations
        explanation_data = self.rag_chain.generate_discrepancy_explanation(
            invoice_id=norm_inv.invoice_id,
            customer_name=norm_inv.customer_name,
            contract_id=contract.contract_id if contract else None,
            expected_amount=tolerance_res["expected_amount"],
            actual_amount=norm_inv.total_amount,
            variance_amount=tolerance_res["variance_amount"],
            variance_percent=tolerance_res["variance_percent"],
            currency=norm_inv.currency,
            issue_type=issue_type,
            contract_notes=contract.special_conditions if contract else None,
        )
        
        has_citations = bool(explanation_data["evidence_citations"])
        
        # 5. Compute Explainable Confidence Score
        confidence_breakdown = calculate_confidence_score(
            exact_res=exact_res,
            tolerance_res=tolerance_res,
            fuzzy_res=fuzzy_res,
            has_evidence=has_citations,
            is_duplicate=is_duplicate,
            has_contract=bool(contract),
        )

        return ReconciliationResult(
            invoice_id=norm_inv.invoice_id,
            contract_id=contract.contract_id if contract else norm_inv.contract_id,
            customer_id=contract.customer_id if contract else norm_inv.customer_id,
            customer_name=norm_inv.customer_name,
            status=status,
            priority=priority,
            confidence_score=confidence_breakdown.total_score,
            confidence_breakdown=confidence_breakdown,
            expected_amount=tolerance_res["expected_amount"],
            actual_amount=norm_inv.total_amount,
            variance_amount=tolerance_res["variance_amount"],
            variance_percent=tolerance_res["variance_percent"],
            is_within_tolerance=tolerance_res["is_within_tolerance"],
            financial_exposure=round(financial_exposure, 2),
            exception_reason=exception_reason,
            what_happened=explanation_data["what_happened"],
            why_did_it_happen=explanation_data["why_did_it_happen"],
            what_contract_says=explanation_data["what_contract_says"],
            evidence_citations=explanation_data["evidence_citations"],
            recommendation=explanation_data["recommendation"],
            matching_methods_used=methods_used,
            review_status=ReviewDecision.PENDING if status != ReconciliationStatus.MATCHED else ReviewDecision.ACCEPT,
            reconciliation_timestamp=datetime.utcnow().isoformat(),
        )

    def reconcile_batch(
        self,
        invoices: List[RawInvoice],
        persist_to_db: bool = True
    ) -> List[ReconciliationResult]:
        """
        Reconciles a batch of invoices and saves results and audit entries to SQLite.
        """
        results: List[ReconciliationResult] = []
        processed_invoices: List[RawInvoice] = []

        for inv in invoices:
            res = self.reconcile_invoice(inv, existing_invoices=processed_invoices)
            results.append(res)
            processed_invoices.append(inv)
            
            if persist_to_db:
                # Log audit entry
                citation = res.evidence_citations[0] if res.evidence_citations else "System Calculation"
                log_audit_entry(AuditLogEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    invoice_id=res.invoice_id,
                    contract_id=res.contract_id,
                    action_type="RECONCILE",
                    actor="AI_ENGINE",
                    previous_status=None,
                    new_status=res.status.value,
                    details=f"Automated reconciliation: {res.status.value} (Confidence: {int(res.confidence_score*100)}%). Reason: {res.exception_reason}",
                    evidence_citation=citation,
                ))
                
        if persist_to_db:
            save_reconciliation_results(results)
            
        return results
