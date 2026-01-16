"""
Neural Vault Reranker Configuration
===================================

Konfiguration für Reranking-Modelle mit A/B-Test Support.

Models:
- cross-electra-german: Schnell, German-optimiert, Cross-Encoder (baseline)
- Qwen3-Reranker-8B: SOTA-Qualität, multilingual (experimental)

Usage:
    from config.reranker_config import get_reranker_model, RERANKER_CONFIG
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class RerankerModel(Enum):
    """Verfügbare Reranking-Modelle."""
    # Aktuell (Baseline) - schnell, German-optimiert
    CROSS_ELECTRA_GERMAN = "svalabs/cross-electra-melange-german"
    
    # Qwen3-Reranker-8B (SOTA Quality, Multilingual)
    QWEN3_RERANKER_8B = "Qwen/Qwen3-Reranker-8B"
    
    # Alternative (multilingual baseline)
    MS_MARCO_MINILM = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@dataclass
class RerankerConfig:
    """Konfiguration für ein Reranking-Modell."""
    model_id: str
    max_tokens: int
    batch_size: int
    use_quantization: bool = False  # 4-bit quantization for VRAM savings
    device: str = "cuda"


# =============================================================================
# MODELL-KONFIGURATIONEN
# =============================================================================

RERANKER_CONFIGS = {
    RerankerModel.CROSS_ELECTRA_GERMAN: RerankerConfig(
        model_id="svalabs/cross-electra-melange-german",
        max_tokens=512,
        batch_size=32,
        use_quantization=False,
    ),
    
    RerankerModel.QWEN3_RERANKER_8B: RerankerConfig(
        model_id="Qwen/Qwen3-Reranker-8B",
        max_tokens=8192,
        batch_size=4,  # Reduced for 8GB VRAM
        use_quantization=True,  # 4-bit for RTX 2070
        device="cuda",
    ),
    
    RerankerModel.MS_MARCO_MINILM: RerankerConfig(
        model_id="cross-encoder/ms-marco-MiniLM-L-6-v2",
        max_tokens=512,
        batch_size=64,
        use_quantization=False,
    ),
}


# =============================================================================
# AKTIVE KONFIGURATION
# =============================================================================

# A/B Test: Baseline vs Experimental
RERANKER_MODEL_ACTIVE = RerankerModel.CROSS_ELECTRA_GERMAN  # Baseline
RERANKER_MODEL_EXPERIMENTAL = RerankerModel.QWEN3_RERANKER_8B  # A/B Test


def get_reranker_config(experimental: bool = False) -> RerankerConfig:
    """
    Holt die aktive Reranker-Konfiguration.
    
    Args:
        experimental: True für Qwen3-Reranker-8B
    
    Returns:
        RerankerConfig
    """
    model = RERANKER_MODEL_EXPERIMENTAL if experimental else RERANKER_MODEL_ACTIVE
    return RERANKER_CONFIGS[model]


def get_reranker_model(experimental: bool = False) -> str:
    """Holt die Model-ID."""
    config = get_reranker_config(experimental)
    return config.model_id


def get_ab_test_info() -> dict:
    """Informationen für A/B-Test Vergleich."""
    baseline = RERANKER_CONFIGS[RERANKER_MODEL_ACTIVE]
    experimental = RERANKER_CONFIGS[RERANKER_MODEL_EXPERIMENTAL]
    
    return {
        "baseline_model": baseline.model_id,
        "experimental_model": experimental.model_id,
        "baseline_max_tokens": baseline.max_tokens,
        "experimental_max_tokens": experimental.max_tokens,
        "experimental_uses_quantization": experimental.use_quantization,
    }
