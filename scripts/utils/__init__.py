"""
Neural Vault Utils Package
==========================

Gemeinsame Utility-Module für das Neural Vault Projekt.
"""

from .context_header import (
    SourceType,
    ChunkLocation,
    wrap_chunk,
    unwrap_chunk,
    create_chunk_for_rag,
    detect_source_type,
    format_timestamp
)

from .feedback_tracker import (
    FeedbackTracker,
    CorrectionEvent,
    detect_manual_move
)

__all__ = [
    # Context Header
    "SourceType",
    "ChunkLocation",
    "wrap_chunk",
    "unwrap_chunk",
    "create_chunk_for_rag",
    "detect_source_type",
    "format_timestamp",
    # Feedback Tracker
    "FeedbackTracker",
    "CorrectionEvent",
    "detect_manual_move"
]
