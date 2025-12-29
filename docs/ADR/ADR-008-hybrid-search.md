# ADR-008: Hybrid-Suche (Volltext + Semantik)

## Status
**Akzeptiert** (2025-12-26)

## Kontext und Problemstellung

Für maximale Auffindbarkeit brauchen wir verschiedene Sucharten:

1. **Exakte Suche:** "Finde alle Dokumente mit 'Bauhaus'"
2. **Semantische Suche:** "Finde Rechnungen für Gartenzubehör" (auch wenn "Gartenzubehör" nicht wörtlich vorkommt)
3. **Zeitbasierte Suche:** "Was wurde bei Minute 3:00 im Video gesagt?"

Keine einzelne Technologie kann alle drei optimal.

---

## Entscheidung: Drei-Stufen-Hybrid-Suche

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SUCHANFRAGE                                       │
│                 "Bauhaus Rechnung Garten"                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│  STUFE 1:           │ │  STUFE 2:           │ │  STUFE 3:           │
│  VOLLTEXT-SUCHE     │ │  SEMANTISCHE SUCHE  │ │  METADATEN-FILTER   │
│  (Meilisearch)      │ │  (Qdrant)           │ │  (SQLite)           │
├─────────────────────┤ ├─────────────────────┤ ├─────────────────────┤
│ • Exakte Keywords   │ │ • Bedeutungsähnlich │ │ • Kategorie         │
│ • Typo-Toleranz     │ │ • Kontextverständnis│ │ • Datum             │
│ • Prefix-Match      │ │ • Synonyme          │ │ • Betrag            │
│ • Ranking           │ │ • "Wie X"           │ │ • Vendor            │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │  FUSION & RE-RANKING          │
                    │  (Reciprocal Rank Fusion)     │
                    │                               │
                    │  Kombiniert Scores aus allen  │
                    │  drei Quellen                 │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  TOP 10 ERGEBNISSE            │
                    │  mit Highlighting & Snippets  │
                    └───────────────────────────────┘
```

---

## Die drei Such-Engines im Detail

### 1. Meilisearch: Volltext-Durchsuchung (EXAKT)

**Was wird durchsucht?**
| Feld | Durchsuchbar | Beispiel |
| :--- | :--- | :--- |
| `extracted_text` | ✅ Vollständig | Der komplette OCR-Text, alle Seiten |
| `meta_description` | ✅ | "Eine Bauhaus-Rechnung..." |
| `original_filename` | ✅ | "IMG_4523.jpg" |
| `current_filename` | ✅ | "2024-05-12_Rechnung_Bauhaus.jpg" |
| `transcript_timestamped[].text` | ✅ | Jedes Segment des Transkripts |
| `entities_flat` | ✅ | "Bauhaus 127.50 EUR Gartenschlauch" |

**Meilisearch Konfiguration:**
```json
{
  "searchableAttributes": [
    "extracted_text",
    "meta_description",
    "original_filename",
    "current_filename",
    "transcript_text",
    "entities_flat",
    "tags"
  ],
  "filterableAttributes": [
    "category",
    "subcategory",
    "content_type",
    "file_created_at"
  ],
  "typoTolerance": {
    "enabled": true,
    "minWordSizeForTypos": {
      "oneTypo": 4,
      "twoTypos": 8
    }
  }
}
```

**Suchanfragen-Beispiele:**
```
"Rechnung 2024-12345"     → Exakter Match auf Rechnungsnummer
"Baauhuas"                → Findet "Bauhaus" (Typo-Toleranz)
"Gartenschlauch*"         → Prefix-Match: Gartenschlauch, Gartenschläuche
"\"WSL2 nicht aktiviert\"" → Phrase-Match im Transkript
```

---

### 2. Qdrant: Semantische Suche (BEDEUTUNG)

**Was wird vektorisiert?**
| Feld | Embedding-Strategie |
| :--- | :--- |
| `extracted_text` | Chunking (500-1000 Tokens), jeder Chunk = 1 Vektor |
| `meta_description` | Eigener Vektor (für schnelle Übersichtssuche) |
| `transcript_timestamped` | Jedes Segment = 1 Vektor (für Zeitmarken-Suche) |

**Chunk-Strategie:**
```python
# Für ein 10-seitiges PDF:
chunks = [
    {"chunk_id": 1, "text": "Seite 1-2...", "page_start": 1, "page_end": 2},
    {"chunk_id": 2, "text": "Seite 2-4...", "page_start": 2, "page_end": 4},
    {"chunk_id": 3, "text": "Seite 4-6...", "page_start": 4, "page_end": 6},
    # ...
]

