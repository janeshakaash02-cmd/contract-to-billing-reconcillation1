import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.config import DB_PATH, MANUAL_MINUTES_PER_INVOICE, FINANCE_HOURLY_COST
from app.core.models import (
    ContractTerms,
    RawInvoice,
    ReconciliationResult,
    ReconciliationStatus,
    ExceptionPriority,
    ReviewDecision,
    ConfidenceBreakdown,
    AuditLogEntry,
)

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Contracts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contracts (
        contract_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        effective_date TEXT NOT NULL,
        expiry_date TEXT NOT NULL,
        product_service TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        currency TEXT NOT NULL,
        billing_frequency TEXT NOT NULL,
        discount_percent REAL DEFAULT 0.0,
        discount_notes TEXT,
        tax_terms TEXT,
        payment_terms TEXT,
        tolerance_percent REAL DEFAULT 1.0,
        tolerance_absolute REAL DEFAULT 50.0,
        special_conditions TEXT,
        file_path TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Invoices table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id TEXT PRIMARY KEY,
        contract_id TEXT,
        customer_id TEXT,
        customer_name TEXT NOT NULL,
        invoice_date TEXT NOT NULL,
        billing_period TEXT,
        currency TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        discount REAL DEFAULT 0.0,
        tax REAL DEFAULT 0.0,
        total_amount REAL NOT NULL,
        reference_number TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Reconciliation Results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reconciliation_results (
        invoice_id TEXT PRIMARY KEY,
        contract_id TEXT,
        customer_id TEXT,
        customer_name TEXT NOT NULL,
        status TEXT NOT NULL,
        priority TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        confidence_json TEXT,
        expected_amount REAL NOT NULL,
        actual_amount REAL NOT NULL,
        variance_amount REAL NOT NULL,
        variance_percent REAL NOT NULL,
        is_within_tolerance INTEGER NOT NULL,
        financial_exposure REAL NOT NULL,
        exception_reason TEXT,
        what_happened TEXT,
        why_did_it_happen TEXT,
        what_contract_says TEXT,
        evidence_citations TEXT,
        recommendation TEXT,
        matching_methods TEXT,
        review_status TEXT DEFAULT 'PENDING',
        reviewer_name TEXT,
        reviewer_comment TEXT,
        override_amount REAL,
        reconciliation_timestamp TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Audit Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        invoice_id TEXT NOT NULL,
        contract_id TEXT,
        action_type TEXT NOT NULL,
        actor TEXT NOT NULL,
        previous_status TEXT,
        new_status TEXT,
        details TEXT NOT NULL,
        evidence_citation TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def reset_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS contracts")
    cursor.execute("DROP TABLE IF EXISTS invoices")
    cursor.execute("DROP TABLE IF EXISTS reconciliation_results")
    cursor.execute("DROP TABLE IF EXISTS audit_logs")
    conn.commit()
    conn.close()
    init_db()

def save_contracts(contracts: List[ContractTerms]):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    for c in contracts:
        cursor.execute("""
        INSERT OR REPLACE INTO contracts (
            contract_id, customer_id, customer_name, effective_date, expiry_date,
            product_service, quantity, unit_price, currency, billing_frequency,
            discount_percent, discount_notes, tax_terms, payment_terms,
            tolerance_percent, tolerance_absolute, special_conditions, file_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c.contract_id, c.customer_id, c.customer_name, c.effective_date, c.expiry_date,
            c.product_service, c.quantity, c.unit_price, c.currency, c.billing_frequency,
            c.discount_percent, c.discount_notes, c.tax_terms, c.payment_terms,
            c.tolerance_percent, c.tolerance_absolute, c.special_conditions, c.file_path
        ))
    conn.commit()
    conn.close()

def get_all_contracts() -> List[ContractTerms]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contracts ORDER BY contract_id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [
        ContractTerms(
            contract_id=r["contract_id"],
            customer_id=r["customer_id"],
            customer_name=r["customer_name"],
            effective_date=r["effective_date"],
            expiry_date=r["expiry_date"],
            product_service=r["product_service"],
            quantity=r["quantity"],
            unit_price=r["unit_price"],
            currency=r["currency"],
            billing_frequency=r["billing_frequency"],
            discount_percent=r["discount_percent"],
            discount_notes=r["discount_notes"],
            tax_terms=r["tax_terms"] or "Exclusive",
            payment_terms=r["payment_terms"] or "Net 30",
            tolerance_percent=r["tolerance_percent"],
            tolerance_absolute=r["tolerance_absolute"],
            special_conditions=r["special_conditions"],
            file_path=r["file_path"],
        )
        for r in rows
    ]

def get_contract(contract_id: str) -> Optional[ContractTerms]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contracts WHERE contract_id = ?", (contract_id,))
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return ContractTerms(
        contract_id=r["contract_id"],
        customer_id=r["customer_id"],
        customer_name=r["customer_name"],
        effective_date=r["effective_date"],
        expiry_date=r["expiry_date"],
        product_service=r["product_service"],
        quantity=r["quantity"],
        unit_price=r["unit_price"],
        currency=r["currency"],
        billing_frequency=r["billing_frequency"],
        discount_percent=r["discount_percent"],
        discount_notes=r["discount_notes"],
        tax_terms=r["tax_terms"] or "Exclusive",
        payment_terms=r["payment_terms"] or "Net 30",
        tolerance_percent=r["tolerance_percent"],
        tolerance_absolute=r["tolerance_absolute"],
        special_conditions=r["special_conditions"],
        file_path=r["file_path"],
    )

def save_invoices(invoices: List[RawInvoice]):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    for inv in invoices:
        cursor.execute("""
        INSERT OR REPLACE INTO invoices (
            invoice_id, contract_id, customer_id, customer_name, invoice_date,
            billing_period, currency, quantity, unit_price, discount, tax,
            total_amount, reference_number
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inv.invoice_id, inv.contract_id, inv.customer_id, inv.customer_name,
            inv.invoice_date, inv.billing_period, inv.currency, inv.quantity,
            inv.unit_price, inv.discount, inv.tax, inv.total_amount, inv.reference_number
        ))
    conn.commit()
    conn.close()

def get_all_invoices() -> List[RawInvoice]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices ORDER BY invoice_id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [
        RawInvoice(
            invoice_id=r["invoice_id"],
            contract_id=r["contract_id"],
            customer_id=r["customer_id"],
            customer_name=r["customer_name"],
            invoice_date=r["invoice_date"],
            billing_period=r["billing_period"],
            currency=r["currency"],
            quantity=r["quantity"],
            unit_price=r["unit_price"],
            discount=r["discount"],
            tax=r["tax"],
            total_amount=r["total_amount"],
            reference_number=r["reference_number"],
        )
        for r in rows
    ]

def save_reconciliation_results(results: List[ReconciliationResult]):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    for res in results:
        cursor.execute("""
        INSERT OR REPLACE INTO reconciliation_results (
            invoice_id, contract_id, customer_id, customer_name, status, priority,
            confidence_score, confidence_json, expected_amount, actual_amount,
            variance_amount, variance_percent, is_within_tolerance, financial_exposure,
            exception_reason, what_happened, why_did_it_happen, what_contract_says,
            evidence_citations, recommendation, matching_methods, review_status,
            reviewer_name, reviewer_comment, override_amount, reconciliation_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            res.invoice_id,
            res.contract_id,
            res.customer_id,
            res.customer_name,
            res.status.value,
            res.priority.value,
            res.confidence_score,
            res.confidence_breakdown.model_dump_json(),
            res.expected_amount,
            res.actual_amount,
            res.variance_amount,
            res.variance_percent,
            1 if res.is_within_tolerance else 0,
            res.financial_exposure,
            res.exception_reason,
            res.what_happened,
            res.why_did_it_happen,
            res.what_contract_says,
            json.dumps(res.evidence_citations),
            res.recommendation,
            json.dumps(res.matching_methods_used),
            res.review_status.value,
            res.reviewer_name,
            res.reviewer_comment,
            res.override_amount,
            res.reconciliation_timestamp,
        ))
    conn.commit()
    conn.close()

def _row_to_reconciliation_result(r: sqlite3.Row) -> ReconciliationResult:
    conf_breakdown_raw = json.loads(r["confidence_json"]) if r["confidence_json"] else {}
    conf_breakdown = ConfidenceBreakdown(**conf_breakdown_raw) if conf_breakdown_raw else ConfidenceBreakdown()
    
    citations = json.loads(r["evidence_citations"]) if r["evidence_citations"] else []
    methods = json.loads(r["matching_methods"]) if r["matching_methods"] else []
    
    return ReconciliationResult(
        invoice_id=r["invoice_id"],
        contract_id=r["contract_id"],
        customer_id=r["customer_id"],
        customer_name=r["customer_name"],
        status=ReconciliationStatus(r["status"]),
        priority=ExceptionPriority(r["priority"]),
        confidence_score=r["confidence_score"],
        confidence_breakdown=conf_breakdown,
        expected_amount=r["expected_amount"],
        actual_amount=r["actual_amount"],
        variance_amount=r["variance_amount"],
        variance_percent=r["variance_percent"],
        is_within_tolerance=bool(r["is_within_tolerance"]),
        financial_exposure=r["financial_exposure"],
        exception_reason=r["exception_reason"] or "",
        what_happened=r["what_happened"] or "",
        why_did_it_happen=r["why_did_it_happen"] or "",
        what_contract_says=r["what_contract_says"] or "",
        evidence_citations=citations,
        recommendation=r["recommendation"] or "",
        matching_methods_used=methods,
        review_status=ReviewDecision(r["review_status"]) if r["review_status"] else ReviewDecision.PENDING,
        reviewer_name=r["reviewer_name"],
        reviewer_comment=r["reviewer_comment"],
        override_amount=r["override_amount"],
        reconciliation_timestamp=r["reconciliation_timestamp"] or "",
    )

def get_reconciliation_results(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    review_status_filter: Optional[str] = None
) -> List[ReconciliationResult]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM reconciliation_results WHERE 1=1"
    params = []
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if priority_filter:
        query += " AND priority = ?"
        params.append(priority_filter)
    if review_status_filter:
        query += " AND review_status = ?"
        params.append(review_status_filter)
        
    query += " ORDER BY CASE priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END, financial_exposure DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_reconciliation_result(r) for r in rows]

def get_reconciliation_result(invoice_id: str) -> Optional[ReconciliationResult]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reconciliation_results WHERE invoice_id = ?", (invoice_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_reconciliation_result(row)

def update_review_decision(
    invoice_id: str,
    decision: ReviewDecision,
    reviewer_name: str,
    comment: str,
    override_amount: Optional[float] = None
) -> bool:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current status
    cursor.execute("SELECT status, contract_id, review_status FROM reconciliation_results WHERE invoice_id = ?", (invoice_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
        
    prev_status = row["status"]
    contract_id = row["contract_id"]
    
    # Determine new status
    new_status = prev_status
    if decision == ReviewDecision.ACCEPT:
        new_status = ReconciliationStatus.MATCHED.value
    elif decision == ReviewDecision.REJECT:
        new_status = ReconciliationStatus.UNMATCHED.value
    elif decision == ReviewDecision.OVERRIDE:
        new_status = ReconciliationStatus.MATCHED.value
        
    cursor.execute("""
    UPDATE reconciliation_results
    SET review_status = ?,
        reviewer_name = ?,
        reviewer_comment = ?,
        override_amount = ?,
        status = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE invoice_id = ?
    """, (
        decision.value,
        reviewer_name,
        comment,
        override_amount,
        new_status,
        invoice_id
    ))
    
    # Write to audit log
    action_type = decision.value
    details = f"Reviewer '{reviewer_name}' set decision to {decision.value}. Comment: '{comment}'."
    if override_amount is not None:
        details += f" Override amount set to {override_amount}."
        
    cursor.execute("""
    INSERT INTO audit_logs (
        timestamp, invoice_id, contract_id, action_type, actor, previous_status, new_status, details, evidence_citation
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        invoice_id,
        contract_id,
        action_type,
        reviewer_name,
        prev_status,
        new_status,
        details,
        f"Human review action by {reviewer_name}"
    ))
    
    conn.commit()
    conn.close()
    return True

def batch_update_review_decisions(
    invoice_ids: List[str],
    decision: ReviewDecision,
    reviewer_name: str,
    comment: str
) -> int:
    """Updates review decisions for multiple invoices and logs immutable audit entries."""
    if not invoice_ids:
        return 0
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    updated_count = 0
    now_ts = datetime.utcnow().isoformat()
    
    for inv_id in invoice_ids:
        cursor.execute("SELECT status, contract_id FROM reconciliation_results WHERE invoice_id = ?", (inv_id,))
        row = cursor.fetchone()
        if not row:
            continue
            
        prev_status = row["status"]
        contract_id = row["contract_id"]
        
        new_status = prev_status
        if decision == ReviewDecision.ACCEPT:
            new_status = ReconciliationStatus.MATCHED.value
        elif decision == ReviewDecision.REJECT:
            new_status = ReconciliationStatus.UNMATCHED.value
            
        cursor.execute("""
        UPDATE reconciliation_results
        SET review_status = ?,
            reviewer_name = ?,
            reviewer_comment = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE invoice_id = ?
        """, (
            decision.value,
            reviewer_name,
            comment,
            new_status,
            inv_id
        ))
        
        cursor.execute("""
        INSERT INTO audit_logs (
            timestamp, invoice_id, contract_id, action_type, actor, previous_status, new_status, details, evidence_citation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now_ts,
            inv_id,
            contract_id,
            f"BATCH_{decision.value}",
            reviewer_name,
            prev_status,
            new_status,
            f"Batch clearance by '{reviewer_name}': {comment}",
            "Batch Triage Action"
        ))
        updated_count += 1
        
    conn.commit()
    conn.close()
    return updated_count

def log_audit_entry(entry: AuditLogEntry):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO audit_logs (
        timestamp, invoice_id, contract_id, action_type, actor, previous_status, new_status, details, evidence_citation
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entry.timestamp,
        entry.invoice_id,
        entry.contract_id,
        entry.action_type,
        entry.actor,
        entry.previous_status,
        entry.new_status,
        entry.details,
        entry.evidence_citation
    ))
    conn.commit()
    conn.close()

def get_audit_logs(invoice_id: Optional[str] = None, limit: int = 150) -> List[AuditLogEntry]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    if invoice_id:
        cursor.execute("SELECT * FROM audit_logs WHERE invoice_id = ? ORDER BY id DESC LIMIT ?", (invoice_id, limit))
    else:
        cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [
        AuditLogEntry(
            id=r["id"],
            timestamp=r["timestamp"],
            invoice_id=r["invoice_id"],
            contract_id=r["contract_id"],
            action_type=r["action_type"],
            actor=r["actor"],
            previous_status=r["previous_status"],
            new_status=r["new_status"],
            details=r["details"],
            evidence_citation=r["evidence_citation"],
        )
        for r in rows
    ]

def get_dashboard_summary_metrics() -> Dict[str, Any]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM invoices")
    total_invoices = cursor.fetchone()["total"]
    
    cursor.execute("SELECT status, COUNT(*) as cnt, SUM(financial_exposure) as exposure FROM reconciliation_results GROUP BY status")
    status_counts = {r["status"]: r["cnt"] for r in cursor.fetchall()}
    
    cursor.execute("SELECT SUM(financial_exposure) as total_exposure FROM reconciliation_results WHERE status != 'MATCHED'")
    total_exposure = cursor.fetchone()["total_exposure"] or 0.0
    
    matched = status_counts.get(ReconciliationStatus.MATCHED.value, 0)
    probable = status_counts.get(ReconciliationStatus.PROBABLE_MATCH.value, 0)
    unmatched = status_counts.get(ReconciliationStatus.UNMATCHED.value, 0)
    duplicate = status_counts.get(ReconciliationStatus.DUPLICATE.value, 0)
    data_quality = status_counts.get(ReconciliationStatus.DATA_QUALITY_EXCEPTION.value, 0)
    
    total_reconciled = matched + probable + unmatched + duplicate + data_quality
    auto_match_rate = (matched / total_reconciled * 100.0) if total_reconciled > 0 else 0.0
    
    cursor.execute("SELECT COUNT(*) as high_pri FROM reconciliation_results WHERE priority = 'HIGH' AND review_status = 'PENDING'")
    high_priority_exceptions = cursor.fetchone()["high_pri"]
    
    # Operational metrics
    hours_saved = (matched * MANUAL_MINUTES_PER_INVOICE) / 60.0
    cost_saved = hours_saved * FINANCE_HOURLY_COST
    
    cursor.execute("""
    SELECT exception_reason, COUNT(*) as cnt, SUM(financial_exposure) as exposure
    FROM reconciliation_results 
    WHERE status != 'MATCHED' AND exception_reason IS NOT NULL AND exception_reason != ''
    GROUP BY exception_reason
    ORDER BY cnt DESC LIMIT 5
    """)
    top_reasons = [{"reason": r["exception_reason"], "count": r["cnt"], "exposure": r["exposure"] or 0.0} for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_invoices": total_invoices,
        "total_reconciled": total_reconciled,
        "matched": matched,
        "probable_matches": probable,
        "unmatched": unmatched,
        "duplicates": duplicate,
        "data_quality_exceptions": data_quality,
        "auto_match_rate": round(auto_match_rate, 1),
        "total_financial_exposure": round(total_exposure, 2),
        "high_priority_exceptions": high_priority_exceptions,
        "hours_saved": round(hours_saved, 1),
        "cost_saved": round(cost_saved, 2),
        "top_reasons": top_reasons,
    }
