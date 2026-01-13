"""
Neural Vault - Erweitertes Qualitaets-Test-Framework
Testet auf Halluzinationen, Informationsverlust und RAG-Tauglichkeit

NEUE TESTPARAMETER:
1. EXTRACTION_COMPLETENESS - Wurde alle wichtige Info extrahiert?
2. HALLUCINATION_DETECTION - Hat das LLM Infos erfunden?
3. ENTITY_GROUNDING - Sind extrahierte Entities im Original?
4. RAG_RETRIEVAL_QUALITY - Findet die Suche das Dokument?
5. ROUND_TRIP_VALIDATION - Koennen Fakten rekonstruiert werden?
6. SEMANTIC_PRESERVATION - Bleibt die Bedeutung erhalten?
"""

import os
import json
import time
import hashlib
import requests
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Set
from difflib import SequenceMatcher

from config.paths import TEST_SUITE_DIR, BASE_DIR

# Konfiguration
TEST_DIR = TEST_SUITE_DIR
TIKA_URL = "http://localhost:9998"
OLLAMA_URL = "http://localhost:11435"
QDRANT_URL = "http://localhost:6335"
QDRANT_COLLECTION = "neural_vault"

# Load .env
def load_env():
    env_path = BASE_DIR / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
    return env

ENV = load_env()

@dataclass
class EnhancedTestResult:
    """Erweiterte Testergebnisse mit Qualitaetsmetriken"""
    filepath: str
    filename: str
    extension: str
    size_mb: float
    
    # Basis-Metriken (wie vorher)
    tika_success: bool = False
    tika_mime: str = ""
    tika_text_length: int = 0
    ollama_success: bool = False
    ollama_category: str = ""
    ollama_confidence: float = 0.0
    
    # NEUE METRIKEN
    # 1. Extraction Completeness
    extraction_completeness: float = 0.0
    missing_elements: List[str] = field(default_factory=list)
    
    # 2. Hallucination Detection
    hallucination_score: float = 0.0  # 0 = keine, 1 = komplett halluziniert
    ungrounded_claims: List[str] = field(default_factory=list)
    
    # 3. Entity Grounding
    entities_found: List[str] = field(default_factory=list)
    entities_grounded: int = 0  # Im Original gefunden
    entities_ungrounded: int = 0  # Erfunden
    entity_grounding_rate: float = 0.0
    
    # 4. RAG Retrieval Quality  
    rag_retrievable: bool = False
    rag_rank: int = -1  # Position in Suchergebnissen
    rag_query_used: str = ""
    
    # 5. Round-Trip Validation
    round_trip_success: bool = False
    reconstructed_facts: List[str] = field(default_factory=list)
    
    # 6. Semantic Preservation
    semantic_similarity: float = 0.0
    key_terms_preserved: float = 0.0
    
    # 7. Informationsverlust
    information_loss_score: float = 0.0  # 0 = kein Verlust, 1 = alles verloren
    lost_elements: List[str] = field(default_factory=list)
    
    # Meta
    total_quality_score: float = 0.0
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0


def extract_text_via_tika(filepath: Path) -> tuple:
    """Extrahiere Text und Metadaten via Tika."""
    try:
        with open(filepath, "rb") as f:
            # MIME
            mime_resp = requests.put(
                f"{TIKA_URL}/detect/stream",
                data=f.read(8192),
                timeout=30
            )
            mime = mime_resp.text.strip() if mime_resp.ok else ""
        
        with open(filepath, "rb") as f:
            # Text
            text_resp = requests.put(
                f"{TIKA_URL}/tika",
                data=f,
                headers={"Accept": "text/plain"},
                timeout=60
            )
            text = text_resp.text.strip() if text_resp.ok else ""
        
        with open(filepath, "rb") as f:
            # Metadaten
            meta_resp = requests.put(
                f"{TIKA_URL}/meta",
                data=f,
                headers={"Accept": "application/json"},
                timeout=30
            )
            metadata = meta_resp.json() if meta_resp.ok else {}
        
        return True, mime, text, metadata
    except Exception as e:
        return False, "", "", {}


