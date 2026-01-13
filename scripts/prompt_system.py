"""
Neural Vault - Zentrales Prompt-System mit Anti-Halluzinations-Strategien
=========================================================================

Dieses Modul definiert alle LLM-Prompts zentral, sodass:
1. Alle Scripts dieselben optimierten Prompts verwenden
2. Bei LLM-Updates die Prompts bestehen bleiben
3. Anti-Halluzinations-Strategien einheitlich angewendet werden

Best Practices implementiert (Stand: Dezember 2025):
- Chain-of-Verification (CoVe)
- Abstention Instructions ("Ich weiss nicht")
- Grounding Requirements
- Low Temperature Settings
- Explicit JSON Schema Constraints
- Source Citation Requirements

Referenzen:
- machinelearningmastery.com: Prompt Engineering for Hallucination Prevention
- medium.com: Reducing LLM Hallucinations 2025
- ollama.com: Structured Outputs
- forbes.com: RAG and Grounding Techniques
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

# =============================================================================
# KONFIGURATION
# =============================================================================

# Diese Datei wird bei LLM-Updates NICHT ueberschrieben
PROMPT_VERSION = "2.0.0"
PROMPT_UPDATED = "2025-12-27"
MAX_TEXT_CHARS = 3000

# Empfohlene Ollama-Parameter fuer minimale Halluzination
RECOMMENDED_OPTIONS = {
    "temperature": 0.1,      # Sehr niedrig fuer deterministische Ausgaben
    "top_p": 0.9,            # Nucleus Sampling
    "top_k": 40,             # Begrenzt Vokabular
    "repeat_penalty": 1.1,   # Vermeidet Wiederholungen
    "num_predict": 1024,     # Max Tokens
}

# =============================================================================
# ANTI-HALLUZINATIONS-STRATEGIEN
# =============================================================================

ANTI_HALLUCINATION_RULES = """
WICHTIGE REGELN ZUR VERMEIDUNG VON HALLUZINATIONEN:

1. GROUNDING: Beziehe dich NUR auf Informationen die EXPLIZIT im Text stehen.
2. ABSTENTION: Wenn Information nicht vorhanden ist, antworte "Nicht im Dokument".
3. KEINE ANNAHMEN: Erfinde KEINE Daten, Zahlen oder Fakten.
4. ZITATION: Markiere jeden Fakt mit [QUELLE: im Text] oder [QUELLE: Dateiname].
5. UNSICHERHEIT: Bei Unsicherheit, gib confidence < 0.5 an.
6. BINAERDATEIEN: Bei Dateien ohne Text, extrahiere NUR was im Dateinamen steht.

VERBOTEN:
- Erfinden von Datumsangaben die nicht im Text sind
- Erfinden von Betraegen oder Zahlen
- Erfinden von Namen oder Organisationen
- Schlussfolgern ueber Inhalt der nicht da ist
- "Wahrscheinlich", "Vermutlich", "Koennte sein" ohne Kennzeichnung
"""

# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

@dataclass
class PromptTemplate:
    """Container fuer ein Prompt Template mit Metadaten."""
    name: str
    version: str
    purpose: str
    prompt: str
    expected_format: str
    anti_hallucination_level: str  # "strict", "moderate", "relaxed"
    
    def get_full_prompt(self, **kwargs) -> str:
        """Gibt vollstaendiges Prompt mit eingesetzten Variablen zurueck."""
        return self.prompt.format(**kwargs)


# =============================================================================
# KLASSIFIZIERUNGS-PROMPT (V2 - Anti-Halluzination)
# =============================================================================

CLASSIFICATION_PROMPT_V2 = PromptTemplate(
    name="file_classification_v2",
    version="2.0.0",
    purpose="Datei-Klassifizierung mit minimaler Halluzination",
    anti_hallucination_level="strict",
    expected_format="JSON",
    prompt="""Du bist ein FAKTEN-BASIERTES Klassifizierungssystem.

{anti_hallucination_rules}

=== EINGABE ===
Dateiname: {filename}
MIME-Type: {mime_type}
Textinhalt (falls vorhanden):
---
{text_content}
---

=== AUFGABE ===
Analysiere die Datei und extrahiere NUR Fakten die EXPLIZIT vorhanden sind.

