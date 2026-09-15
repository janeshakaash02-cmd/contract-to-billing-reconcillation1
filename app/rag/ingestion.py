import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pymupdf  # PyMuPDF

from app.core.models import ContractClause

CLAUSE_CATEGORIES = {
    r"\b(price|pricing|rate|fee|cost|subscription|amount)\b": "PRICING",
    r"\b(discount|rebate|concession|promotional)\b": "DISCOUNT",
    r"\b(billing|frequency|cycle|invoice|invoicing|cadence)\b": "BILLING_TERM",
    r"\b(payment|net\s*30|net\s*15|due|penalty|late)\b": "PAYMENT_TERMS",
    r"\b(tolerance|variance|threshold|margin)\b": "TOLERANCE",
    r"\b(term|duration|effective|expiry|expiration|renewal|termination)\b": "TERM_AND_EXPIRY",
    r"\b(scope|service|product|deliverable|seat|license)\b": "SCOPE_OF_WORK",
    r"\b(tax|vat|gst|withholding)\b": "TAX_TERMS",
}

def detect_clause_category(text: str) -> str:
    text_lower = text.lower()
    for pattern, category in CLAUSE_CATEGORIES.items():
        if re.search(pattern, text_lower):
            return category
    return "GENERAL_TERMS"

def extract_clauses_from_pdf(
    pdf_path: str,
    contract_id: str,
    chunk_size: int = 500,
    chunk_overlap: int = 80
) -> List[ContractClause]:
    """
    Extracts text page-by-page from a PDF using PyMuPDF, chunks the text,
    and attaches page numbers and clause categories.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF document not found: {pdf_path}")
        
    doc = pymupdf.open(str(path))
    clauses: List[ContractClause] = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1
        page_text = page.get_text("text").strip()
        if not page_text:
            continue
            
        # Split page into logical paragraphs/sections
        paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
        
        current_chunk = ""
        for p in paragraphs:
            if len(current_chunk) + len(p) < chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + p
            else:
                if current_chunk:
                    cat = detect_clause_category(current_chunk)
                    clauses.append(ContractClause(
                        contract_id=contract_id,
                        document_name=path.name,
                        page_number=page_num,
                        clause_category=cat,
                        clause_text=current_chunk,
                    ))
                current_chunk = p
                
        if current_chunk:
            cat = detect_clause_category(current_chunk)
            clauses.append(ContractClause(
                contract_id=contract_id,
                document_name=path.name,
                page_number=page_num,
                clause_category=cat,
                clause_text=current_chunk,
            ))
            
    doc.close()
    return clauses

def extract_clauses_from_text(
    text: str,
    doc_name: str,
    contract_id: str = "POLICY",
    page_number: int = 1
) -> List[ContractClause]:
    """
    Extracts clauses from raw text or policy documents.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    clauses: List[ContractClause] = []
    
    for p in paragraphs:
        if len(p) < 20:
            continue
        cat = detect_clause_category(p)
        clauses.append(ContractClause(
            contract_id=contract_id,
            document_name=doc_name,
            page_number=page_number,
            clause_category=cat,
            clause_text=p,
        ))
    return clauses