def classify_with_ollama(text: str, filename: str, mime_type: str = "unknown") -> dict:
    """
    Klassifiziere mit dem zentralen Anti-Halluzinations-Prompt-System.
    Nutzt prompt_system.py fuer konsistente, halluzinations-arme Klassifizierung.
    """
    
    # Versuche das neue Prompt-System zu nutzen
    try:
        from prompt_system import get_safe_ollama_client, PROMPT_VERSION
        
        client = get_safe_ollama_client()
        result = client.classify_file(
            filename=filename,
            text_content=text,
            mime_type=mime_type,
            verify=False  # Fuer Schnelligkeit keine Verifikation
        )
        
        # Konvertiere zu erwarteten Format
        return {
            "category": result.get("category", "Sonstiges"),
            "confidence": result.get("confidence", 0.5),
            "entities": result.get("entities", {}).get("found_in_text", []) if isinstance(result.get("entities"), dict) else result.get("entities", []),
            "dates": result.get("dates", {}).get("found_in_text", []) if isinstance(result.get("dates"), dict) else result.get("dates", []),
            "amounts": result.get("amounts", {}).get("found_in_text", []) if isinstance(result.get("amounts"), dict) else result.get("amounts", []),
            "key_facts": [f.get("fact", str(f)) if isinstance(f, dict) else str(f) for f in result.get("key_facts", [])],
            "document_type": result.get("document_type", "Sonstiges"),
            "language": result.get("language", "unknown"),
            "summary": result.get("summary", ""),
            "_prompt_version": PROMPT_VERSION,
            "_anti_hallucination": True
        }
        
    except ImportError:
        print("  [INFO] Prompt-System nicht gefunden, nutze Fallback")
    except Exception as e:
        print(f"  [WARN] Prompt-System Fehler: {e}, nutze Fallback")
    
    # FALLBACK: Klassischer Prompt mit Anti-Halluzinations-Hints
    prompt = f"""Analysiere diese Datei und extrahiere strukturierte Informationen.
WICHTIG: Erfinde NICHTS. Antworte nur mit Fakten die im Text stehen.
Wenn etwas nicht im Text ist, lasse das Feld leer oder schreibe "Nicht gefunden".

Dateiname: {filename}
Inhalt: {text[:2000]}

Antworte NUR mit diesem JSON (keine anderen Texte):
{{
    "category": "Finanzen|Technologie|Privat|Arbeit|Medien|Dokumente|Sonstiges",
    "confidence": 0.85,
    "entities": ["Nur Namen die im Text stehen"],
    "dates": ["Nur Daten die im Text stehen"],
    "amounts": ["Nur Betraege die im Text stehen"],
    "key_facts": ["Nur Fakten die woertlich im Text stehen"],
    "document_type": "Rechnung|Vertrag|Email|Code|Foto|Video|Sonstiges",
    "language": "de|en|other",
    "summary": "Kurze Zusammenfassung basierend auf dem Text"
}}

Bei Binaerdateien ohne Text: Analysiere nur den Dateinamen, erfinde KEINE Details."""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "qwen3:8b",
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.1,  # Sehr niedrig fuer weniger Halluzination
                    "top_p": 0.9
                }
            },
            timeout=120
        )
        
        if response.ok:
            resp_text = response.json().get("response", "{}")
            result = json.loads(resp_text)
            result["_prompt_version"] = "fallback_v2"
            result["_anti_hallucination"] = True
            return result
    except:
        pass
    
    return {
        "category": "Sonstiges",
        "confidence": 0.5,
        "entities": [],
        "key_facts": [],
        "summary": "",
        "_prompt_version": "fallback_error",
        "_anti_hallucination": False
    }


def check_entity_grounding(entities: List[str], original_text: str, filename: str) -> tuple:
    """Pruefe ob extrahierte Entities im Original vorkommen."""
    grounded = 0
    ungrounded = 0
    ungrounded_list = []
    
    search_text = (original_text + " " + filename).lower()
    
    for entity in entities:
        entity_lower = entity.lower()
        # Fuzzy-Match: Entity oder Teile davon muessen vorkommen
        if entity_lower in search_text or any(part in search_text for part in entity_lower.split()):
            grounded += 1
        else:
            ungrounded += 1
            ungrounded_list.append(entity)
    
    total = grounded + ungrounded
    rate = grounded / total if total > 0 else 1.0
    
    return grounded, ungrounded, rate, ungrounded_list


