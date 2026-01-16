"""
Neural Vault Embedding Configuration
====================================

Konfiguration für Embedding-Modelle mit A/B-Test Support.

Benchmark-basierte Empfehlung (MTEB 2025):
- Qwen3-Embedding 0.6B: Score 68.2, 100+ Sprachen
- multilingual-e5-large: Score 63.0 (aktuell)

Usage:
    from config.embeddings import get_embedding_model, EMBEDDING_CONFIG
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class EmbeddingModel(Enum):
    """Verfügbare Embedding-Modelle."""
    # Aktuell (Baseline)
    E5_LARGE = "intfloat/multilingual-e5-large"

    # Empfohlen (2025 Benchmark Winner)
    QWEN3_EMBEDDING_0_6B = "Alibaba-NLP/gte-Qwen3-Embedding-0.6B"
    QWEN3_EMBEDDING_1_5B = "Alibaba-NLP/gte-Qwen3-Embedding-1.5B"
    
    # Qwen3-Embedding-8B (Höchste Qualität, MTEB SOTA)
    QWEN3_EMBEDDING_8B = "Qwen/Qwen3-Embedding-8B"

    # Alternativen
    JINA_V3 = "jinaai/jina-embeddings-v3"
    BGE_M3 = "BAAI/bge-m3"


@dataclass
class EmbeddingConfig:
    """Konfiguration für ein Embedding-Modell."""
    model_id: str
    dimensions: int
    max_tokens: int
    batch_size: int
    normalize: bool = True
    device: str = "cuda"  # cuda, cpu, mps


# =============================================================================
# MODELL-KONFIGURATIONEN
# =============================================================================

EMBEDDING_CONFIGS = {
    # Aktuell (Baseline)
    EmbeddingModel.E5_LARGE: EmbeddingConfig(
        model_id="intfloat/multilingual-e5-large",
        dimensions=1024,
        max_tokens=512,
        batch_size=32,
    ),

    # Empfohlen (2025)
    EmbeddingModel.QWEN3_EMBEDDING_0_6B: EmbeddingConfig(
        model_id="Alibaba-NLP/gte-Qwen3-Embedding-0.6B",
        dimensions=1024,
        max_tokens=8192,
        batch_size=16,
    ),

    EmbeddingModel.QWEN3_EMBEDDING_1_5B: EmbeddingConfig(
        model_id="Alibaba-NLP/gte-Qwen3-Embedding-1.5B",
        dimensions=1536,
        max_tokens=8192,
        batch_size=8,
    ),

    EmbeddingModel.JINA_V3: EmbeddingConfig(
        model_id="jinaai/jina-embeddings-v3",
        dimensions=1024,
        max_tokens=8192,
        batch_size=16,
    ),

    EmbeddingModel.BGE_M3: EmbeddingConfig(
        model_id="BAAI/bge-m3",
        dimensions=1024,
        max_tokens=8192,
        batch_size=16,
    ),

    # Qwen3-Embedding-8B (MTEB SOTA, Highest Quality)
    EmbeddingModel.QWEN3_EMBEDDING_8B: EmbeddingConfig(
        model_id="Qwen/Qwen3-Embedding-8B",
        dimensions=4096,
        max_tokens=32768,
        batch_size=4,  # Reduced for 8GB VRAM
        device="cuda",
    ),
}


# =============================================================================
# AKTIVE KONFIGURATION
# =============================================================================

# Feature Flag für A/B-Test
EMBEDDING_MODEL_ACTIVE = EmbeddingModel.QWEN3_EMBEDDING_0_6B  # Aktuell
EMBEDDING_MODEL_EXPERIMENTAL = EmbeddingModel.E5_LARGE  # Test


def get_embedding_config(experimental: bool = False) -> EmbeddingConfig:
    """
    Holt die aktive Embedding-Konfiguration.

    Args:
        experimental: True für experimentelles Modell

    Returns:
        EmbeddingConfig
    """
    model = EMBEDDING_MODEL_EXPERIMENTAL if experimental else EMBEDDING_MODEL_ACTIVE
    return EMBEDDING_CONFIGS[model]


def get_embedding_model(experimental: bool = False) -> str:
    """Holt die Model-ID."""
    config = get_embedding_config(experimental)
    return config.model_id


# =============================================================================
# MIGRATION HELPER
# =============================================================================

def check_dimension_compatibility(old_dim: int, new_dim: int) -> bool:
    """
    Prüft ob Dimensionen kompatibel sind.

    Bei Wechsel der Dimensionen muss der gesamte
    Qdrant-Index neu aufgebaut werden!
    """
    return old_dim == new_dim


def get_migration_info() -> dict:
    """
    Informationen für die Embedding-Migration.
    """
    old_config = EMBEDDING_CONFIGS[EMBEDDING_MODEL_ACTIVE]
    new_config = EMBEDDING_CONFIGS[EMBEDDING_MODEL_EXPERIMENTAL]

    return {
        "old_model": old_config.model_id,
        "new_model": new_config.model_id,
        "dimension_change": old_config.dimensions != new_config.dimensions,
        "old_dimensions": old_config.dimensions,
        "new_dimensions": new_config.dimensions,
        "reindex_required": old_config.dimensions != new_config.dimensions,
        "estimated_improvement": "+5 MTEB points (~8% better retrieval)",
    }


# =============================================================================
# QDRANT COLLECTION CONFIG
# =============================================================================

def get_qdrant_collection_config(experimental: bool = False) -> dict:
    """
    Generiert Qdrant Collection-Konfiguration.
    """
    config = get_embedding_config(experimental)

    return {
        "vectors": {
            "size": config.dimensions,
            "distance": "Cosine",
        },
        "optimizers_config": {
            "indexing_threshold": 20000,
        },
        "hnsw_config": {
            "m": 16,
            "ef_construct": 100,
        },
    }
