
"""
Feature: GLiNER Classification (Experimental)
Status: EXPERIMENTAL
Candidate for: ABT-R02
Depends on: neural-worker (Port 8005)
"""

import requests
import json
from typing import Dict, Any, List

NEURAL_WORKER_URL = "http://localhost:8005"

class GLiNERClassifier:
    """Klassifikation via GLiNER Entities + Regelwerk."""

    def classify(self, text: str, filename: str) -> Dict[str, Any]:
        """
        1. Extract Entities via GLiNER (neural-worker).
        2. Apply Heuristics to determine category.
        """
        
        # 1. Call Neural Worker
        try:
            # Labels we care about for categorization
            labels = ["person", "organization", "iban", "date", "money", "email", "phone", "tax_id"]
            
            response = requests.post(
                f"{NEURAL_WORKER_URL}/process/pii",
                json={"text": text[:2000], "labels": labels}, # Limit text for speed
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"[WARN] GLiNER API Error: {response.text}")
                return self._fallback_result(filename)
                
            entities = response.json().get("entities", [])
            
        except Exception as e:
            print(f"[WARN] GLiNER Connection Error: {e}")
            return self._fallback_result(filename)

        # 2. Rule-Based Categorization
        category = self._apply_rules(entities, text, filename)
        
        # 3. Extract Metadata
        main_entity = self._extract_main_entity(entities, filename)
        date = self._extract_date(entities)
        
        return {
            "category": category,
            "subcategory": "Automatisch",
            "entity": main_entity,
            "date": date,
            "confidence": 0.85, # GLiNER is usually confident
            "meta_description": f"GLiNER Entities: {len(entities)} found.",
            "tags": [e["label"] for e in entities],
            "_classifier_model": "gliner_medium-v2.1"
        }

    def _apply_rules(self, entities: List[Dict], text: str, filename: str) -> str:
        """Heuristic Rules for Category."""
        
        labels = [e["label"] for e in entities]
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Rule 1: Work / Contracts (Highest Priority)
        if "vertrag" in text_lower or "contract" in text_lower:
            return "Arbeit"
        if "arbeits" in text_lower or "salary" in text_lower or "gehalt" in text_lower:
            return "Arbeit"
            
        # Rule 2: Finance
        if "iban" in labels or "tax_id" in labels:
            return "Finanzen"
        if "money" in labels:
            if "rechnung" in filename_lower or "invoice" in filename_lower:
                return "Finanzen"
            # If money but no invoice keyword, could be anything?
            # Default to Finanzen if money amount is found is a strong signal usually
            return "Finanzen"
                
        # Rule 3: Communication
        if "email" in labels or "phone" in labels:
             # Only if not already classified as Work
            return "Arbeit" 
            
        # Rule 4: Date-heavy (Logs, Reports)
        if labels.count("date") > 3:
            return "Dokumente"
            
        # Rule 5: Health
        if "arzt" in text_lower or "diagnose" in text_lower: return "Gesundheit"
        if "versicher" in text_lower: return "Finanzen"
        
        return "Sonstiges"

    def _extract_main_entity(self, entities: List[Dict], filename: str) -> str:
        # Prioritize Organization -> Person -> Filename
        for e in entities:
            if e["label"] == "organization":
                return e["text"]
        for e in entities:
            if e["label"] == "person":
                return e["text"]
        return filename[:20]

    def _extract_date(self, entities: List[Dict]) -> str:
        for e in entities:
            if e["label"] == "date":
                return e["text"]
        return ""

    def _fallback_result(self, filename: str):
        return {
            "category": "Sonstiges",
            "subcategory": "Error",
            "entity": filename[:20],
            "confidence": 0.0,
            "tags": [],
            "_error": "gliner_unavailable"
        }