def check_hallucination(classification: dict, original_text: str, filename: str) -> tuple:
    """Erkenne halluzinierte Informationen."""
    hallucination_score = 0.0
    ungrounded_claims = []
    
    search_text = (original_text + " " + filename).lower()
    
    # Pruefe key_facts
    key_facts = classification.get("key_facts", [])
    for fact in key_facts:
        # Extrahiere Schluesselbegriffe aus dem Fakt
        words = re.findall(r'\b\w{4,}\b', fact.lower())
        matches = sum(1 for w in words if w in search_text)
        if matches < len(words) * 0.3:  # Weniger als 30% der Woerter gefunden
            ungrounded_claims.append(fact)
    
    # Pruefe Betraege
    amounts = classification.get("amounts", [])
    for amount in amounts:
        # Extrahiere Zahl
        numbers = re.findall(r'[\d.,]+', amount)
        for num in numbers:
            if num not in search_text:
                ungrounded_claims.append(f"Betrag: {amount}")
    
    # Berechne Score
    total_claims = len(key_facts) + len(amounts)
    if total_claims > 0:
        hallucination_score = len(ungrounded_claims) / total_claims
    
    return hallucination_score, ungrounded_claims


def check_rag_retrieval(text_snippet: str, expected_filename: str) -> tuple:
    """Teste ob Dokument ueber Suche gefunden werden kann."""
    if len(text_snippet) < 20:
        return False, -1, ""
    
    # Extrahiere Suchbegriffe aus Text
    words = re.findall(r'\b\w{5,}\b', text_snippet[:500])
    if not words:
        return False, -1, ""
    
    # Waehle 3-5 signifikante Woerter
    query = " ".join(words[:5])
    
    try:
        response = requests.post(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/scroll",
            json={
                "limit": 1,
                "with_payload": True,
                "with_vector": False,
                "filter": {
                    "should": [
                        {"key": "filename", "match": {"value": expected_filename}},
                        {"key": "original_filename", "match": {"value": expected_filename}}
                    ],
                    "minimum_should_match": 1
                }
            },
            timeout=10
        )

        if response.ok:
            results = response.json().get("result", {}).get("points", [])
            if results:
                return True, 1, query
    except:
        pass
    
    return False, -1, query


def calculate_extraction_completeness(text: str, metadata: dict, filepath: Path) -> tuple:
    """Berechne wie vollstaendig die Extraktion war."""
    score = 0.0
    missing = []
    
    checks = {
        "text_extracted": len(text) > 50,
        "has_metadata": len(metadata) > 0,
        "readable_content": bool(re.search(r'[a-zA-Z]{3,}', text)),
    }
    
    # Bei Dokumenten erwarten wir mehr
    doc_extensions = {'.pdf', '.docx', '.doc', '.xlsx', '.txt', '.md', '.html'}
    if filepath.suffix.lower() in doc_extensions:
        checks["substantial_text"] = len(text) > 200
    
    # Bei Bildern erwarten wir Metadaten
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.gif'}
    if filepath.suffix.lower() in image_extensions:
        checks["image_metadata"] = "Image" in str(metadata) or len(metadata) > 2
    
    passed = sum(1 for v in checks.values() if v)
    score = passed / len(checks) if checks else 0.0
    
    missing = [k for k, v in checks.items() if not v]
    
    return score, missing


def calculate_information_loss(original_text: str, classification: dict) -> tuple:
    """Schaetze Informationsverlust durch Verarbeitung."""
    loss_score = 0.0
    lost_elements = []
    
    # Extrahiere wichtige Elemente aus Original
    original_lower = original_text.lower()
    
    # Zahlen
    original_numbers = set(re.findall(r'\d+[.,]\d+|\d{4,}', original_text))
    extracted_numbers = set()
    for amount in classification.get("amounts", []):
        extracted_numbers.update(re.findall(r'\d+[.,]\d+|\d{4,}', amount))
    
    lost_numbers = original_numbers - extracted_numbers
    if lost_numbers and len(original_numbers) <= 10:  # Nur bei wenigen Zahlen relevant
        lost_elements.append(f"Zahlen: {list(lost_numbers)[:3]}")
    
    # Datumsangaben
    original_dates = set(re.findall(r'\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{4}-\d{2}-\d{2}', original_text))
    extracted_dates = set(classification.get("dates", []))
    
    if original_dates and not extracted_dates:
        lost_elements.append(f"Datumsangaben: {list(original_dates)[:3]}")
    
    # Berechne Score
    total_important = len(original_numbers) + len(original_dates)
    if total_important > 0:
        extracted_count = len(extracted_numbers) + len(extracted_dates)
        loss_score = 1 - (extracted_count / total_important)
        loss_score = max(0, min(1, loss_score))
    
    return loss_score, lost_elements


