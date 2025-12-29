
"""
Feature: Ollama Classification (Legacy)
Status: DEPRECATED
Superseded by: GLiNER Rules (neural-worker)
ADR: ADR-010-classification-method.md
A/B-Test: ABT-R02
"""

import requests
import json
from pathlib import Path
from typing import Dict, Any

OLLAMA_URL = "http://localhost:11435"

class OllamaClassifier:
    """Klassifikation via Ollama (Legacy Implementation)."""

    def classify(self, text: str, filename: str) -> Dict[str, Any]:
        """Original implementation from smart_ingest.py"""
        
        # 1. Prompt-System (wenn verfügbar)
        try:
            # Hacky import specific to this project structure
            import sys
            from config.paths import SCRIPTS_DIR
            sys.path.append(str(SCRIPTS_DIR)) 
            from prompt_system import get_safe_ollama_client, PROMPT_VERSION
            
            client = get_safe_ollama_client()
            result = client.classify_file(
                filename=filename,
                text_content=text,
                mime_type="unknown",
                verify=False
            )
            
            return {
                "category": result.get("category", "Sonstiges"),
                "subcategory": result.get("subcategory", "Unbekannt"),
                "entity": result.get("entities", {}).get("found_in_filename", [""])[0] if result.get("entities") else filename[:20],
                "date": result.get("dates", {}).get("found_in_text", [""])[0] if result.get("dates") else "",
                "confidence": result.get("confidence", 0.6),
                "meta_description": result.get("summary", f"Klassifiziert mit Prompt v{PROMPT_VERSION}"),
                "tags": result.get("tags", []),
                "_prompt_version": PROMPT_VERSION,
                "_anti_hallucination": True
            }
            
        except Exception as e:
            # Fallback Logic
            pass

        # 2. Fallback Logic
        if len(text) < 20:
            text = f"Dateiname: {filename}"
        
        prompt = f"""Du bist ein Datei-Klassifizierungssystem. Analysiere diese Datei und antworte NUR mit validem JSON.
        Dateiname: {filename}
        Inhalt (Auszug): {text[:1500]}
        
        JSON Format:
        {{
            "category": "Technologie",
            "subcategory": "Dokumentation",
            "entity": "NeuralVault",
            "date": "",
            "confidence": 0.8,
            "meta_description": "Beschreibung",
            "tags": ["tag1"]
        }}
        """
        
        default_result = {
            "category": "Sonstiges",
            "subcategory": "Unbekannt",
            "entity": Path(filename).stem[:20],
            "confidence": 0.6,
            "tags": [],
            "_prompt_version": "fallback"
        }

        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "qwen3:8b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.1}
                },
                timeout=120
            )
            if response.status_code == 200:
                result_text = response.json().get("response", "{}")
                parsed = json.loads(result_text)
                parsed["_prompt_version"] = "fallback"
                return parsed
                
        except Exception:
            pass
            
        return default_result
