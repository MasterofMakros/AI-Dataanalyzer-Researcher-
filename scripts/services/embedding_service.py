"""
Neural Vault Embedding Service
==============================

Produktions-Service für Embedding-Generierung mit:
- A/B-Test Support
- Batch Processing
- Caching
- Qdrant Integration

Usage:
    from scripts.services.embedding_service import EmbeddingService

    service = EmbeddingService()
    embeddings = service.embed(["Text 1", "Text 2"])
    service.store_in_qdrant(embeddings, metadata)
"""

import os
import sys
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
import numpy as np

# Projekt-Root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.embeddings import (
    EmbeddingModel,
    EmbeddingConfig,
    EMBEDDING_CONFIGS,
    get_embedding_config,
    get_embedding_model,
    EMBEDDING_MODEL_ACTIVE,
    EMBEDDING_MODEL_EXPERIMENTAL,
)
from config.paths import QDRANT_URL, DATA_DIR


# =============================================================================
# CACHE
# =============================================================================

class EmbeddingCache:
    """
    Einfacher Disk-Cache für Embeddings.

    Verhindert Re-Embedding von bereits verarbeiteten Texten.
    """

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or (DATA_DIR / "embedding_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache = {}  # In-Memory für Session

    def _hash_text(self, text: str, model_id: str) -> str:
        """Generiert Hash für Text + Modell."""
        content = f"{model_id}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, text: str, model_id: str) -> Optional[np.ndarray]:
        """Holt Embedding aus Cache."""
        key = self._hash_text(text, model_id)

        # Memory-Cache zuerst
        if key in self.memory_cache:
            return self.memory_cache[key]

        # Disk-Cache
        cache_file = self.cache_dir / f"{key}.npy"
        if cache_file.exists():
            try:
                embedding = np.load(cache_file)
                self.memory_cache[key] = embedding
                return embedding
            except:
                pass

        return None

    def set(self, text: str, model_id: str, embedding: np.ndarray):
        """Speichert Embedding im Cache."""
        key = self._hash_text(text, model_id)

        # Memory-Cache
        self.memory_cache[key] = embedding

        # Disk-Cache (optional, für Persistenz)
        try:
            cache_file = self.cache_dir / f"{key}.npy"
            np.save(cache_file, embedding)
        except:
            pass

    def clear(self):
        """Leert den Cache."""
        self.memory_cache.clear()
        for f in self.cache_dir.glob("*.npy"):
            f.unlink()


# =============================================================================
# EMBEDDING SERVICE
# =============================================================================

@dataclass
class EmbeddingResult:
    """Ergebnis einer Embedding-Operation."""
    embeddings: np.ndarray
    model_id: str
    dimensions: int
    cached_count: int
    computed_count: int


class EmbeddingService:
    """
    Produktions-Service für Embedding-Generierung.

    Features:
    - Automatisches Model-Loading
    - Batch Processing
    - Caching
    - A/B-Test Support
    - Qdrant Integration
    """

    def __init__(
        self,
        experimental: bool = False,
        use_cache: bool = True,
        device: str = None,
    ):
        """
        Initialisiert den Service.

        Args:
            experimental: True für experimentelles Modell (A/B-Test)
            use_cache: Embedding-Cache verwenden
            device: cuda, cpu, oder mps
        """
        self.experimental = experimental
        self.config = get_embedding_config(experimental)
        self.use_cache = use_cache

        # Device Override
        if device:
            self.config.device = device

        self.model = None
        self.cache = EmbeddingCache() if use_cache else None

        # Qdrant Client (lazy loading)
        self._qdrant = None

    @property
    def model_id(self) -> str:
        """Gibt die aktuelle Model-ID zurück."""
        return self.config.model_id

    def load(self) -> bool:
        """
        Lädt das Embedding-Modell.

        Returns:
            True bei Erfolg
        """
        if self.model is not None:
            return True

        try:
            from sentence_transformers import SentenceTransformer

            print(f"[EmbeddingService] Loading {self.config.model_id}...")

            # Device-Handling
            device = None
            if self.config.device == "cuda":
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                else:
                    print("  ⚠ CUDA not available, falling back to CPU")
                    device = "cpu"
            elif self.config.device == "mps":
                device = "mps"
            else:
                device = "cpu"

            self.model = SentenceTransformer(
                self.config.model_id,
                device=device,
            )

            print(f"[EmbeddingService] ✓ Loaded on {device}")
            return True

        except Exception as e:
            print(f"[EmbeddingService] ✗ Failed to load: {e}")
            return False

    def unload(self):
        """Entlädt das Modell."""
        if self.model is not None:
            del self.model
            self.model = None

            import gc
            gc.collect()

            try:
                import torch
                torch.cuda.empty_cache()
            except:
                pass

    def embed(
        self,
        texts: Union[str, List[str]],
        batch_size: int = None,
        show_progress: bool = False,
    ) -> EmbeddingResult:
        """
        Generiert Embeddings für Texte.

        Args:
            texts: Einzelner Text oder Liste von Texten
            batch_size: Batch-Größe (default aus Config)
            show_progress: Progress-Bar anzeigen

        Returns:
            EmbeddingResult mit Embeddings und Metadaten
        """
        # Normalisieren zu Liste
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return EmbeddingResult(
                embeddings=np.array([]),
                model_id=self.model_id,
                dimensions=self.config.dimensions,
                cached_count=0,
                computed_count=0,
            )

        # Modell laden falls nötig
        if self.model is None:
            if not self.load():
                raise RuntimeError("Failed to load embedding model")

        batch_size = batch_size or self.config.batch_size

        # Cache-Lookup
        cached_embeddings = {}
        texts_to_compute = []
        indices_to_compute = []

        if self.cache:
            for i, text in enumerate(texts):
                cached = self.cache.get(text, self.model_id)
                if cached is not None:
                    cached_embeddings[i] = cached
                else:
                    texts_to_compute.append(text)
                    indices_to_compute.append(i)
        else:
            texts_to_compute = texts
            indices_to_compute = list(range(len(texts)))

        # Neue Embeddings berechnen
        computed_embeddings = {}
        if texts_to_compute:
            new_embeddings = self.model.encode(
                texts_to_compute,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=self.config.normalize,
            )

            for i, idx in enumerate(indices_to_compute):
                embedding = new_embeddings[i]
                computed_embeddings[idx] = embedding

                # Cache speichern
                if self.cache:
                    self.cache.set(texts_to_compute[i], self.model_id, embedding)

        # Ergebnis zusammenbauen
        all_embeddings = []
        for i in range(len(texts)):
            if i in cached_embeddings:
                all_embeddings.append(cached_embeddings[i])
            else:
                all_embeddings.append(computed_embeddings[i])

        embeddings_array = np.array(all_embeddings)

        return EmbeddingResult(
            embeddings=embeddings_array,
            model_id=self.model_id,
            dimensions=embeddings_array.shape[1] if len(embeddings_array) > 0 else self.config.dimensions,
            cached_count=len(cached_embeddings),
            computed_count=len(computed_embeddings),
        )

    def embed_single(self, text: str) -> np.ndarray:
        """Convenience-Methode für einzelnen Text."""
        result = self.embed(text)
        return result.embeddings[0]

    # =========================================================================
    # QDRANT INTEGRATION
    # =========================================================================

    @property
    def qdrant(self):
        """Lazy-Loading Qdrant Client."""
        if self._qdrant is None:
            try:
                from qdrant_client import QdrantClient
                self._qdrant = QdrantClient(url=QDRANT_URL)
            except Exception as e:
                print(f"[EmbeddingService] ⚠ Qdrant connection failed: {e}")
                return None
        return self._qdrant

    def store_in_qdrant(
        self,
        texts: List[str],
        metadata: List[Dict],
        collection_name: str = "documents",
        ids: List[str] = None,
    ) -> bool:
        """
        Speichert Embeddings in Qdrant.

        Args:
            texts: Texte zum Embedden
            metadata: Metadaten pro Dokument
            collection_name: Qdrant Collection
            ids: Optional: IDs für Dokumente

        Returns:
            True bei Erfolg
        """
        if self.qdrant is None:
            return False

        try:
            from qdrant_client.models import PointStruct

            # Embeddings generieren
            result = self.embed(texts, show_progress=True)

            # IDs generieren falls nicht gegeben
            if ids is None:
                ids = [hashlib.sha256(t.encode()).hexdigest()[:16] for t in texts]

            # Points erstellen
            points = []
            for i, (embedding, meta, doc_id) in enumerate(zip(
                result.embeddings, metadata, ids
            )):
                points.append(PointStruct(
                    id=doc_id,
                    vector=embedding.tolist(),
                    payload=meta,
                ))

            # In Qdrant speichern
            self.qdrant.upsert(
                collection_name=collection_name,
                points=points,
            )

            print(f"[EmbeddingService] ✓ Stored {len(points)} vectors in Qdrant")
            return True

        except Exception as e:
            print(f"[EmbeddingService] ✗ Qdrant storage failed: {e}")
            return False

    def search_similar(
        self,
        query: str,
        collection_name: str = "documents",
        top_k: int = 10,
        score_threshold: float = 0.5,
    ) -> List[Dict]:
        """
        Sucht ähnliche Dokumente in Qdrant.

        Args:
            query: Suchtext
            collection_name: Qdrant Collection
            top_k: Anzahl Ergebnisse
            score_threshold: Minimum Similarity Score

        Returns:
            Liste von {id, score, payload}
        """
        if self.qdrant is None:
            return []

        try:
            # Query embedden
            query_embedding = self.embed_single(query)

            # Suche
            results = self.qdrant.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k,
                score_threshold=score_threshold,
            )

            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload,
                }
                for r in results
            ]

        except Exception as e:
            print(f"[EmbeddingService] ✗ Search failed: {e}")
            return []

    # =========================================================================
    # A/B TEST SUPPORT
    # =========================================================================

    @classmethod
    def create_ab_pair(cls) -> Tuple["EmbeddingService", "EmbeddingService"]:
        """
        Erstellt ein Paar von Services für A/B-Testing.

        Returns:
            (service_a, service_b) - Aktuell und Experimental
        """
        service_a = cls(experimental=False)
        service_b = cls(experimental=True)
        return service_a, service_b


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Singleton für einfache Nutzung
_default_service: Optional[EmbeddingService] = None