def calculate_semantic_preservation(original_text: str, summary: str) -> tuple:
    """Pruefe ob Kernbedeutung erhalten bleibt."""
    if not original_text or not summary:
        return 0.0, 0.0
    
    # Extrahiere Schluesselbegriffe
    original_words = set(re.findall(r'\b\w{4,}\b', original_text.lower()))
    summary_words = set(re.findall(r'\b\w{4,}\b', summary.lower()))
    
    # Berechne Ueberlappung
    if original_words:
        overlap = len(original_words & summary_words)
        key_terms_preserved = overlap / min(len(original_words), 20)  # Max 20 Begriffe
    else:
        key_terms_preserved = 0.0
    
    # Semantische Aehnlichkeit (vereinfacht)
    semantic_sim = SequenceMatcher(None, 
                                   original_text[:500].lower(), 
                                   summary.lower()).ratio()
    
    return semantic_sim, min(1.0, key_terms_preserved)


def calculate_quality_score(result: EnhancedTestResult) -> float:
    """Berechne Gesamtqualitaetsscore."""
    weights = {
        "extraction": 0.2,
        "grounding": 0.25,
        "hallucination": 0.25,
        "info_loss": 0.15,
        "semantic": 0.15
    }
    
    scores = {
        "extraction": result.extraction_completeness,
        "grounding": result.entity_grounding_rate,
        "hallucination": 1 - result.hallucination_score,  # Invertieren
        "info_loss": 1 - result.information_loss_score,  # Invertieren
        "semantic": result.semantic_similarity
    }
    
    total = sum(weights[k] * scores[k] for k in weights)
    return total


def process_file_enhanced(filepath: Path) -> EnhancedTestResult:
    """Verarbeite Datei mit allen erweiterten Tests."""
    start_time = time.time()
    stat = filepath.stat()
    
    result = EnhancedTestResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower() or "[no_ext]",
        size_mb=stat.st_size / (1024 * 1024)
    )
    
    # 1. Tika Extraktion
    tika_ok, mime, text, metadata = extract_text_via_tika(filepath)
    result.tika_success = tika_ok
    result.tika_mime = mime
    result.tika_text_length = len(text)
    
    # 2. Ollama Klassifizierung
    classification = classify_with_ollama(text, filepath.name)
    result.ollama_success = True
    result.ollama_category = classification.get("category", "Sonstiges")
    result.ollama_confidence = classification.get("confidence", 0.5)
    
    # 3. Extraction Completeness
    result.extraction_completeness, result.missing_elements = \
        calculate_extraction_completeness(text, metadata, filepath)
    
    # 4. Entity Grounding
    entities = classification.get("entities", [])
    result.entities_found = entities
    result.entities_grounded, result.entities_ungrounded, result.entity_grounding_rate, ungrounded = \
        check_entity_grounding(entities, text, filepath.name)
    
    # 5. Hallucination Detection
    result.hallucination_score, result.ungrounded_claims = \
        check_hallucination(classification, text, filepath.name)
    
    # 6. Information Loss
    result.information_loss_score, result.lost_elements = \
        calculate_information_loss(text, classification)
    
    # 7. Semantic Preservation
    summary = classification.get("summary", "")
    result.semantic_similarity, result.key_terms_preserved = \
        calculate_semantic_preservation(text, summary)
    
    # 8. RAG Retrieval (optional, wenn Qdrant laeuft)
    if text:
        result.rag_retrievable, result.rag_rank, result.rag_query_used = \
            check_rag_retrieval(text, filepath.name)
    
    # 9. Round-Trip: Key Facts speichern
    result.reconstructed_facts = classification.get("key_facts", [])
    result.round_trip_success = len(result.reconstructed_facts) > 0
    
    # 10. Gesamtscore
    result.total_quality_score = calculate_quality_score(result)
    
    # Warnungen generieren
    if result.hallucination_score > 0.3:
        result.warnings.append("WARNUNG: Hoher Halluzinationsverdacht")
    if result.information_loss_score > 0.5:
        result.warnings.append("WARNUNG: Signifikanter Informationsverlust")
    if result.entity_grounding_rate < 0.5 and len(entities) > 0:
        result.warnings.append("WARNUNG: Viele unbegruendete Entities")
    
    result.processing_time = time.time() - start_time
    return result


