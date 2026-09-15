import os
import csv
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.config import DATA_DIR, CONTRACTS_DIR, INVOICES_DIR, POLICIES_DIR
from app.core.models import ContractTerms, RawInvoice
from app.database.db import save_contracts, save_invoices, reset_database
from app.rag.ingestion import extract_clauses_from_pdf, extract_clauses_from_text
from app.rag.vector_store import get_vector_store

CONTRACT_TEMPLATES = [
    {
        "contract_id": "CTR-1001",
        "customer_id": "CUST-201",
        "customer_name": "Nexus Cloud Technologies Inc.",
        "product_service": "Enterprise Cloud Platform Tier 3",
        "quantity": 100,
        "unit_price": 100.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 10.0,
        "discount_notes": "10% promotional subscription discount valid for all invoices in first year.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "payment_terms": "Net 30",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 50.0,
        "special_conditions": "The customer is entitled to a 10% discount on the monthly software subscription. Standard monthly gross is $10,000.00, discounted to $9,000.00 net. Variance tolerance is 1.0%."
    },
    {
        "contract_id": "CTR-1002",
        "customer_id": "CUST-202",
        "customer_name": "Meridian Logistics Corp",
        "product_service": "Fleet Telematics & Route Optimization Engine",
        "quantity": 50,
        "unit_price": 150.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 0.0,
        "discount_notes": "Standard list pricing. No promotional discount authorized.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "payment_terms": "Net 30",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 50.0,
        "special_conditions": "Fixed baseline fee of $7,500.00 monthly for up to 50 monitored vehicles. Additional vehicles billed at $150 per vehicle."
    },
    {
        "contract_id": "CTR-1003",
        "customer_id": "CUST-203",
        "customer_name": "Apex Health Solutions LLC",
        "product_service": "HIPAA Interoperability Gateway & Data Pipeline",
        "quantity": 1,
        "unit_price": 18000.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 5.0,
        "discount_notes": "5% healthcare sector volume discount applied at invoice generation.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-06-30",
        "payment_terms": "Net 15",
        "tax_terms": "Exclusive",
        "tolerance_percent": 0.5,
        "tolerance_absolute": 100.0,
        "special_conditions": "Monthly base subscription is $18,000.00 less 5% discount ($900.00) resulting in net $17,100.00. Term ends on June 30, 2025."
    },
    {
        "contract_id": "CTR-1004",
        "customer_id": "CUST-204",
        "customer_name": "Vortex Media Global",
        "product_service": "Content Delivery Network & Streaming Infrastructure",
        "quantity": 1,
        "unit_price": 12500.0,
        "currency": "EUR",
        "billing_frequency": "Monthly",
        "discount_percent": 0.0,
        "discount_notes": "Euro denominated billing. Any foreign exchange conversions are disallowed.",
        "effective_date": "2025-02-01",
        "expiry_date": "2026-01-31",
        "payment_terms": "Net 45",
        "tax_terms": "Inclusive of VAT",
        "tolerance_percent": 1.5,
        "tolerance_absolute": 75.0,
        "special_conditions": "Invoices must be submitted strictly in Euros (EUR) at €12,500.00. USD submissions will be rejected automatically."
    },
    {
        "contract_id": "CTR-1005",
        "customer_id": "CUST-205",
        "customer_name": "Horizon Financial Partners",
        "product_service": "Algorithmic Risk Assessment API Engine",
        "quantity": 20,
        "unit_price": 1200.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 15.0,
        "discount_notes": "15% early adopter discount for first 12 billing cycles.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "payment_terms": "Net 30",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 50.0,
        "special_conditions": "Gross monthly billing of 20 seats @ $1,200 = $24,000.00. Less 15% ($3,600.00) yields net monthly $20,400.00."
    },
    {
        "contract_id": "CTR-1006",
        "customer_id": "CUST-206",
        "customer_name": "Zenith Retail Systems Ltd",
        "product_service": "Omnichannel Point-of-Sale Integration",
        "quantity": 250,
        "unit_price": 40.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 0.0,
        "discount_notes": "Volume tier fixed pricing.",
        "effective_date": "2025-03-01",
        "expiry_date": "2026-02-28",
        "payment_terms": "Net 30",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 50.0,
        "special_conditions": "250 register licenses at $40.00 per unit totaling $10,000.00 monthly. Tolerance is 1.0%."
    },
    {
        "contract_id": "CTR-1007",
        "customer_id": "CUST-207",
        "customer_name": "Bharat Data Analytics Pvt Ltd",
        "product_service": "Big Data ETL & Warehousing Cloud Cluster",
        "quantity": 1,
        "unit_price": 500000.0,
        "currency": "INR",
        "billing_frequency": "Monthly",
        "discount_percent": 10.0,
        "discount_notes": "10% domestic partner discount applied to base service fee.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "payment_terms": "Net 30",
        "tax_terms": "GST 18% Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 2500.0,
        "special_conditions": "Monthly base fee ₹500,000. Less 10% discount (₹50,000) = ₹450,000 net monthly subscription."
    },
    {
        "contract_id": "CTR-1008",
        "customer_id": "CUST-208",
        "customer_name": "Starlight Cyber Defense Corp",
        "product_service": "SOC-as-a-Service & Managed EDR 24/7",
        "quantity": 1,
        "unit_price": 14000.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 0.0,
        "discount_notes": "Flat retainership.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-05-31",
        "payment_terms": "Net 15",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 50.0,
        "special_conditions": "Contract expires strictly on May 31, 2025. Any invoice dated after May 31, 2025 requires signed Addendum B."
    },
    {
        "contract_id": "CTR-1009",
        "customer_id": "CUST-209",
        "customer_name": "Beacon Renewable Energy Group",
        "product_service": "Solar SCADA Telemetry & Inverter Monitoring",
        "quantity": 80,
        "unit_price": 125.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 8.0,
        "discount_notes": "8% clean energy cooperative incentive discount.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "payment_terms": "Net 30",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 50.0,
        "special_conditions": "80 site units @ $125 = $10,000 gross. With 8% rebate ($800.00), monthly net invoice amount is $9,200.00."
    },
    {
        "contract_id": "CTR-1010",
        "customer_id": "CUST-210",
        "customer_name": "Titan Heavy Industries Inc.",
        "product_service": "Predictive Maintenance IoT Sensor Platform",
        "quantity": 1,
        "unit_price": 32000.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 0.0,
        "discount_notes": "None.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "payment_terms": "Net 60",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 100.0,
        "special_conditions": "Monthly fee of $32,000.00. High-value enterprise contract requiring controller sign-off for variances > $100."
    },
    {
        "contract_id": "CTR-1011",
        "customer_id": "CUST-211",
        "customer_name": "Kensington Financial Software Ltd",
        "product_service": "Regulatory Compliance Reporting Suite",
        "quantity": 1,
        "unit_price": 9500.0,
        "currency": "GBP",
        "billing_frequency": "Monthly",
        "discount_percent": 5.0,
        "discount_notes": "5% financial services consortium discount.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "payment_terms": "Net 30",
        "tax_terms": "VAT 20% Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 50.0,
        "special_conditions": "Base monthly fee £9,500.00 less 5% (£475.00) = £9,025.00 net monthly. Invoices must be submitted in GBP."
    },
    {
        "contract_id": "CTR-1012",
        "customer_id": "CUST-212",
        "customer_name": "OmniHealth Diagnostics Inc.",
        "product_service": "Genomics Sequencing Analytics Pipeline",
        "quantity": 40,
        "unit_price": 350.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 0.0,
        "discount_notes": "Standard clinical tier.",
        "effective_date": "2025-02-01",
        "expiry_date": "2026-01-31",
        "payment_terms": "Net 30",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 50.0,
        "special_conditions": "Fixed compute allocation of 40 batch slots @ $350 = $14,000.00 monthly."
    },
    {
        "contract_id": "CTR-1013",
        "customer_id": "CUST-213",
        "customer_name": "Pioneer Autonomous Systems Corp",
        "product_service": "Robotics Fleet Simulation Virtual Sandbox",
        "quantity": 1,
        "unit_price": 22000.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 12.0,
        "discount_notes": "12% academic/research partnership concession.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "payment_terms": "Net 30",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 100.0,
        "special_conditions": "Gross monthly rate $22,000.00 with 12% discount ($2,640.00) net $19,360.00."
    },
    {
        "contract_id": "CTR-1014",
        "customer_id": "CUST-214",
        "customer_name": "Silverline Telecom Solutions",
        "product_service": "VoIP SIP Trunking & Global Routing Mesh",
        "quantity": 500,
        "unit_price": 16.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 0.0,
        "discount_notes": "Carrier wholesale rate.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "payment_terms": "Net 15",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 50.0,
        "special_conditions": "500 concurrent channel trunks @ $16.00 = $8,000.00 monthly."
    },
    {
        "contract_id": "CTR-1015",
        "customer_id": "CUST-215",
        "customer_name": "Crestview Real Estate Asset Mgmt",
        "product_service": "Smart Commercial Building Energy Optimization",
        "quantity": 1,
        "unit_price": 11500.0,
        "currency": "USD",
        "billing_frequency": "Monthly",
        "discount_percent": 6.0,
        "discount_notes": "6% portfolio energy reduction credit.",
        "effective_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "payment_terms": "Net 30",
        "tax_terms": "Exclusive",
        "tolerance_percent": 1.0,
        "tolerance_absolute": 50.0,
        "special_conditions": "Base monthly retainer $11,500.00 with 6% credit ($690.00) net $10,810.00."
    },
]

