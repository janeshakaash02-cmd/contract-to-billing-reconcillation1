import os
from typing import List, Dict, Any, Optional, Tuple
from app.config import LLM_PROVIDER, LLM_API_KEY, LLM_MODEL
from app.core.models import ContractClause
from app.rag.vector_store import get_vector_store

SYSTEM_PROMPT = """You are a senior Finance AI Auditor. Your job is to analyze billing invoices against contractual legal agreements.

STRICT AUDIT RULES:
1. ONLY use the provided contractual clauses as your factual basis.
2. DO NOT make up, assume, or invent contract terms or numbers.
3. If the provided contractual evidence does not answer the question or does not contain the clause, you MUST state explicitly:
   "Insufficient contractual evidence."
4. ALWAYS cite the document name and page number for every claim (e.g., "[Contract CTR-1001, Page 2]").
5. Keep explanations precise, objective, and actionable for a finance operations reviewer.
"""

class ContractRAGChain:
    """
    RAG chain for answering questions against ingested contracts and policies,
    and explaining invoice discrepancies with explicit citations.
    """
    def __init__(self):
        self.vector_store = get_vector_store()
        self.provider = LLM_PROVIDER
        self.api_key = LLM_API_KEY
        self.model_name = LLM_MODEL
        
        # Check if live LLM is configured
        self._llm = None
        if self.provider == "groq" and self.api_key:
            try:
                from langchain_groq import ChatGroq
                self._llm = ChatGroq(groq_api_key=self.api_key, model_name=self.model_name or "llama-3.3-70b-versatile", temperature=0.0)
            except Exception as e:
                print(f"[WARN] Failed to initialize ChatGroq: {e}")
                self._llm = None
        elif self.provider == "openai" and self.api_key:
            try:
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(api_key=self.api_key, model=self.model_name, temperature=0.0)
            except Exception:
                self._llm = None

    def retrieve_evidence(
        self,
        query: str,
        contract_id: Optional[str] = None,
        k: int = 4
    ) -> List[Tuple[ContractClause, float]]:
        """
        Retrieves top relevant clauses from ChromaDB.
        """
        return self.vector_store.query_clauses(query=query, contract_id=contract_id, k=k)

    def ask_contract(
        self,
        question: str,
        contract_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answers a user question regarding contract terms, strictly grounded in retrieved evidence.
        """
        evidence_results = self.retrieve_evidence(query=question, contract_id=contract_id, k=4)
        
        if not evidence_results or evidence_results[0][1] < 0.25:
            return {
                "answer": "Insufficient contractual evidence.",
                "evidence_citations": [],
                "grounded": False,
            }
            
        context_blocks = []
        citations = []
        for clause, score in evidence_results:
            citation_str = f"{clause.document_name} (Page {clause.page_number}, {clause.clause_category})"
            citations.append(citation_str)
            context_blocks.append(f"[{citation_str}]:\n{clause.clause_text}")
            
        context_str = "\n\n".join(context_blocks)
        
        # If live LLM is active
        if self._llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                messages = [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=f"Context from Contract:\n{context_str}\n\nQuestion: {question}\n\nAnswer:")
                ]
                resp = self._llm.invoke(messages)
                return {
                    "answer": resp.content.strip(),
                    "evidence_citations": citations,
                    "grounded": True,
                }
            except Exception:
                pass  # Fallback to local grounded synthesizer
                
        # High-precision local grounded synthesizer (works 100% offline for demo & tests)
        top_clause, top_score = evidence_results[0]
        summary_answer = (
            f"Based on {top_clause.document_name} (Page {top_clause.page_number}):\n\n"
            f"\"{top_clause.clause_text.strip()}\""
        )
        
        return {
            "answer": summary_answer,
            "evidence_citations": citations,
            "grounded": True,
        }

    def generate_discrepancy_explanation(
        self,
        invoice_id: str,
        customer_name: str,
        contract_id: Optional[str],
        expected_amount: float,
        actual_amount: float,
        variance_amount: float,
        variance_percent: float,
        currency: str,
        issue_type: str,
        contract_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates structured 5-part explanation for reconciliation exceptions:
        1. WHAT HAPPENED?
        2. WHY DID IT HAPPEN?
        3. WHAT DOES THE CONTRACT SAY?
        4. WHAT EVIDENCE SUPPORTS THIS?
        5. WHAT SHOULD THE FINANCE REVIEWER DO?
        """
        citations = []
        contract_clause_snippet = "No active contract found."
        
        if contract_id:
            query = f"discount billing price amount tolerance {issue_type}"
            ev_list = self.retrieve_evidence(query, contract_id=contract_id, k=2)
            if ev_list and ev_list[0][1] >= 0.20:
                top_clause = ev_list[0][0]
                citations.append(f"{top_clause.document_name}, Page {top_clause.page_number} ({top_clause.clause_category})")
                contract_clause_snippet = f"\"{top_clause.clause_text.strip()}\""
            else:
                citations.append(f"Contract ID: {contract_id} (Metadata Record)")

        # Formulate structured explanation
        if issue_type == "DUPLICATE":
            what_happened = f"Duplicate invoice detected for invoice {invoice_id} ({customer_name})."
            why_did_it_happen = "The invoice shares identical billing period and amount with an already processed invoice."
            what_contract_says = "Standard billing controls stipulate exactly one invoice per contracted billing cycle."
            recommendation = "Reject the duplicate invoice or request confirmation from Accounts Payable."
            
        elif issue_type == "MISSING_CONTRACT":
            what_happened = f"Invoice {invoice_id} for '{customer_name}' has no identifiable contract reference."
            why_did_it_happen = "The invoice was submitted without a valid contract ID or reference number."
            what_contract_says = "Finance policy requires all non-standard billing to link to an approved Master Services Agreement."
            recommendation = "Hold payment/posting and route to Vendor Relations to attach an executed contract."
            
        elif issue_type == "CONTRACT_EXPIRED":
            what_happened = f"Invoice {invoice_id} was submitted after the contract expiration date."
            why_did_it_happen = f"The invoice date is beyond the agreed contractual term."
            what_contract_says = f"Contractual agreement ended on the expiry date. {contract_clause_snippet}"
            recommendation = "Verify if a contract amendment, renewal, or extension has been signed before approving."
            
        elif issue_type == "DISCOUNT_MISMATCH":
            what_happened = f"Contractual discount was not applied. Expected {currency} {expected_amount:,.2f}, but billed {currency} {actual_amount:,.2f}."
            why_did_it_happen = f"Contract stipulates a promotional or volume discount that was omitted from the line items."
            what_contract_says = f"Applicable clause: {contract_clause_snippet}"
            recommendation = "Issue short-pay / credit note request to vendor or request revised invoice reflecting the discount."
            
        elif issue_type == "QUANTITY_MISMATCH":
            what_happened = f"Billed quantity does not match contracted volume."
            why_did_it_happen = "Invoice reflects different unit count than the contracted baseline."
            what_contract_says = f"Contract defines fixed baseline volume. {contract_clause_snippet}"
            recommendation = "Verify timesheets/deliverables or request proof of change order."
            
        elif issue_type == "CURRENCY_MISMATCH":
            what_happened = f"Invoice currency '{currency}' differs from contracted currency."
            why_did_it_happen = "Invoice was billed in foreign currency without agreed forex conversion terms."
            what_contract_says = f"Contract mandates payment in base contracted currency. {contract_clause_snippet}"
            recommendation = "Reject invoice and request rebilling in contract currency or confirm FX hedging policy."
            
        elif issue_type == "AMOUNT_VARIANCE":
            what_happened = f"Invoice amount {currency} {actual_amount:,.2f} deviates from expected {currency} {expected_amount:,.2f} by {currency} {abs(variance_amount):,.2f} ({variance_percent:.2f}%)."
            why_did_it_happen = "Variance exceeds permissible contractual tolerance thresholds."
            what_contract_says = f"Contract specifies pricing terms. {contract_clause_snippet}"
            recommendation = "Manual review required. Obtain variance approval from Department Head if variance is justified."
            
        elif issue_type == "TOLERANCE_MATCH":
            what_happened = f"Invoice amount {currency} {actual_amount:,.2f} has a small variance of {currency} {abs(variance_amount):,.2f} ({variance_percent:.2f}%) within allowable tolerance."
            why_did_it_happen = "Minor rounding or tax rounding variation within contractual margin."
            what_contract_says = f"Contract policy allows minor operational tolerances. {contract_clause_snippet}"
            recommendation = "Auto-clear or approve as low-risk variance within corporate tolerance policy."
            
        else:
            what_happened = f"Invoice {invoice_id} matched contract terms."
            why_did_it_happen = "All line items, amounts, and dates conform to the contractual agreement."
            what_contract_says = f"Standard terms apply. {contract_clause_snippet}"
            recommendation = "Auto-approve for standard payment processing."
            
        return {
            "what_happened": what_happened,
            "why_did_it_happen": why_did_it_happen,
            "what_contract_says": what_contract_says,
            "evidence_citations": citations,
            "recommendation": recommendation,
        }

_rag_chain_instance = None

def get_rag_chain() -> ContractRAGChain:
    global _rag_chain_instance
    if _rag_chain_instance is None:
        _rag_chain_instance = ContractRAGChain()
    return _rag_chain_instance
