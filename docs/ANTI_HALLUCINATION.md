# Anti-Halluzinations-Framework

> Neural Vault - Prompt Engineering Best Practices (Stand: 27.12.2025)

---

## Implementierte Strategien

Basierend auf aktueller Forschung (Dezember 2025) wurden folgende Anti-Halluzinations-Strategien implementiert:

### 1. Zentrale Prompt-Registry

**Datei:** `F:/conductor/scripts/prompt_system.py`

```python
from prompt_system import get_safe_ollama_client

client = get_safe_ollama_client()
result = client.classify_file(
    filename="Rechnung_2024.pdf",
    text_content="...",
    verify=True  # Chain-of-Verification aktivieren
)
```

**Vorteile:**
- Alle Scripts nutzen dieselben optimierten Prompts
- Bei LLM-Updates (Qwen3 → Qwen4) bleiben Prompts erhalten
- Versionierung und Audit-Trail

---

### 2. Anti-Halluzinations-Regeln

Jeder Prompt enthält diese expliziten Anweisungen:

```
WICHTIGE REGELN ZUR VERMEIDUNG VON HALLUZINATIONEN:

1. GROUNDING: Beziehe dich NUR auf Informationen die EXPLIZIT im Text stehen.
2. ABSTENTION: Wenn Information nicht vorhanden ist, antworte "Nicht im Dokument".
3. KEINE ANNAHMEN: Erfinde KEINE Daten, Zahlen oder Fakten.
4. ZITATION: Markiere jeden Fakt mit [QUELLE: im Text] oder [QUELLE: Dateiname].
5. UNSICHERHEIT: Bei Unsicherheit, gib confidence < 0.5 an.
6. BINAERDATEIEN: Bei Dateien ohne Text, extrahiere NUR was im Dateinamen steht.
```

---

### 3. Temperature-Kontrolle

| Aufgabe | Temperature | Begründung |
| :--- | :--- | :--- |
| **Klassifizierung** | 0.05 - 0.1 | Minimal: Deterministisch |
| **Entity-Extraktion** | 0.1 | Sehr niedrig: Faktenbasiert |
| **Zusammenfassung** | 0.3 | Niedrig: Etwas Variation erlaubt |
| **Kreative Aufgaben** | 0.7+ | Nicht für Indexierung! |

---

### 4. Chain-of-Verification (CoVe)

Selbst-Überprüfung vom LLM:

```
1. LLM generiert Antwort
2. LLM prüft eigene Behauptungen gegen Original
3. Status pro Behauptung:
   - grounded: Im Text gefunden ✅
   - inferred: Abgeleitet ⚠️
   - hallucinated: Erfunden ❌
```

---

### 5. Entity-Grounding

Jede extrahierte Entity muss im Original vorkommen:

```json
{
    "entities": {
        "found_in_text": ["Amazon", "2024-12-15"],
        "found_in_filename": ["Rechnung"]
    }
}
```

Unbegruendete Entities werden als Halluzination markiert.

---

### 6. Abstention Instructions

Das LLM darf "Ich weiß nicht" sagen:

```
Wenn Information nicht vorhanden ist:
- "Nicht im Dokument"
- "Unklar"
- confidence: 0.3
```

---

## Messung der Qualität

### Test-Script

```bash
python F:\conductor\scripts\run_quality_test.py
```

### Gemessene Metriken

| Metrik | Beschreibung | Zielwert |
| :--- | :--- | :--- |
| **Halluzinationsrisiko** | % erfundene Fakten | < 20% |
| **Entity-Grounding** | % Entities im Original | > 80% |
| **Informationsverlust** | % verlorene Zahlen/Daten | < 20% |
| **Gesamt-Qualität** | Gewichteter Score | > 70% |

---

## Versionshistorie

| Version | Datum | Änderungen |
| :--- | :--- | :--- |
| 2.0.0 | 2025-12-27 | Anti-Halluzinations-Framework |
| 1.0.0 | 2025-12-26 | Initiale Prompts |

---

## Referenzen (Dezember 2025)

1. **machinelearningmastery.com**: Prompt Engineering for Hallucination Prevention
2. **medium.com**: Reducing LLM Hallucinations 2025
3. **ollama.com**: Structured Outputs with Qwen3
4. **forbes.com**: RAG and Grounding Techniques
5. **prompthub.us**: Chain-of-Verification Patterns

---

*Letzte Aktualisierung: 27.12.2025 01:10*