=== AUSGABEFORMAT (NUR JSON, KEINE ANDEREN TEXTE) ===
{{
    "category": "Finanzen|Technologie|Arbeit|Privat|Medien|Dokumente|Sonstiges",
    "subcategory": "Rechnung|Vertrag|Code|Foto|Video|Email|Sonstiges",
    "confidence": 0.0-1.0,
    "confidence_reason": "Warum diese Konfidenz",
    
    "entities": {{
        "found_in_text": ["Entity1", "Entity2"],
        "found_in_filename": ["Entity3"]
    }},
    
    "dates": {{
        "found_in_text": ["2024-01-15"],
        "found_in_filename": []
    }},
    
    "amounts": {{
        "found_in_text": ["149.99 EUR"],
        "found_in_filename": []
    }},
    
    "key_facts": [
        {{"fact": "Beschreibung des Fakts", "source": "text|filename", "line": "Originalzeile"}}
    ],
    
    "document_type": "Rechnung|Vertrag|Email|Code|Bild|Video|Unbekannt",
    "language": "de|en|unknown",
    
    "extraction_quality": {{
        "has_text": true|false,
        "text_length": 0,
        "is_binary": true|false
    }},
    
    "warnings": ["Liste von Warnungen falls unsicher"]
}}

=== WICHTIGE HINWEISE ===
- Wenn KEIN Text vorhanden ist: Analysiere NUR den Dateinamen
- Wenn der Dateiname keine Informationen enthaelt: category="Sonstiges", confidence=0.5
- JEDER Fakt in key_facts MUSS mit Quellenangabe versehen sein
- Bei Binaerdateien ohne Text: extraction_quality.is_binary = true
"""
)


# =============================================================================
# ENTITY-EXTRACTION-PROMPT (V2 - Grounded)
# =============================================================================

ENTITY_EXTRACTION_PROMPT_V2 = PromptTemplate(
    name="entity_extraction_v2",
    version="2.0.0",
    purpose="Entity-Extraktion mit Grounding-Validierung",
    anti_hallucination_level="strict",
    expected_format="JSON",
    prompt="""Du bist ein PRAEZISES Entity-Extraction-System.

KRITISCH: Extrahiere NUR Entities die WOERTLICH im Text vorkommen.

=== TEXT ===
{text_content}

=== AUFGABE ===
Finde alle benannten Entitaeten (Personen, Orte, Organisationen, Produkte).

=== REGELN ===
1. JEDE Entity muss EXAKT so im Text stehen
2. Gib die ORIGINALSCHREIBWEISE an
3. Gib die POSITION (ungefaehre Zeilennummer) an
4. Wenn keine Entities: leere Liste zurueckgeben
5. KEINE ANNAHMEN - nur was da steht

=== AUSGABE (NUR JSON) ===
{{
    "entities": [
        {{
            "text": "Exakter Text wie im Original",
            "type": "PERSON|ORG|LOCATION|PRODUCT|DATE|AMOUNT|OTHER",
            "context": "...umgebende Woerter...",
            "grounded": true
        }}
    ],
    "extraction_notes": "Bemerkungen zur Extraktion"
}}
"""
)


# =============================================================================
# ZUSAMMENFASSUNGS-PROMPT (V2 - Faktenbasiert)
# =============================================================================

SUMMARIZATION_PROMPT_V2 = PromptTemplate(
    name="document_summary_v2",
    version="2.0.0",
    purpose="Faktenbasierte Zusammenfassung ohne Interpretation",
    anti_hallucination_level="moderate",
    expected_format="JSON",
    prompt="""Du bist ein OBJEKTIVES Zusammenfassungssystem.

{anti_hallucination_rules}

=== DOKUMENT ===
{text_content}

=== AUFGABE ===
Erstelle eine FAKTENBASIERTE Zusammenfassung.

=== REGELN ===
1. Fasse NUR zusammen was im Text steht
2. KEINE Interpretationen oder Schlussfolgerungen
3. Wenn unklar, schreibe "Unklar im Dokument"
4. Behalte wichtige Zahlen und Daten EXAKT bei

