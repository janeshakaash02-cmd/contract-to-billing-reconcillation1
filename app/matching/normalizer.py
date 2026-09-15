import re
from datetime import datetime, date
from typing import Optional, Tuple
from app.core.models import RawInvoice, NormalizedInvoice

CURRENCY_MAP = {
    "$": "USD",
    "USD": "USD",
    "US DOLLAR": "USD",
    "€": "EUR",
    "EUR": "EUR",
    "EURO": "EUR",
    "₹": "INR",
    "INR": "INR",
    "RS": "INR",
    "RUPEES": "INR",
    "£": "GBP",
    "GBP": "GBP",
    "POUND": "GBP",
}

LEGAL_SUFFIXES = [
    r"\binc\b\.?",
    r"\bcorp\b\.?",
    r"\bcorporation\b",
    r"\bllc\b\.?",
    r"\bltd\b\.?",
    r"\blimited\b",
    r"\bpvt\b\.?",
    r"\bprivate\b",
    r"\bgmbh\b",
    r"\btechnologies\b",
    r"\btechnology\b",
    r"\bsolutions\b",
    r"\bservices\b",
    r"\bgroup\b",
    r"\bglobal\b",
]

def normalize_currency(currency_str: Optional[str]) -> str:
    if not currency_str:
        return "USD"
    curr_clean = currency_str.strip().upper()
    return CURRENCY_MAP.get(curr_clean, curr_clean)

def normalize_customer_name(name: Optional[str]) -> str:
    if not name:
        return ""
    cleaned = name.strip().lower()
    # Remove punctuation
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    # Remove standard legal company suffixes
    for suffix in LEGAL_SUFFIXES:
        cleaned = re.sub(suffix, " ", cleaned, flags=re.IGNORECASE)
    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def parse_flexible_date(date_str: Optional[str]) -> Tuple[Optional[str], Optional[date]]:
    if not date_str:
        return None, None
    s = date_str.strip()
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt).date()
            return dt.isoformat(), dt
        except ValueError:
            continue
    return s, None

def normalize_invoice(raw: RawInvoice) -> NormalizedInvoice:
    iso_date, parsed_dt = parse_flexible_date(raw.invoice_date)
    norm_curr = normalize_currency(raw.currency)
    clean_name = normalize_customer_name(raw.customer_name)
    clean_ref = raw.reference_number.strip().upper() if raw.reference_number else None
    clean_contract_id = raw.contract_id.strip().upper() if raw.contract_id else None
    clean_cust_id = raw.customer_id.strip().upper() if raw.customer_id else None
    
    return NormalizedInvoice(
        invoice_id=raw.invoice_id.strip().upper(),
        contract_id=clean_contract_id,
        customer_id=clean_cust_id,
        customer_name=raw.customer_name.strip(),
        clean_customer_name=clean_name,
        invoice_date=iso_date or raw.invoice_date,
        parsed_date=parsed_dt,
        billing_period=raw.billing_period.strip() if raw.billing_period else None,
        currency=norm_curr,
        quantity=max(1, int(raw.quantity)),
        unit_price=round(float(raw.unit_price), 2),
        discount=round(float(raw.discount), 2),
        tax=round(float(raw.tax), 2),
        total_amount=round(float(raw.total_amount), 2),
        reference_number=clean_ref,
        raw_data=raw.model_dump(),
    )