def get_embedding_service(experimental: bool = False) -> EmbeddingService:
    """
    Holt den Default-Embedding-Service.

    Args:
        experimental: True für experimentelles Modell

    Returns:
        EmbeddingService Instanz
    """
    global _default_service

    if _default_service is None or _default_service.experimental != experimental:
        _default_service = EmbeddingService(experimental=experimental)

    return _default_service


def embed_text(text: str) -> np.ndarray:
    """
    Convenience-Funktion zum Embedden eines Textes.

    Args:
        text: Zu embeddender Text

    Returns:
        Embedding als numpy Array
    """
    service = get_embedding_service()
    return service.embed_single(text)


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Convenience-Funktion zum Embedden mehrerer Texte.

    Args:
        texts: Liste von Texten

    Returns:
        Embeddings als numpy Array (n_texts, dimensions)
    """
    service = get_embedding_service()
    result = service.embed(texts)
    return result.embeddings


# =============================================================================
# MAIN (Test)
# =============================================================================

if __name__ == "__main__":
    print("Testing EmbeddingService...")

    # Service erstellen
    service = EmbeddingService(experimental=False)

    # Test-Texte
    texts = [
        "Dies ist ein Test-Dokument über Verträge.",
        "Rechnung Nr. 12345 für Dienstleistungen.",
        "Technische Dokumentation für Software.",
    ]

    # Embeddings generieren
    result = service.embed(texts, show_progress=True)

    print(f"\nErgebnis:")
    print(f"  Model: {result.model_id}")
    print(f"  Dimensions: {result.dimensions}")
    print(f"  Shape: {result.embeddings.shape}")
    print(f"  Cached: {result.cached_count}")
    print(f"  Computed: {result.computed_count}")

    # Similarity Test
    from sklearn.metrics.pairwise import cosine_similarity
    sim = cosine_similarity(result.embeddings)
    print(f"\nSimilarity Matrix:")
    print(sim)
