
"""
Search Reranking Service
Status: EXPERIMENTAL
Enhances search relevance using Cross-Encoders or Qwen3-Reranker-8B.

A/B Test Configuration:
- USE_QWEN3_RERANKER=False: Cross-Encoder (svalabs/cross-electra-melange-german)
- USE_QWEN3_RERANKER=True: Qwen3-Reranker-8B (quantized for 8GB VRAM)
"""

import time
from typing import List, Dict, Any, Optional
from config.feature_flags import is_enabled

# Model imports with lazy loading
_cross_encoder = None
_qwen3_reranker = None


def _load_cross_encoder():
    """Lazy load Cross-Encoder model."""
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder
        from config.reranker_config import get_reranker_config
        config = get_reranker_config(experimental=False)
        print(f"🚀 Loading Cross-Encoder ({config.model_id})...")
        _cross_encoder = CrossEncoder(config.model_id)
        print("✅ Cross-Encoder Ready.")
    return _cross_encoder


def _load_qwen3_reranker():
    """Lazy load Qwen3-Reranker-8B with quantization."""
    global _qwen3_reranker
    if _qwen3_reranker is None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from config.reranker_config import get_reranker_config
        
        config = get_reranker_config(experimental=True)
        print(f"🚀 Loading Qwen3-Reranker-8B ({config.model_id})...")
        
        # Load with 4-bit quantization for VRAM savings
        load_kwargs = {"device_map": "auto"}
        if config.use_quantization:
            try:
                from transformers import BitsAndBytesConfig
                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype="float16",
                )
                print("  → Using 4-bit quantization")
            except ImportError:
                print("  ⚠️ bitsandbytes not available, loading without quantization")
        
        _qwen3_reranker = {
            "model": AutoModelForSequenceClassification.from_pretrained(
                config.model_id, **load_kwargs
            ),
            "tokenizer": AutoTokenizer.from_pretrained(config.model_id),
            "config": config,
        }
        print("✅ Qwen3-Reranker-8B Ready.")
    return _qwen3_reranker


class RerankingService:
    """Re-ranks search results using Cross-Encoder or Qwen3-Reranker-8B."""

    def __init__(self):
        self._enabled = is_enabled("ENABLE_RERANKING")
        self._use_qwen3 = is_enabled("USE_QWEN3_RERANKER")
        self._model = None
        self._metrics = {"calls": 0, "total_time_ms": 0, "avg_improvement": 0}
        
        if self._enabled:
            try:
                if self._use_qwen3:
                    self._model = _load_qwen3_reranker()
                else:
                    self._model = _load_cross_encoder()
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

        start_time = time.time()
        
        # Prepare pairs
        pairs = []
        valid_candidates = []
        
        for doc in candidates:
            text = doc.get("extracted_text", "") or doc.get("text", "")
            text_snippet = text[:2000] if self._use_qwen3 else text[:1000]
            pairs.append((query, text_snippet))
            valid_candidates.append(doc)

        if not pairs:
            return candidates[:top_k]

        # Score based on model type
        if self._use_qwen3:
            scores = self._score_qwen3(pairs)
        else:
            scores = self._model.predict(pairs)

        # Attach scores and sort
        for i, doc in enumerate(valid_candidates):
            doc["rerank_score"] = float(scores[i])
            doc["_reranked"] = True
            doc["_reranker"] = "qwen3-8b" if self._use_qwen3 else "cross-electra"

        reranked = sorted(valid_candidates, key=lambda x: x["rerank_score"], reverse=True)
        
        # Update metrics
        elapsed_ms = (time.time() - start_time) * 1000
        self._metrics["calls"] += 1
        self._metrics["total_time_ms"] += elapsed_ms
        
        return reranked[:top_k]

    def _score_qwen3(self, pairs: List[tuple]) -> List[float]:
        """Score using Qwen3-Reranker-8B."""
        import torch
        
        tokenizer = self._model["tokenizer"]
        model = self._model["model"]
        config = self._model["config"]
        
        scores = []
        batch_size = config.batch_size
        
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]
            inputs = tokenizer(
                [p[0] for p in batch],  # queries
                [p[1] for p in batch],  # documents
                padding=True,
                truncation=True,
                max_length=config.max_tokens,
                return_tensors="pt"
            ).to(model.device)
            
            with torch.no_grad():
                outputs = model(**inputs)
                batch_scores = outputs.logits.squeeze(-1).tolist()
                
            if isinstance(batch_scores, float):
                batch_scores = [batch_scores]
            scores.extend(batch_scores)
        
        return scores

    def get_metrics(self) -> dict:
        """Return reranking performance metrics."""
        return {
            **self._metrics,
            "model": "qwen3-8b" if self._use_qwen3 else "cross-electra",
            "avg_time_ms": self._metrics["total_time_ms"] / max(1, self._metrics["calls"]),
        }