def build_pdf_contract(contract: Dict[str, Any], output_path: str):
    """
    Generates a realistic multi-page PDF contract using ReportLab.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ContractTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=14
    )
    h2_style = ParagraphStyle(
        'ContractH2',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'ContractBody',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155")
    )
    bold_body = ParagraphStyle(
        'ContractBold',
        parent=body_style,
        fontName="Helvetica-Bold"
    )
    
    story = []
    
    # Header
    story.append(Paragraph(f"MASTER SERVICES AGREEMENT", title_style))
    story.append(Paragraph(f"<b>Agreement Reference:</b> {contract['contract_id']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Date:</b> {contract['effective_date']}", body_style))
    story.append(Spacer(1, 10))
    
    # Parties Table
    parties_data = [
        [Paragraph("<b>SERVICE PROVIDER</b>", bold_body), Paragraph("<b>CLIENT / CUSTOMER</b>", bold_body)],
        [
            Paragraph("Enterprise AI Solutions Inc.<br/>100 Innovation Way, Suite 400<br/>San Francisco, CA 94105", body_style),
            Paragraph(f"<b>{contract['customer_name']}</b><br/>Customer ID: {contract['customer_id']}<br/>Authorized Finance Department", body_style)
        ]
    ]
    t = Table(parties_data, colWidths=[260, 260])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    
    # Section 1: Scope of Services
    story.append(Paragraph("1. SCOPE OF SERVICES & SUBSCRIPTION", h2_style))
    story.append(Paragraph(
        f"The Service Provider shall provide the Client with continuous access to <b>{contract['product_service']}</b>. "
        f"This agreement entitles the Client to an allocated capacity of <b>{contract['quantity']} unit(s) / seat(s)</b>. "
        f"All access rights and service levels are governed by the operational specifications outlined herein.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    # Section 2: Pricing & Payment Terms
    story.append(Paragraph("2. PRICING, FEES & BILLING CADENCE", h2_style))
    story.append(Paragraph(
        f"2.1 <b>Base Fee:</b> The agreed unit price is <b>{contract['currency']} {contract['unit_price']:,.2f}</b> per unit, "
        f"calculated across the baseline quantity of {contract['quantity']} units, resulting in a scheduled baseline of "
        f"<b>{contract['currency']} {(contract['quantity'] * contract['unit_price']):,.2f}</b> per billing period.<br/>"
        f"2.2 <b>Billing Cadence:</b> Invoicing shall occur on a <b>{contract['billing_frequency']}</b> basis.<br/>"
        f"2.3 <b>Payment Terms:</b> Undisputed invoices are payable under <b>{contract['payment_terms']}</b> from invoice receipt.<br/>"
        f"2.4 <b>Taxation:</b> Fees are {contract['tax_terms']} of applicable local sales taxes, VAT, or withholding taxes.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    # Section 3: Discounts & Rebates
    story.append(Paragraph("3. DISCOUNT TERMS & SPECIAL CONCESSIONS", h2_style))
    disc_text = (
        f"The Client is entitled to an authorized contractual discount of <b>{contract['discount_percent']}%</b>. "
        f"<i>Notes on concession:</i> {contract['discount_notes']} "
        f"Any invoice omitting this contractual discount shall be considered non-compliant."
        if contract['discount_percent'] > 0 else
        "No promotional discount, rebate, or concessions are applicable under this agreement. Billing shall proceed at standard list rates."
    )
    story.append(Paragraph(disc_text, body_style))
    story.append(Spacer(1, 8))
    
    # Page 2 content
    story.append(PageBreak())
    story.append(Paragraph("MASTER SERVICES AGREEMENT (CONTINUED)", title_style))
    story.append(Paragraph(f"<b>Agreement Reference:</b> {contract['contract_id']} &nbsp;&nbsp;|&nbsp;&nbsp; Page 2", body_style))
    story.append(Spacer(1, 10))
    
    # Section 4: Term & Termination
    story.append(Paragraph("4. TERM, EXPIRATION & RENEWAL", h2_style))
    story.append(Paragraph(
        f"4.1 <b>Effective Date:</b> This Agreement shall commence on <b>{contract['effective_date']}</b>.<br/>"
        f"4.2 <b>Expiration Date:</b> This Agreement terminates definitively on <b>{contract['expiry_date']}</b> unless extended in writing.<br/>"
        f"4.3 <b>Invoicing Window:</b> Invoices submitted for service dates following {contract['expiry_date']} will be held and cannot be settled without an executed contract renewal amendment.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    # Section 5: Audit & Tolerances
    story.append(Paragraph("5. TOLERANCE POLICY & RECONCILIATION AUDIT", h2_style))
    story.append(Paragraph(
        f"5.1 <b>Audit Rights:</b> Invoices are audited via automated reconciliation controls before remittance.<br/>"
        f"5.2 <b>Permissible Variance:</b> An operational tolerance threshold of <b>{contract['tolerance_percent']}%</b> "
        f"or an absolute variance not exceeding <b>{contract['currency']} {contract['tolerance_absolute']:,.2f}</b> is allowed for rounding adjustments.<br/>"
        f"5.3 <b>Dispute Threshold:</b> Variances exceeding this threshold require manual finance approval or invoice re-submission.",
        body_style
    ))
    story.append(Spacer(1, 8))
    
    # Section 6: Special Conditions
    story.append(Paragraph("6. SPECIAL BILLING CONDITIONS", h2_style))
    story.append(Paragraph(f"<b>Special Stipulation:</b> {contract['special_conditions']}", body_style))
    story.append(Spacer(1, 20))
    
    # Signatures
    sig_data = [
        [Paragraph("<b>FOR SERVICE PROVIDER:</b>", bold_body), Paragraph("<b>FOR CLIENT:</b>", bold_body)],
        [Paragraph("Signature: _______________________<br/>Name: Jane Doe<br/>Title: VP Commercial Operations", body_style),
         Paragraph("Signature: _______________________<br/>Name: Authorized Signatory<br/>Title: Chief Procurement Officer", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.5, colors.HexColor("#94A3B8")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(sig_table)
    
    doc.build(story)

def build_policy_documents():
    """
    Creates enterprise billing and tolerance policy documents in PDF and Text format.
    """
    policy_pdf = POLICIES_DIR / "Billing_and_Tolerance_Policy.pdf"
    policy_txt = POLICIES_DIR / "Billing_and_Tolerance_Policy.txt"
    
    content = """GLOBAL FINANCE OPERATIONS: BILLING & TOLERANCE POLICY (FIN-POL-2025)