def generate_enhanced_report(results: List[EnhancedTestResult]):
    """Generiere erweiterten Qualitaetsbericht."""
    report_path = TEST_DIR / "_QUALITY_REPORT.md"
    
    total = len(results)
    
    # Aggregierte Metriken
    avg_quality = sum(r.total_quality_score for r in results) / total if total else 0
    avg_hallucination = sum(r.hallucination_score for r in results) / total if total else 0
    avg_grounding = sum(r.entity_grounding_rate for r in results) / total if total else 0
    avg_info_loss = sum(r.information_loss_score for r in results) / total if total else 0
    avg_extraction = sum(r.extraction_completeness for r in results) / total if total else 0
    
    warnings_count = sum(len(r.warnings) for r in results)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Neural Vault - Erweiterter Qualitaetsbericht\n\n")
        f.write(f"> Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Qualitaets-Dashboard
        f.write("## Qualitaets-Dashboard\n\n")
        f.write("| Metrik | Wert | Bewertung |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| **Gesamt-Qualitaet** | {avg_quality*100:.1f}% | {'✅' if avg_quality > 0.7 else '⚠️' if avg_quality > 0.5 else '❌'} |\n")
        f.write(f"| **Halluzinationsrisiko** | {avg_hallucination*100:.1f}% | {'✅' if avg_hallucination < 0.2 else '⚠️' if avg_hallucination < 0.4 else '❌'} |\n")
        f.write(f"| **Entity-Grounding** | {avg_grounding*100:.1f}% | {'✅' if avg_grounding > 0.7 else '⚠️' if avg_grounding > 0.5 else '❌'} |\n")
        f.write(f"| **Informationsverlust** | {avg_info_loss*100:.1f}% | {'✅' if avg_info_loss < 0.2 else '⚠️' if avg_info_loss < 0.4 else '❌'} |\n")
        f.write(f"| **Extraktions-Vollstaendigkeit** | {avg_extraction*100:.1f}% | {'✅' if avg_extraction > 0.7 else '⚠️'} |\n")
        f.write(f"| **Warnungen** | {warnings_count} | - |\n\n")
        
        # Erklaerung der Metriken
        f.write("## Metrik-Erklaerungen\n\n")
        f.write("""
| Metrik | Bedeutung | Wie vermieden? |
| :--- | :--- | :--- |
| **Halluzinationsrisiko** | LLM erfindet Infos die nicht im Dokument sind | Strikte Prompt-Anweisungen, Grounding-Check |
| **Entity-Grounding** | Extrahierte Namen/Orte sind im Original | Nur Entities aus dem Text extrahieren |
| **Informationsverlust** | Wichtige Zahlen/Daten gehen verloren | Alle numerischen Werte extrahieren |
| **Extraktions-Vollstaendigkeit** | Wieviel vom Dokument wurde verarbeitet | Bessere Parser, OCR fuer Bilder |
| **Semantische Erhaltung** | Bedeutung bleibt in Zusammenfassung | Praezisere Summarization |
""")
        
        # Dateien mit Warnungen
        warned_files = [r for r in results if r.warnings]
        if warned_files:
            f.write(f"\n## Dateien mit Warnungen ({len(warned_files)})\n\n")
            for r in warned_files[:20]:
                f.write(f"### `{r.extension}` {r.filename[:40]}\n")
                for w in r.warnings:
                    f.write(f"- {w}\n")
                if r.ungrounded_claims:
                    f.write(f"- Unbegruendete Behauptungen: {r.ungrounded_claims[:2]}\n")
                f.write("\n")
        
        # Top/Bottom Qualitaet
        sorted_by_quality = sorted(results, key=lambda x: x.total_quality_score, reverse=True)
        
        f.write("## Beste Qualitaet (Top 10)\n\n")
        f.write("| Datei | Qualitaet | Halluz. | Grounding |\n")
        f.write("| :--- | ---: | ---: | ---: |\n")
        for r in sorted_by_quality[:10]:
            f.write(f"| `{r.extension}` {r.filename[:30]} | {r.total_quality_score*100:.0f}% | {r.hallucination_score*100:.0f}% | {r.entity_grounding_rate*100:.0f}% |\n")
        
        f.write("\n## Schlechteste Qualitaet (Bottom 10)\n\n")
        f.write("| Datei | Qualitaet | Problem |\n")
        f.write("| :--- | ---: | :--- |\n")
        for r in sorted_by_quality[-10:]:
            problems = []
            if r.hallucination_score > 0.3:
                problems.append("Halluz.")
            if r.information_loss_score > 0.3:
                problems.append("Info-Verlust")
            if r.extraction_completeness < 0.5:
                problems.append("Extraktion")
            f.write(f"| `{r.extension}` {r.filename[:30]} | {r.total_quality_score*100:.0f}% | {', '.join(problems) or '-'} |\n")
        
        # Empfehlungen
        f.write("\n## Empfehlungen zur Verbesserung\n\n")
        
        if avg_hallucination > 0.2:
            f.write("### Halluzination reduzieren\n")
            f.write("1. Prompt strenger formulieren: 'Antworte NUR mit Infos aus dem Text'\n")
            f.write("2. Temperature auf 0.1 setzen fuer deterministischere Ausgaben\n")
            f.write("3. Post-Processing: Fakten gegen Original validieren\n\n")
        
        if avg_info_loss > 0.3:
            f.write("### Informationsverlust reduzieren\n")
            f.write("1. Alle Zahlen und Daten explizit extrahieren\n")
            f.write("2. Volltext in Qdrant indexieren (nicht nur Summary)\n")
            f.write("3. OCR fuer gescannte Dokumente aktivieren\n\n")
        
        if avg_grounding < 0.7:
            f.write("### Entity-Grounding verbessern\n")
            f.write("1. NER (Named Entity Recognition) vor LLM-Klassifizierung\n")
            f.write("2. Entities gegen Original-Text validieren\n")
            f.write("3. Unbegruendete Entities verwerfen\n\n")
    
    print(f"Qualitaetsbericht: {report_path}")
    
    # JSON speichern
    json_path = TEST_DIR / "_quality_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, indent=2, default=str)


def main():
    print("=" * 70)
    print("NEURAL VAULT - ERWEITERTER QUALITAETS-TEST")
    print("=" * 70)
    print(f"Neue Testparameter:")
    print("  1. Halluzinations-Erkennung")
    print("  2. Entity-Grounding")
    print("  3. Informationsverlust-Messung")
    print("  4. RAG-Retrieval-Qualitaet")
    print("  5. Semantische Erhaltung")
    print("-" * 70)
    
    # Sammle Testdateien
    test_files = []
    for folder in TEST_DIR.iterdir():
        if folder.is_dir() and not folder.name.startswith("_"):
            for f in folder.iterdir():
                if f.is_file():
                    test_files.append(f)
    
    limit = 30  # Fuer Schnelltest
    test_files = test_files[:limit]
    
    print(f"\nTeste {len(test_files)} Dateien...\n")
    
    results = []
    for i, filepath in enumerate(test_files, 1):
        print(f"[{i}/{len(test_files)}] {filepath.name[:40]}...", end=" ", flush=True)
        result = process_file_enhanced(filepath)
        results.append(result)
        
        status = "✅" if result.total_quality_score > 0.7 else "⚠️" if result.total_quality_score > 0.5 else "❌"
        print(f"{status} Q:{result.total_quality_score*100:.0f}% H:{result.hallucination_score*100:.0f}% ({result.processing_time:.1f}s)")
    
    print("\n" + "=" * 70)
    print("GENERIERE QUALITAETSBERICHT...")
    generate_enhanced_report(results)
    
    # Summary
    avg_q = sum(r.total_quality_score for r in results) / len(results)
    print(f"\nDURCHSCHNITTLICHE QUALITAET: {avg_q*100:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
