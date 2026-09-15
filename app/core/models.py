from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class ReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    PROBABLE_MATCH = "PROBABLE_MATCH"
    UNMATCHED = "UNMATCHED"
    DUPLICATE = "DUPLICATE"
    DATA_QUALITY_EXCEPTION = "DATA_QUALITY_EXCEPTION"

class ExceptionPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ReviewDecision(str, Enum):
    PENDING = "PENDING"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    OVERRIDE = "OVERRIDE"

class ContractClause(BaseModel):
    contract_id: str
    document_name: str
    page_number: int
    clause_category: str  # e.g., "PRICING", "DISCOUNT", "BILLING_TERM", "TERMINATION", "TOLERANCE"
    clause_text: str

class ContractTerms(BaseModel):
    contract_id: str
    customer_id: str
    customer_name: str
    effective_date: str  # YYYY-MM-DD
    expiry_date: str     # YYYY-MM-DD
    product_service: str
    quantity: int = 1
    unit_price: float
    currency: str = "USD"
    billing_frequency: str = "Monthly"  # Monthly, Quarterly, Annual, Milestone
    discount_percent: float = 0.0
    discount_notes: Optional[str] = None
    tax_terms: str = "Exclusive"
    payment_terms: str = "Net 30"
    tolerance_percent: float = 1.0
    tolerance_absolute: float = 50.0
    special_conditions: Optional[str] = None
    file_path: Optional[str] = None

class RawInvoice(BaseModel):
    invoice_id: str
    contract_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: str
    invoice_date: str
    billing_period: Optional[str] = None
    currency: str = "USD"
    quantity: int = 1
    unit_price: float
    discount: float = 0.0
    tax: float = 0.0
    total_amount: float
    reference_number: Optional[str] = None

class NormalizedInvoice(BaseModel):
    invoice_id: str
    contract_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: str
    clean_customer_name: str
    invoice_date: str
    parsed_date: Optional[date] = None
    billing_period: Optional[str] = None
    currency: str = "USD"
    quantity: int = 1
    unit_price: float
    discount: float = 0.0
    tax: float = 0.0
    total_amount: float
    reference_number: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)

class ConfidenceBreakdown(BaseModel):
    id_match_score: float = 0.0        # Weight: 0.30
    amount_match_score: float = 0.0    # Weight: 0.35
    date_match_score: float = 0.0      # Weight: 0.15
    name_match_score: float = 0.0      # Weight: 0.10
    evidence_score: float = 0.0        # Weight: 0.10
    total_score: float = 0.0
    factors: List[str] = Field(default_factory=list)

class ReconciliationResult(BaseModel):
    invoice_id: str
    contract_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: str
    status: ReconciliationStatus
    priority: ExceptionPriority = ExceptionPriority.LOW
    confidence_score: float
    confidence_breakdown: ConfidenceBreakdown
    
    # Financial calculations (Deterministic)
    expected_amount: float
    actual_amount: float
    variance_amount: float
    variance_percent: float
    is_within_tolerance: bool
    financial_exposure: float
    
    # Explanations & Evidence (RAG & Reasoning)
    exception_reason: str
    what_happened: str
    why_did_it_happen: str
    what_contract_says: str
    evidence_citations: List[str] = Field(default_factory=list)
    recommendation: str
    matching_methods_used: List[str] = Field(default_factory=list)
    
    # Review & Audit metadata
    review_status: ReviewDecision = ReviewDecision.PENDING
    reviewer_name: Optional[str] = None
    reviewer_comment: Optional[str] = None
    override_amount: Optional[float] = None
    reconciliation_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AuditLogEntry(BaseModel):
    id: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    invoice_id: str
    contract_id: Optional[str] = None
    action_type: str  # RECONCILE, ACCEPT, REJECT, OVERRIDE, RE-INGEST
    actor: str        # SYSTEM, AI_ENGINE, or REVIEWER_NAME
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    details: str
    evidence_citation: Optional[str] = None