1. PURPOSE & SCOPE
This policy sets mandatory reconciliation criteria for accounts payable and customer billing compliance across all corporate contracts.

2. TOLERANCE THRESHOLDS & VARIANCE RULES
- Standard Tolerance Margin: A line-item or invoice variance of up to 1.0% or $50.00 (whichever is lower) is permissible for automated matching to account for minor rounding differences.
- Material Variances: Any variance exceeding 1.0% or $50.00 is classified as an exception requiring human finance review.
- High Exposure Threshold: Any exception with financial exposure exceeding $1,000.00 requires secondary controller sign-off.

3. DISCOUNT GOVERNANCE
- Contractual discounts stipulated in executed agreements (e.g. promotional discounts, volume tiers) must be applied explicitly on the invoice.
- If an invoice is billed at full gross value when a discount is contractual, the invoice must be placed on hold and disputed.

4. MULTI-CURRENCY REGULATIONS
- Invoices must be billed strictly in the currency designated in the executed agreement.
- Billing in unauthorized alternate currencies constitutes an unmatched exception due to unhedged FX exposure.

5. CONTRACT EXPIRATION CONTROLS
- Services rendered after the contractual termination date cannot be settled automatically.
- Accounts payable must verify whether an active addendum, extension, or renewal is executed before payment release.

