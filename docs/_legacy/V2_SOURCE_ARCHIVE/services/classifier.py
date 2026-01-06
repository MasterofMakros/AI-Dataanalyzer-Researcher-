
"""
Classification Router Service
Status: ACTIVE
Routes requests to the active classification implementation based on Feature Flags.
"""

from typing import Dict, Any
from config.feature_flags import is_enabled

class ClassificationRouter:
    """Routet zu aktiver oder experimenteller Implementierung."""

    def __init__(self):
        if is_enabled("USE_GLINER_CLASSIFICATION"):
            from scripts.experimental.gliner_classifier import GLiNERClassifier
            self._impl = GLiNERClassifier()
            self._version = "v2-gliner-experimental"
            print(f"[INFO] Classification Router: Using GLiNER ({self._version})")
        else:
            from scripts.deprecated.ollama_classifier import OllamaClassifier
            self._impl = OllamaClassifier()
            self._version = "v1-ollama-deprecated"
            print(f"[INFO] Classification Router: Using Ollama ({self._version})")

    def classify(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Klassifiziere Dokument.
        Delegiert an die aktive Implementierung.
        """
        result = self._impl.classify(text, filename)
        
        # Add metadata about which classifier was used
        result["_classifier_version"] = self._version
        
        return result
