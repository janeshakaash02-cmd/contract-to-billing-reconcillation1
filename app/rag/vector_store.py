import os
import shutil
from typing import List, Optional, Tuple, Dict, Any

# Streamlit Cloud SQLite3 compatibility fix for ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    pass

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except Exception as _e:
    CHROMA_AVAILABLE = False
    print(f"[WARN] ChromaDB not available in current environment: {_e}")

from app.config import CHROMA_PERSIST_DIR, EMBEDDING_PROVIDER, EMBEDDING_API_KEY, EMBEDDING_MODEL
from app.core.models import ContractClause

COLLECTION_NAME = "contract_billing_clauses"

class VectorStoreManager:
    """
    Manages persistent ChromaDB vector storage for contract clauses and billing policies.
    Supports local ONNX MiniLM embeddings (zero-config, offline) or OpenAI embeddings,
    with an in-memory fallback if ChromaDB is unavailable in cloud environments.
    """
    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or str(CHROMA_PERSIST_DIR)
        os.makedirs(self.persist_dir, exist_ok=True)
        self.in_memory_clauses: List[ContractClause] = []
        
        if CHROMA_AVAILABLE:
            try:
                # Initialize embedding function
                if EMBEDDING_PROVIDER == "openai" and EMBEDDING_API_KEY:
                    self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
                        api_key=EMBEDDING_API_KEY,
                        model_name=EMBEDDING_MODEL
                    )
                else:
                    self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

                self.client = chromadb.PersistentClient(path=self.persist_dir)
                self.collection = self.client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    embedding_function=self.embedding_fn,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                print(f"[WARN] ChromaDB initialization failed, falling back to memory: {e}")
                self.collection = None
        else:
            self.collection = None

    def add_clauses(self, clauses: List[ContractClause]) -> int:
        """
        Adds or updates a batch of contract clauses in the vector collection.
        """
        if not clauses:
            return 0
            
        self.in_memory_clauses.extend(clauses)
        
        if self.collection is not None:
            try:
                ids = []
                documents = []
                metadatas = []
                
                for idx, clause in enumerate(clauses):
                    clause_id = f"{clause.contract_id}_p{clause.page_number}_{clause.clause_category}_{idx}"
                    ids.append(clause_id)
                    documents.append(clause.clause_text)
                    metadatas.append({
                        "contract_id": clause.contract_id,
                        "document_name": clause.document_name,
                        "page_number": clause.page_number,
                        "clause_category": clause.clause_category,
                    })
                    
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception as e:
                print(f"[WARN] ChromaDB upsert failed, retaining in-memory: {e}")
                
        return len(clauses)

    def query_clauses(
        self,
        query: str,
        contract_id: Optional[str] = None,
        clause_category: Optional[str] = None,
        k: int = 4
    ) -> List[Tuple[ContractClause, float]]:
        """
        Queries the vector store for semantic matches.
        Returns a list of (ContractClause, cosine_similarity_score).
        Falls back to lexical matching if ChromaDB is unavailable.
        """
        if self.collection is not None:
            try:
                where_filter = {}
                if contract_id and clause_category:
                    where_filter = {"$and": [{"contract_id": contract_id}, {"clause_category": clause_category}]}
                elif contract_id:
                    where_filter = {"contract_id": contract_id}
                elif clause_category:
                    where_filter = {"clause_category": clause_category}
                    
                kwargs: Dict[str, Any] = {
                    "query_texts": [query],
                    "n_results": min(k, max(1, self.collection.count())),
                }
                if where_filter:
                    kwargs["where"] = where_filter

                results = self.collection.query(**kwargs)
                
                clauses_with_scores: List[Tuple[ContractClause, float]] = []
                if results and results.get("documents") and results["documents"][0]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                    distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
                    
                    for doc_text, meta, dist in zip(docs, metas, distances):
                        similarity = round(max(0.0, 1.0 - (dist / 2.0)), 3)
                        clause = ContractClause(
                            contract_id=meta.get("contract_id", "UNKNOWN"),
                            document_name=meta.get("document_name", "UNKNOWN"),
                            page_number=meta.get("page_number", 1),
                            clause_category=meta.get("clause_category", "GENERAL"),
                            clause_text=doc_text,
                        )
                        clauses_with_scores.append((clause, similarity))
                    return clauses_with_scores
            except Exception as e:
                print(f"[WARN] ChromaDB query failed, using in-memory fallback: {e}")

        # In-memory lexical fallback
        candidates = self.in_memory_clauses
        if contract_id:
            candidates = [c for c in candidates if c.contract_id == contract_id]
        if clause_category:
            candidates = [c for c in candidates if c.clause_category == clause_category]
            
        if not candidates:
            return []
            
        q_tokens = set(query.lower().split())
        scored: List[Tuple[ContractClause, float]] = []
        for c in candidates:
            c_tokens = set(c.clause_text.lower().split())
            overlap = len(q_tokens.intersection(c_tokens))
            score = round(min(0.99, 0.4 + (overlap / max(1, len(q_tokens))) * 0.55), 2)
            scored.append((c, score))
            
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def reset_vector_store(self):
        """
        Drops and recreates the collection or clears memory.
        """
        self.in_memory_clauses.clear()
        if self.collection is not None:
            try:
                self.client.delete_collection(COLLECTION_NAME)
                self.collection = self.client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    embedding_function=self.embedding_fn,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception:
                pass

_vector_store_instance = None

def get_vector_store() -> VectorStoreManager:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreManager()
    return _vector_store_instance