# Jeder Chunk wird separat vektorisiert
for chunk in chunks:
    embedding = llama_index.embed(chunk["text"])
    qdrant.upsert(id=chunk_id, vector=embedding, payload={
        "file_id": file_id,
        "page_start": chunk["page_start"],
        "page_end": chunk["page_end"],
        "text_preview": chunk["text"][:200]
    })
```

**Suchanfragen-Beispiele:**
```
"Gartenartikel kaufen"     → Findet "Gartenschlauch", "Blumenerde" (semantisch)
"Probleme mit Docker"      → Findet "WSL2 Fehler", "Container startet nicht"
"Ähnlich wie diese Datei"  → K-Nearest-Neighbors auf Embedding
```

---

### 3. SQLite: Metadaten-Filter (STRUKTURIERT)

**Was kann gefiltert werden?**
```sql
SELECT * FROM file_metadata
WHERE category = 'Finanzen'
  AND subcategory = 'Rechnung'
  AND json_extract(extracted_entities, '$.amount') > 100
  AND json_extract(extracted_entities, '$.vendor') = 'Bauhaus'
  AND file_created_at BETWEEN '2024-01-01' AND '2024-12-31';
```

**Filterbare Felder:**
| Feld | Typ | Beispiel-Query |
| :--- | :--- | :--- |
| `category` | String | `= 'Finanzen'` |
| `subcategory` | String | `= 'Rechnung'` |
| `content_type` | String | `LIKE 'video/%'` |
| `file_created_at` | Date | `>= '2024-01-01'` |
| `extracted_entities.amount` | Number | `> 100` |
| `extracted_entities.vendor` | String | `= 'Bauhaus'` |
| `duration_seconds` | Number | `> 600` (Videos > 10 Min) |
| `confidence` | Float | `>= 0.8` |

---

## Hybrid-Suche: Fusion der Ergebnisse

### Reciprocal Rank Fusion (RRF)

```python
def reciprocal_rank_fusion(results_lists: list[list], k: int = 60) -> list:
    """
    Kombiniert Rankings aus verschiedenen Quellen.
    
    Args:
        results_lists: [meilisearch_results, qdrant_results, sqlite_results]
        k: Fusion-Konstante (höher = weniger Gewicht auf Top-Ranks)
    
    Returns:
        Fusioniertes Ranking
    """
    scores = defaultdict(float)
    
    for results in results_lists:
        for rank, doc_id in enumerate(results, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    
    # Sortiere nach kombiniertem Score
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Beispiel:**
```
Query: "Bauhaus Rechnung Garten 2024"

Meilisearch-Ergebnisse (Volltext):
  1. file_A (score: 0.95) - "Bauhaus" exakt gefunden
  2. file_B (score: 0.82) - "Garten" gefunden
  3. file_C (score: 0.71)

Qdrant-Ergebnisse (Semantik):
  1. file_B (similarity: 0.89) - Semantisch ähnlich
  2. file_D (similarity: 0.85) - Auch Gartenartikel
  3. file_A (similarity: 0.78)

SQLite-Filter:
  - file_A: category="Rechnung", vendor="Bauhaus", year=2024 ✓
  - file_B: category="Rechnung", vendor="OBI", year=2024 ✓
  - file_C: category="Foto", year=2024 ✗ (excluded)

Nach RRF-Fusion:
  1. file_A (kombiniert) ← Beste Übereinstimmung
  2. file_B (kombiniert)
  3. file_D (nur Qdrant)
```

---

## Spezialfall: Suche IN Dateien mit Zeitmarken

### Video/Audio: "Wo wird X gesagt?"

```python
def search_in_transcript(query: str, file_id: str) -> list[dict]:
    """
    Durchsucht das Transkript einer spezifischen Datei.
    Gibt Zeitmarken zurück, wo der Begriff vorkommt.
    """
    # Hole alle Transkript-Segmente aus der DB
    segments = db.query("""
        SELECT json_each.value as segment
        FROM file_metadata, json_each(transcript_timestamped)
        WHERE id = ?
    """, [file_id])
    
    results = []
    for segment in segments:
        seg = json.loads(segment)
        if query.lower() in seg["text"].lower():
            results.append({
                "start_time": seg["start"],
                "end_time": seg["end"],
                "text": seg["text"],
                "speaker": seg.get("speaker"),
                "deep_link": f"file:///{file_path}?t={int(seg['start'])}"
            })
    
    return results

# Beispiel:
search_in_transcript("WSL2 Fehler", file_id="video_123")

# Ergebnis:
[
    {
        "start_time": 180.0,
        "end_time": 195.5,
        "text": "Ein häufiger Fehler ist, dass WSL2 nicht aktiviert ist.",
        "deep_link": "file:///F:/tutorials/docker.mp4?t=180"
    }
]
```

### PDF: "Auf welcher Seite steht X?"

```python
def search_in_document(query: str, file_id: str) -> list[dict]:
    """
    Durchsucht alle Chunks eines Dokuments.
    Gibt Seitenzahlen zurück, wo der Begriff vorkommt.
    """
    # Hole alle Chunks aus Qdrant mit Page-Info
    chunks = qdrant.scroll(
        collection="neural_vault",
        filter={"file_id": file_id}
    )
    
    results = []
    for chunk in chunks:
        if query.lower() in chunk.payload["text"].lower():
            results.append({
                "page_start": chunk.payload["page_start"],
                "page_end": chunk.payload["page_end"],
                "text_preview": chunk.payload["text"][:200],
                "highlight": highlight_query(chunk.payload["text"], query)
            })
    
    return results
```

---

## Such-API: Beispielanfragen

### 1. Einfache Suche
```json
POST /api/search
{
  "query": "Bauhaus Rechnung",
  "limit": 10
}

Response:
{
  "results": [
    {
      "file_id": "123",
      "filename": "2024-05-12_Rechnung_Bauhaus_127EUR.pdf",
      "score": 0.94,
      "meta_description": "Eine Bauhaus-Rechnung über 127€ für Gartenzubehör.",
      "highlight": "...Rechnung Nr. 2024-12345 | <mark>BAUHAUS</mark>...",
      "path": "/09 Finanzen/Eingangsrechnungen/2024/"
    }
  ]
}
```

### 2. Suche mit Filtern
```json
POST /api/search
{
  "query": "Gartenzubehör",
  "filters": {
    "category": "Finanzen",
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "amount_min": 50
  },
  "limit": 10
}
```

### 3. Suche innerhalb einer Datei (Zeitmarken)
```json
POST /api/search/in-file
{
  "file_id": "video_123",
  "query": "Docker Installation"
}

Response:
{
  "matches": [
    {
      "start_time": 125.5,
      "end_time": 140.2,
      "text": "Jetzt beginnen wir mit der Docker Installation.",
      "deep_link": "file:///F:/tutorials/docker.mp4?t=125"
    }
  ]
}
```

### 4. Semantische Ähnlichkeitssuche
```json
POST /api/search/similar
{
  "file_id": "123",
  "limit": 5
}

Response:
{
  "similar_files": [
    {"file_id": "456", "similarity": 0.92, "reason": "Auch Bauhaus-Rechnung"},
    {"file_id": "789", "similarity": 0.85, "reason": "Auch Gartenartikel"}
  ]
}
```

---

## Konsequenzen

### Positiv
- ✅ **Maximale Auffindbarkeit:** Exakt + Semantisch + Strukturiert
- ✅ **Suche IN Dateien:** Zeitmarken, Seitenzahlen
- ✅ **Typo-tolerant:** "Baauhuas" findet "Bauhaus"
- ✅ **Kontext-Verständnis:** "Gartenartikel" findet "Gartenschlauch"

### Negativ
- ⚠️ Drei Systeme zu warten (Meilisearch, Qdrant, SQLite)
- ⚠️ Indexierung dauert länger (3x Speicherung)
- ⚠️ Komplexere Query-Logik

---

## Verknüpfte Dokumente

- [FILE_PROCESSING.md](./FILE_PROCESSING.md) - Was wird extrahiert
- [ADR-001: Vector Database](./ADR/ADR-001-vector-database.md) - Warum Qdrant
- [tech-stack.md](../tech-stack.md) - Meilisearch Details
