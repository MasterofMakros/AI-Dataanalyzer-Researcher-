"""
Neural Vault Feature Flags
==========================

Status-Werte:
- ACTIVE: Produktiv im Einsatz
- EXPERIMENTAL: In Testphase (A/B-Test)
- PROPOSED: Geplant, noch nicht implementiert
- DEPRECATED: Abgekündigt, wird entfernt
- REJECTED: Getestet und abgelehnt
- REMOVED: Komplett entfernt
"""

FEATURE_FLAGS = {
    # =========================================================================
    # CLASSIFICATION
    # =========================================================================
    "USE_GLINER_CLASSIFICATION": (True, "ACTIVE"),
    "USE_OLLAMA_CLASSIFICATION": (False, "REMOVED"),

    # =========================================================================
    # SEARCH
    # =========================================================================
    "ENABLE_RERANKING": (False, "REJECTED"),
    "USE_HYBRID_SEARCH": (True, "ACTIVE"),

    # =========================================================================
    # EXTRACTION
    # =========================================================================
    "USE_DATA_NARRATOR": (True, "ACTIVE"),
    "USE_DOCLING_PDF": (True, "ACTIVE"),
    "USE_PII_MASKING": (True, "ACTIVE"),
    "USE_ENHANCED_EXTRACTION": (True, "ACTIVE"),  # Magic Bytes + HTML→Markdown

    # =========================================================================
    # A/B TESTS (2025-12 Benchmark-basiert)
    # =========================================================================
    # Embedding: e5-large vs Qwen3-Embedding
    "USE_QWEN3_EMBEDDING": (True, "ACTIVE"),

    # =========================================================================
    # PROCESSOR SELECTION (Benchmark-driven)
    # =========================================================================
    # OCR: Surya (97.7%) vs Tesseract (87%)
    "USE_SURYA_OCR": (True, "ACTIVE"),  # docker/document-processor

    # Parser: Docling (97.9%) vs Tika (75% tables)
    "USE_DOCLING_FIRST": (True, "ACTIVE"),  # scripts/services/extraction_service.py

    # Audio: WhisperX with diarization
    "USE_WHISPERX": (True, "ACTIVE"),  # docker/whisperx

    # =========================================================================
    # PARSER ROUTING
    # =========================================================================
    "USE_PARSER_ROUTING": (True, "ACTIVE"),  # scripts/services/extraction_service.py
    "USE_FALLBACK_CHAIN": (True, "ACTIVE"),  # Fallback bei Parser-Fehler

    # =========================================================================
    # INTELLIGENCE PIPELINE
    # =========================================================================
    "USE_UNIVERSAL_ROUTER": (True, "ACTIVE"),  # docker/universal-router
    "USE_PRIORITY_QUEUES": (True, "ACTIVE"),   # docker/orchestrator
    "USE_VECTOR_STORE": (True, "ACTIVE"),      # LanceDB in document-processor
}

def is_enabled(feature: str) -> bool:
    """Prüft ob ein Feature aktiviert ist."""
    return FEATURE_FLAGS.get(feature, (False,))[0]


def get_status(feature: str) -> str:
    """Gibt den Status eines Features zurück."""
    return FEATURE_FLAGS.get(feature, (False, "UNKNOWN"))[1]


def is_experimental(feature: str) -> bool:
    """Prüft ob ein Feature experimentell ist."""
    return get_status(feature) == "EXPERIMENTAL"


def list_by_status(status: str) -> list:
    """Listet alle Features mit einem bestimmten Status."""
    return [
        name for name, (enabled, s) in FEATURE_FLAGS.items()
        if s == status
    ]


def get_ab_test_features() -> dict:
    """Gibt alle A/B-Test Features zurück."""
    return {
        name: {"enabled": enabled, "status": status}
        for name, (enabled, status) in FEATURE_FLAGS.items()
        if status == "EXPERIMENTAL"
    }


def enable_feature(feature: str) -> bool:
    """
    Aktiviert ein Feature zur Laufzeit.
    ACHTUNG: Nicht persistent!
    """
    if feature in FEATURE_FLAGS:
        status = FEATURE_FLAGS[feature][1]
        FEATURE_FLAGS[feature] = (True, status)
        return True
    return False


def disable_feature(feature: str) -> bool:
    """
    Deaktiviert ein Feature zur Laufzeit.
    ACHTUNG: Nicht persistent!
    """
    if feature in FEATURE_FLAGS:
        status = FEATURE_FLAGS[feature][1]
        FEATURE_FLAGS[feature] = (False, status)
        return True
    return False