=== AUSGABE (NUR JSON) ===
{{
    "summary": "1-3 Saetze die den Inhalt objektiv beschreiben",
    "key_points": [
        "Punkt 1 [QUELLE: Zeile X]",
        "Punkt 2 [QUELLE: Zeile Y]"
    ],
    "important_data": {{
        "dates": ["Datum1", "Datum2"],
        "amounts": ["Betrag1"],
        "names": ["Name1"]
    }},
    "completeness": "vollstaendig|teilweise|minimal",
    "confidence": 0.0-1.0
}}
"""
)


# =============================================================================
# CHAIN-OF-VERIFICATION PROMPT
# =============================================================================

VERIFICATION_PROMPT = PromptTemplate(
    name="chain_of_verification",
    version="2.0.0",
    purpose="Selbst-Verifikation von LLM-Ausgaben",
    anti_hallucination_level="strict",
    expected_format="JSON",
    prompt="""Du bist ein FAKTEN-PRUEFER.

=== URSPRUENGLICHER TEXT ===
{original_text}

=== ZU PRUEFENDE BEHAUPTUNGEN ===
{claims_to_verify}

=== AUFGABE ===
Pruefe JEDE Behauptung gegen den Originaltext.

=== FUER JEDE BEHAUPTUNG ===
1. Ist die Behauptung WOERTLICH im Text? (grounded)
2. Ist sie SINNGEMÄSS im Text? (inferred)
3. Ist sie ERFUNDEN? (hallucinated)

=== AUSGABE (NUR JSON) ===
{{
    "verifications": [
        {{
            "claim": "Die Behauptung",
            "status": "grounded|inferred|hallucinated",
            "evidence": "Zitat aus dem Text oder 'Nicht gefunden'",
            "confidence": 0.0-1.0
        }}
    ],
    "overall_grounding_score": 0.0-1.0,
    "hallucination_detected": true|false,
    "recommendation": "accept|review|reject"
}}
"""
)


# =============================================================================
# PROMPT REGISTRY
# =============================================================================

class PromptRegistry:
    """
    Zentrale Registry fuer alle Prompts.
    Stellt sicher dass alle Scripts dieselben Prompts verwenden.
    """
    
    _instance = None
    _prompts: Dict[str, PromptTemplate] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Registriere alle Standard-Prompts."""
        self._prompts = {
            "classification": CLASSIFICATION_PROMPT_V2,
            "entity_extraction": ENTITY_EXTRACTION_PROMPT_V2,
            "summarization": SUMMARIZATION_PROMPT_V2,
            "verification": VERIFICATION_PROMPT,
        }
    
    def get_prompt(self, name: str) -> PromptTemplate:
        """Hole ein Prompt-Template nach Namen."""
        if name not in self._prompts:
            raise ValueError(f"Prompt '{name}' nicht gefunden. Verfuegbar: {list(self._prompts.keys())}")
        return self._prompts[name]
    
    def get_classification_prompt(self, 
                                   filename: str, 
                                   mime_type: str = "unknown",
                                   text_content: str = "") -> str:
        """Generiere den Klassifizierungs-Prompt mit allen Anti-Halluzinations-Regeln."""
        template = self._prompts["classification"]
        return template.get_full_prompt(
            anti_hallucination_rules=ANTI_HALLUCINATION_RULES,
            filename=filename,
            mime_type=mime_type,
            text_content=text_content[:MAX_TEXT_CHARS] if text_content else "[Kein Text extrahiert - Binaerdatei]"
        )
    
    def get_ollama_options(self, strict: bool = True) -> Dict[str, Any]:
        """Hole empfohlene Ollama-Optionen."""
        options = RECOMMENDED_OPTIONS.copy()
        if strict:
            options["temperature"] = 0.05  # Noch niedriger fuer strikt
        return options
    
    def get_version_info(self) -> Dict[str, str]:
        """Gibt Versionsinformationen zurueck."""
        return {
            "prompt_system_version": PROMPT_VERSION,
            "last_updated": PROMPT_UPDATED,
            "registered_prompts": list(self._prompts.keys()),
            "anti_hallucination_enabled": True
        }


# =============================================================================
# OLLAMA WRAPPER MIT ANTI-HALLUZINATION
# =============================================================================

import requests