6. DUPLICATE BILLING PREVENTION
- Invoices presenting identical customer identity, billing period, and amount will be flagged as DUPLICATE and blocked from settlement.

7. HUMAN-IN-THE-LOOP (HITL) REVIEW PROCESS
- Automated engines provide recommendations, variance breakdowns, and retrieved contractual evidence.
- The final financial disposition (ACCEPT, REJECT, OVERRIDE) must be executed by an authorized human reviewer.
- All reviewer actions must be permanently logged in the audit trail.
"""
    with open(policy_txt, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Build policy PDF
    doc = SimpleDocTemplate(str(policy_pdf), pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("GLOBAL FINANCE OPERATIONS POLICY", styles['Heading1']),
        Paragraph("<b>Standard Operating Procedure: Billing Compliance & Tolerances</b>", styles['Normal']),
        Spacer(1, 14),
    ]
    for para in content.split("\n\n"):
        story.append(Paragraph(para.replace("\n", "<br/>"), styles['Normal']))
        story.append(Spacer(1, 8))
    doc.build(story)

def generate_synthetic_invoices(contracts: List[ContractTerms]) -> List[RawInvoice]:
    """
    Generates 150+ realistic synthetic invoices covering all 15 enterprise reconciliation edge cases.
    """
    invoices: List[RawInvoice] = []
    inv_num = 1000
    
    # Helper to calculate amounts
    def make_inv(c: ContractTerms, month: int, variant: str = "EXACT", **kwargs) -> RawInvoice:
        nonlocal inv_num
        inv_num += 1
        inv_id = f"INV-{inv_num}"
        inv_date = f"2025-{month:02d}-15"
        billing_period = f"2025-{month:02d}"
        
        base_qty = c.quantity
        unit_price = c.unit_price
        gross = base_qty * unit_price
        discount_amount = round(gross * (c.discount_percent / 100.0), 2)
        net_amount = round(gross - discount_amount, 2)
        
        cust_name = c.customer_name
        curr = c.currency
        contract_id = c.contract_id
        cust_id = c.customer_id
        ref = f"PO-{c.contract_id[-4:]}-M{month}"
        
        if variant == "EXACT":
            # Clean exact match
            return RawInvoice(
                invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name=cust_name,
                invoice_date=inv_date, billing_period=billing_period, currency=curr, quantity=base_qty,
                unit_price=unit_price, discount=discount_amount, tax=0.0, total_amount=net_amount, reference_number=ref
            )
            
        elif variant == "TOLERANCE_WITHIN":
            # 0.4% variance ($36 on $9,000)
            slight_delta = round(net_amount * 0.004, 2)
            actual_total = round(net_amount + slight_delta, 2)
            return RawInvoice(
                invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name=cust_name,
                invoice_date=inv_date, billing_period=billing_period, currency=curr, quantity=base_qty,
                unit_price=unit_price, discount=discount_amount, tax=0.0, total_amount=actual_total, reference_number=ref
            )
            
        elif variant == "VARIANCE_EXCEEDS":
            # 12% overcharge
            overcharge = round(net_amount * 0.12, 2)
            actual_total = round(net_amount + overcharge, 2)
            return RawInvoice(
                invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name=cust_name,
                invoice_date=inv_date, billing_period=billing_period, currency=curr, quantity=base_qty,
                unit_price=unit_price, discount=discount_amount, tax=0.0, total_amount=actual_total, reference_number=ref
            )
            
        elif variant == "MISSING_CONTRACT":
            # No contract ID on invoice
            return RawInvoice(
                invoice_id=inv_id, contract_id="", customer_id=cust_id, customer_name=cust_name,
                invoice_date=inv_date, billing_period=billing_period, currency=curr, quantity=base_qty,
                unit_price=unit_price, discount=discount_amount, tax=0.0, total_amount=net_amount, reference_number=ref
            )
            
        elif variant == "WRONG_DISCOUNT":
            # Contract has discount (e.g. 10%), but invoice charged full gross
            return RawInvoice(
                invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name=cust_name,
                invoice_date=inv_date, billing_period=billing_period, currency=curr, quantity=base_qty,
                unit_price=unit_price, discount=0.0, tax=0.0, total_amount=gross, reference_number=ref
            )
            
        elif variant == "WRONG_QUANTITY":
            # Billed 130 units instead of 100
            new_qty = base_qty + 30
            new_gross = new_qty * unit_price
            new_net = round(new_gross * (1.0 - c.discount_percent / 100.0), 2)
            return RawInvoice(
                invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name=cust_name,
                invoice_date=inv_date, billing_period=billing_period, currency=curr, quantity=new_qty,
                unit_price=unit_price, discount=round(new_gross * (c.discount_percent / 100.0), 2), tax=0.0,
                total_amount=new_net, reference_number=ref
            )
            
        elif variant == "CURRENCY_MISMATCH":
            # USD contract billed in EUR
            wrong_curr = "EUR" if curr == "USD" else "USD"
            return RawInvoice(
                invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name=cust_name,
                invoice_date=inv_date, billing_period=billing_period, currency=wrong_curr, quantity=base_qty,
                unit_price=unit_price, discount=discount_amount, tax=0.0, total_amount=net_amount, reference_number=ref
            )
            
        elif variant == "CUSTOMER_NAME_VARIATION":
            # Variation in company suffix
            var_name = cust_name.replace("Inc.", "Incorporated").replace("Corp", "Corporation").replace("LLC", "")
            return RawInvoice(
                invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name=var_name,
                invoice_date=inv_date, billing_period=billing_period, currency=curr, quantity=base_qty,
                unit_price=unit_price, discount=discount_amount, tax=0.0, total_amount=net_amount, reference_number=ref
            )
            
        elif variant == "CONTRACT_EXPIRED":
            # Invoice dated after contract expiry
            exp_date = "2025-10-15" if c.contract_id in ["CTR-1003", "CTR-1008"] else "2026-04-15"
            return RawInvoice(
                invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name=cust_name,
                invoice_date=exp_date, billing_period="2025-10" if c.contract_id in ["CTR-1003", "CTR-1008"] else "2026-04",
                currency=curr, quantity=base_qty, unit_price=unit_price, discount=discount_amount, tax=0.0,
                total_amount=net_amount, reference_number=ref
            )
            
        elif variant == "OUTSIDE_PERIOD":
            # Invoice dated before effective date
            return RawInvoice(
                invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name=cust_name,
                invoice_date="2024-11-15", billing_period="2024-11", currency=curr, quantity=base_qty,
                unit_price=unit_price, discount=discount_amount, tax=0.0, total_amount=net_amount, reference_number=ref
            )
            
        elif variant == "DATA_QUALITY":
            # Missing customer name or negative amount
            return RawInvoice(
                invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name="",
                invoice_date=inv_date, billing_period=billing_period, currency=curr, quantity=base_qty,
                unit_price=unit_price, discount=0.0, tax=0.0, total_amount=-500.0, reference_number=ref
            )
            
        return RawInvoice(
            invoice_id=inv_id, contract_id=contract_id, customer_id=cust_id, customer_name=cust_name,
            invoice_date=inv_date, billing_period=billing_period, currency=curr, quantity=base_qty,
            unit_price=unit_price, discount=discount_amount, tax=0.0, total_amount=net_amount, reference_number=ref
        )

    # 1. Baseline Exact Matches (8 to 9 months for each of the 15 contracts -> ~110 invoices)
    for c in contracts:
        for m in range(1, 8):
            invoices.append(make_inv(c, month=m, variant="EXACT"))
            
    # 2. Add realistic discrepancy scenarios across contracts (~40 invoices)
    c1 = contracts[0]  # CTR-1001 (has 10% discount)
    invoices.append(make_inv(c1, month=8, variant="WRONG_DISCOUNT"))  # Billed gross $10,000 instead of $9,000
    invoices.append(make_inv(c1, month=9, variant="TOLERANCE_WITHIN")) # Small $36 variance
    invoices.append(make_inv(c1, month=10, variant="VARIANCE_EXCEEDS")) # 12% overcharge

    c2 = contracts[1]  # CTR-1002 (Meridian Logistics)
    invoices.append(make_inv(c2, month=8, variant="CUSTOMER_NAME_VARIATION"))
    invoices.append(make_inv(c2, month=9, variant="WRONG_QUANTITY")) # 80 vehicles instead of 50
    # Duplicate invoice test case
    dup_base = make_inv(c2, month=10, variant="EXACT")
    invoices.append(dup_base)
    dup_copy = RawInvoice(**dup_base.model_dump())
    dup_copy.invoice_id = f"INV-{inv_num + 1}"
    invoices.append(dup_copy)

    c3 = contracts[2]  # CTR-1003 (Apex Health - expires June 30, 2025)
    invoices.append(make_inv(c3, month=8, variant="CONTRACT_EXPIRED")) # Dated October 2025

    c4 = contracts[3]  # CTR-1004 (EUR contract)
    invoices.append(make_inv(c4, month=8, variant="CURRENCY_MISMATCH")) # Billed in USD instead of EUR

    c5 = contracts[4]  # CTR-1005 (Horizon Financial)
    invoices.append(make_inv(c5, month=8, variant="WRONG_DISCOUNT"))
    invoices.append(make_inv(c5, month=9, variant="MISSING_CONTRACT"))

    c8 = contracts[7]  # CTR-1008 (Starlight Cyber - expires May 31, 2025)
    invoices.append(make_inv(c8, month=8, variant="CONTRACT_EXPIRED"))

    c9 = contracts[8]  # CTR-1009 (Beacon Renewable)
    invoices.append(make_inv(c9, month=8, variant="TOLERANCE_WITHIN"))
    invoices.append(make_inv(c9, month=9, variant="OUTSIDE_PERIOD"))

    c10 = contracts[9] # CTR-1010 (Titan Heavy - high value)
    invoices.append(make_inv(c10, month=8, variant="VARIANCE_EXCEEDS"))

    # Unrecognized entity / missing contract
    inv_num += 1
    invoices.append(RawInvoice(
        invoice_id=f"INV-{inv_num}",
        contract_id="CTR-9999",
        customer_id="CUST-999",
        customer_name="Phantom Enterprises LLC",
        invoice_date="2025-08-15",
        billing_period="2025-08",
        currency="USD",
        quantity=1,
        unit_price=5400.0,
        discount=0.0,
        tax=0.0,
        total_amount=5400.0,
        reference_number="PO-UNKNOWN-01"
    ))

    # Data quality exception
    invoices.append(make_inv(contracts[5], month=8, variant="DATA_QUALITY"))

    return invoices

def save_invoices_to_csv(invoices: List[RawInvoice], filepath: Path):
    """
    Saves invoice records to a clean CSV file.
    """
    fieldnames = [
        "invoice_id", "contract_id", "customer_id", "customer_name",
        "invoice_date", "billing_period", "currency", "quantity",
        "unit_price", "discount", "tax", "total_amount", "reference_number"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for inv in invoices:
            writer.writerow(inv.model_dump())

def generate_all_data():
    """
    Main orchestration routine to regenerate contracts, policies, vector store, and invoices.
    """
    print("==================================================")
    print("REGENERATING SYNTHETIC FINANCE CONTRACT & BILLING DATA")
    print("==================================================")
    
    # 1. Reset Database & Vector Store
    print("[1/5] Initializing SQLite database and resetting tables...")
    reset_database()
    
    # 2. Build Policy Documents
    print("[2/5] Generating Finance Billing & Tolerance Policies...")
    build_policy_documents()
    
    # 3. Build Contract PDFs & ContractTerms models
    print("[3/5] Generating 15 multi-page Contract PDFs via ReportLab...")
    contract_models: List[ContractTerms] = []
    vector_store = get_vector_store()
    vector_store.reset_vector_store()
    all_clauses = []
    
    for c_data in CONTRACT_TEMPLATES:
        pdf_name = f"{c_data['contract_id']}_{c_data['customer_id']}.pdf"
        pdf_path = CONTRACTS_DIR / pdf_name
        build_pdf_contract(c_data, str(pdf_path))
        
        c_model = ContractTerms(**c_data, file_path=str(pdf_path))
        contract_models.append(c_model)
        
        # Extract clauses using PyMuPDF and prepare for vector store
        clauses = extract_clauses_from_pdf(str(pdf_path), contract_id=c_data['contract_id'])
        all_clauses.extend(clauses)
        
    # Also ingest policy document clauses into ChromaDB
    policy_txt_path = POLICIES_DIR / "Billing_and_Tolerance_Policy.txt"
    with open(policy_txt_path, "r", encoding="utf-8") as f:
        policy_clauses = extract_clauses_from_text(f.read(), doc_name="Billing_and_Tolerance_Policy.pdf", contract_id="POLICY-CORP")
        all_clauses.extend(policy_clauses)
        
    # Save contracts to database
    save_contracts(contract_models)
    
    # 4. Ingest Clauses into ChromaDB Vector Store
    print(f"[4/5] Ingesting {len(all_clauses)} contract clauses into ChromaDB Vector Store...")
    vector_store.add_clauses(all_clauses)
    
    # 5. Generate 140+ Synthetic Invoices
    print("[5/5] Generating 140+ realistic synthetic invoices with edge cases...")
    invoices = generate_synthetic_invoices(contract_models)
    save_invoices(invoices)
    
    csv_path = INVOICES_DIR / "synthetic_invoices.csv"
    save_invoices_to_csv(invoices, csv_path)
    
    print("==================================================")
    print(f"SUCCESS: Generated {len(contract_models)} Contracts, {len(all_clauses)} Vector Clauses, and {len(invoices)} Invoices.")
    print(f"Contracts: {CONTRACTS_DIR}")
    print(f"Invoices CSV: {csv_path}")
    print(f"Policies: {POLICIES_DIR}")
    print("==================================================")

if __name__ == "__main__":
    generate_all_data()
