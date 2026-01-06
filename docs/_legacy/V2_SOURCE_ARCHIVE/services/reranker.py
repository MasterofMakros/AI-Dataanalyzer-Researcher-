
"""
Search Reranking Service
Status: EXPERIMENTAL
Enhances search relevance using Cross-Encoders.
"""

from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from config.feature_flags import is_enabled

# Model for Reranking (German Optimized)
# mmarco returned 0.0 scores. Trying explicit German model.
RERANK_MODEL = "svalabs/cross-electra-melange-german"

class RerankingService:
    """Re-ranks search results using a Cross-Encoder."""

    def __init__(self):
        self._enabled = is_enabled("ENABLE_RERANKING")
        self._model = None
        
        if self._enabled:
            print(f"🚀 Initializing Reranker ({RERANK_MODEL})...")
            try:
                self._model = CrossEncoder(RERANK_MODEL)
                print("✅ Reranker Ready.")
            except Exception as e:
                print(f"⚠️ Reranker Init Failed: {e}")
                self._enabled = False

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate documents based on the query.
        Each candidate must have a 'text' or 'extracted_text' field.
        """
        if not self._enabled or not self._model or not candidates:
            return candidates[:top_k]

        # Prepare pairs for Cross-Encoder
        # (Query, Document Text)
        pairs = []
        valid_candidates = []
        
        for doc in candidates:
            text = doc.get("extracted_text", "") or doc.get("text", "")
            # Truncate text to avoiding token limit issues (Cross-Encoders usually 512 tokens)
            text_snippet = text[:1000] 
            pairs.append((query, text_snippet))
            valid_candidates.append(doc)

        if not pairs:
            return candidates[:top_k]

        # Predict scores
        scores = self._model.predict(pairs)

        # Attach scores and sort
        for i, doc in enumerate(valid_candidates):
            doc["rerank_score"] = float(scores[i])
            doc["_reranked"] = True

        # Sort descending by new score
        reranked = sorted(valid_candidates, key=lambda x: x["rerank_score"], reverse=True)
        
        return reranked[:top_k]
