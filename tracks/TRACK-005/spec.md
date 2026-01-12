# TRACK-005: Context-Aware AI Sorting

## Problem
Nach der Datenmigration landen alle "unbekannten" Ordner und Dateien in `F:\_Inbox_Sorting\Rest_of_D\`. Diese müssen manuell sortiert werden – bei tausenden Dateien ein enormer Aufwand.

## Lösung: AI-Assisted Semantic Sorting

### Kernidee
Jeder Zielordner auf `F:` enthält eine `_context.md` Datei, die beschreibt, welche Inhalte dort hingehören. Ein LLM liest diese Kontexte und entscheidet automatisch, wohin jede unsortierte Datei gehört.

---

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    AI SORTING ENGINE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Context Loader                                           │
│     └─ Scannt alle _context.md auf F:\                       │
│     └─ Erstellt Vector-Embeddings (optional)                 │
│                                                              │
│  2. File Analyzer                                            │
│     └─ Liest Dateiname, Extension, Metadaten                 │
│     └─ Optional: Inhalt (Text, EXIF, ID3-Tags)               │
│                                                              │
│  3. LLM Matcher                                              │
│     └─ Prompt: "Welcher Kontext passt zu dieser Datei?"      │
│     └─ Output: Zielordner + Confidence Score                 │
│                                                              │
│  4. Action Queue                                             │
│     └─ High Confidence (>90%): Auto-Move                     │
│     └─ Medium (70-90%): Vorschlagen, User bestätigt          │
│     └─ Low (<70%): In _Inbox_Sorting\Manual\ belassen        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Beispiel-Flow

**Input:** `_Inbox_Sorting\Rest_of_D\Rechnung_Telekom_2024.pdf`

**Step 1 - Context Scan:**
```
F:\10 Datenpool Finanzen\_context.md:
  "Enthält Rechnungen, Kontoauszüge, Steuerdokumente..."

F:\07 Datenpool Persönliche Angelegenheiten\_context.md:
  "Enthält Verträge, Versicherungen, persönliche Dokumente..."
```

**Step 2 - LLM Prompt:**
```
Datei: "Rechnung_Telekom_2024.pdf"
Typ: PDF
Größe: 245 KB

Verfügbare Kontexte:
1. "Finanzen: Rechnungen, Kontoauszüge..."
2. "Persönliches: Verträge, Versicherungen..."
3. "Mediathek: Videos, Bilder, Audio..."

Frage: Welcher Kontext passt am besten? Antworte mit Nummer und Confidence (0-100).
```

**Step 3 - LLM Response:**
```
1 (Confidence: 95)
Begründung: "Rechnung" + "Telekom" deutet klar auf Finanzen hin.
```

**Step 4 - Action:**
→ Auto-Move zu `F:\10 Datenpool Finanzen\Rechnungen\Telekom\`

---

## Technische Anforderungen

| Komponente | Option A (Lokal) | Option B (API) |
|------------|------------------|----------------|
| LLM | Ollama (Phi-3, Qwen) | OpenAI GPT-4o-mini |
| Embedding | nomic-embed-text | text-embedding-3-small |
| Runtime | Laptop GPU (RTX) | Cloud |
| Speed | ~1-2 Dateien/Sek | ~5-10 Dateien/Sek |
| Kosten | Strom | ~$0.001/Datei |

---

## Implementierungsplan

### Phase 1: Context Indexer
- [ ] Skript zum Scannen aller `_context.md` auf F:\
- [ ] JSON-Export: `{Ordner: Kontext-Text}`

### Phase 2: File Metadata Extractor
- [ ] Dateiname, Extension, Größe, Erstelldatum
- [ ] Optional: PDF-Text, EXIF, ID3-Tags

### Phase 3: LLM Integration
- [ ] Prompt-Template für Klassifizierung
- [ ] Batch-Processing (10 Dateien pro Request)
- [ ] Confidence-Threshold Logik

### Phase 4: Action Engine
- [ ] Auto-Move für High Confidence
- [ ] CLI/Dashboard für Medium Confidence Review
- [ ] Logging aller Aktionen

### Phase 5: Continuous Learning (Future)
- [ ] User-Korrekturen speichern
- [ ] Fine-tuning des Matching-Prompts

---

## Abhängigkeiten
- TRACK-003: RAG Infrastructure (Vector Store, LLM Backend)
- Migration v5 abgeschlossen
- `_context.md` in allen Zielordnern vorhanden

---

## Risiken & Mitigations

| Risiko | Mitigation |
|--------|------------|
| LLM-Halluzination | Confidence-Threshold + Human Review |
| Falsche Zuordnung | Undo-Log für Rollback |
| API-Kosten | Batch-Processing, lokales LLM bevorzugen |
| Duplicate Files | Hash-Check vor Move |

---

## Status
**[ ] Nicht gestartet** - Wartet auf Migration-Abschluss