class SafeOllamaClient:
    """
    Ollama-Client mit eingebauten Anti-Halluzinations-Massnahmen.
    
    Features:
    - Automatische Temperature-Kontrolle
    - Chain-of-Verification
    - Response-Validierung
    - Fallback bei Parse-Fehlern
    """
    
    def __init__(self, base_url: str = "http://localhost:11435", model: str = "qwen3:8b"):
        self.base_url = base_url
        self.model = model
        self.registry = PromptRegistry()
    
    def classify_file(self, 
                      filename: str, 
                      text_content: str = "",
                      mime_type: str = "unknown",
                      verify: bool = True) -> Dict[str, Any]:
        """
        Klassifiziere eine Datei mit Anti-Halluzinations-Massnahmen.
        
        Args:
            filename: Name der Datei
            text_content: Extrahierter Text
            mime_type: MIME-Type der Datei
            verify: Wenn True, fuehre Chain-of-Verification durch
        
        Returns:
            Klassifizierungsergebnis mit Grounding-Score
        """
        prompt = self.registry.get_classification_prompt(
            filename=filename,
            mime_type=mime_type,
            text_content=text_content
        )
        
        options = self.registry.get_ollama_options(strict=True)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": options
                },
                timeout=120
            )
            
            if response.ok:
                result_text = response.json().get("response", "{}")
                result = json.loads(result_text)
                
                # Fuege Metadaten hinzu
                result["_meta"] = {
                    "prompt_version": PROMPT_VERSION,
                    "model": self.model,
                    "anti_hallucination_enabled": True,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Optional: Chain-of-Verification
                if verify and result.get("key_facts"):
                    verification = self._verify_claims(
                        text_content, 
                        [f["fact"] for f in result.get("key_facts", []) if isinstance(f, dict)]
                    )
                    result["_verification"] = verification
                
                return result
                
        except json.JSONDecodeError:
            return self._fallback_classification(filename, mime_type)
        except Exception as e:
            return {
                "error": str(e),
                "category": "Sonstiges",
                "confidence": 0.0
            }
    
    def _verify_claims(self, original_text: str, claims: List[str]) -> Dict[str, Any]:
        """Fuehre Chain-of-Verification fuer Behauptungen durch."""
        if not claims or not original_text:
            return {"status": "skipped", "reason": "no_claims_or_text"}
        
        template = self.registry.get_prompt("verification")
        prompt = template.get_full_prompt(
            original_text=original_text[:2000],
            claims_to_verify=json.dumps(claims, ensure_ascii=False)
        )
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.05}
                },
                timeout=60
            )
            
            if response.ok:
                return json.loads(response.json().get("response", "{}"))
        except:
            pass
        
        return {"status": "error"}
    
    def _fallback_classification(self, filename: str, mime_type: str) -> Dict[str, Any]:
        """Minimal-Klassifizierung wenn LLM fehlschlaegt."""
        return {
            "category": "Sonstiges",
            "subcategory": "Unbekannt",
            "confidence": 0.3,
            "confidence_reason": "Fallback - LLM Parse Error",
            "entities": {"found_in_text": [], "found_in_filename": []},
            "key_facts": [],
            "extraction_quality": {"has_text": False, "is_binary": True},
            "warnings": ["LLM-Ausgabe konnte nicht geparst werden"]
        }


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def get_prompt_registry() -> PromptRegistry:
    """Gibt die globale Prompt-Registry zurueck."""
    return PromptRegistry()

def get_safe_ollama_client(model: str = "qwen3:8b") -> SafeOllamaClient:
    """Gibt einen konfigurierten SafeOllamaClient zurueck."""
    return SafeOllamaClient(model=model)


# =============================================================================
# CLI / STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("NEURAL VAULT - PROMPT SYSTEM")
    print("=" * 60)
    
    registry = get_prompt_registry()
    info = registry.get_version_info()
    
    print(f"Version: {info['prompt_system_version']}")
    print(f"Updated: {info['last_updated']}")
    print(f"Prompts: {', '.join(info['registered_prompts'])}")
    print(f"Anti-Halluzination: {'Aktiv' if info['anti_hallucination_enabled'] else 'Inaktiv'}")
    print()
    
    # Beispiel-Klassifizierung
    print("Teste Klassifizierungs-Prompt...")
    prompt = registry.get_classification_prompt(
        filename="Rechnung_Amazon_2024-12-15.pdf",
        mime_type="application/pdf",
        text_content="Amazon Bestellung #123-456\nBetrag: 49,99 EUR\nDatum: 15.12.2024"
    )
    print(f"Prompt-Laenge: {len(prompt)} Zeichen")
    print("OK!")
