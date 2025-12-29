# ADR-015: Search Ranking - BM25 Only vs. BM25 + Cross-Encoder Reranking

## Status
**Proposed** - A/B-Test erforderlich (ABT-B01)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Cross-encoder Reranking (zerank-1) hinzufügen - State of the Art 2025"
- **Gemini 3 Pro:** "Hybrid Search ist das Herzstück - mach das so gut wie möglich"

---

## Kontext und Problemstellung

Aktuelle Implementierung:
- Meilisearch für Fulltext (BM25-ähnlich)
- Qdrant/LanceDB für Vektor-Suche
- Ergebnisse werden einfach zusammengeführt

**Verbesserungspotential:**
- Cross-Encoder Reranking kann Relevanz um 10-30% verbessern
- Besonders bei ambigen Queries ("Rechnung" → welche?)

**Kritikalität:** BLUE BUTTON - Kernfeature verstärken

---

## Entscheidungstreiber (Decision Drivers)

* **Relevanz:** Beste Treffer müssen oben stehen
* **Latenz:** Reranking darf Search nicht zu langsam machen
* **Skalierbarkeit:** Muss bei 100k+ Dokumenten funktionieren

---

## Betrachtete Optionen

1. **Option A (Baseline):** BM25 + Vektor-Fusion ohne Reranking
2. **Option B (Kandidat):** BM25 + Vektor → Top-50 → Cross-Encoder Rerank
3. **Option C:** Multi-Stage mit Coarse + Fine Reranking

---

## A/B-Test Spezifikation

### Test-ID: ABT-B01

```yaml
hypothese:
  these: "Cross-Encoder Reranking verbessert Precision@10 um mindestens 15%"
  null_hypothese: "Reranking bringt keinen signifikanten Vorteil"

baseline:
  implementierung: "Meilisearch + LanceDB Fusion"
  metriken:
    - name: "precision_at_10"
      beschreibung: "Relevante Dokumente in Top 10"
      messmethode: "Manuelles Relevanz-Rating"
      aktueller_wert: "~70% (geschätzt)"
    - name: "search_latency"
      beschreibung: "Zeit für Suchanfrage"
      aktueller_wert: "~200ms"
    - name: "mrr"
      beschreibung: "Mean Reciprocal Rank"
      aktueller_wert: "UNBEKANNT"

kandidat:
  implementierung: |
    # Zwei-Stufen-Suche

    def search_with_rerank(query: str, top_k: int = 10) -> list:
        # Stage 1: Schnelle Retrieval (BM25 + Vektor)
        candidates = retrieve_candidates(query, top_n=50)

        # Stage 2: Cross-Encoder Reranking
        reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        # Alternative 2025: "jinaai/jina-reranker-v2-base-multilingual"

        pairs = [(query, doc["text"]) for doc in candidates]
        scores = reranker.predict(pairs)

        # Sortieren nach Rerank-Score
        for i, doc in enumerate(candidates):
            doc["rerank_score"] = scores[i]

        return sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)[:top_k]
  erwartete_verbesserung:
    - "precision_at_10: >= 85%"
    - "search_latency: < 500ms (akzeptabler Trade-off)"
    - "mrr: >= 0.8"

testbedingungen:
  daten: "100 vordefinierte Suchanfragen mit Ground Truth"
  ground_truth_erstellung:
    - "50 einfache Queries ('Rechnung Bauhaus')"
    - "30 ambige Queries ('Vertrag 2024')"
    - "20 komplexe Queries ('Ausgaben für Software letztes Jahr')"
  bewertung: "3 menschliche Bewerter, Relevanz 0-3"

erfolgskriterien:
  primaer: "precision_at_10 Kandidat > Baseline + 10%"
  sekundaer: "search_latency < 1000ms"
  tertiaer: "Keine Regression bei einfachen Queries"

testscript: |
  # tests/ab_test_reranking.py

  from sentence_transformers import CrossEncoder
  import time

  def evaluate_search_quality(
      search_fn,
      queries: list,
      ground_truth: dict
  ) -> dict:
      """Evaluiert Suchqualität gegen Ground Truth."""
      results = {
          "precision_at_10": [],
          "latencies": [],
          "mrr": []
      }

      for query in queries:
          start = time.perf_counter()
          search_results = search_fn(query, top_k=10)
          latency = (time.perf_counter() - start) * 1000

          results["latencies"].append(latency)

          # Precision@10
          relevant_ids = ground_truth[query]
          found_ids = [r["id"] for r in search_results]
          precision = len(set(found_ids) & set(relevant_ids)) / 10
          results["precision_at_10"].append(precision)

          # MRR
          for rank, doc_id in enumerate(found_ids, 1):
              if doc_id in relevant_ids:
                  results["mrr"].append(1 / rank)
                  break
          else:
              results["mrr"].append(0)

      return {
          "avg_precision_at_10": sum(results["precision_at_10"]) / len(queries),
          "avg_latency_ms": sum(results["latencies"]) / len(queries),
          "mrr": sum(results["mrr"]) / len(queries)
      }
```

---

## Reranker-Modell Optionen (2025)

| Modell | Sprache | Latenz | Qualität |
|--------|---------|--------|----------|
| ms-marco-MiniLM-L-6-v2 | EN | ~20ms/doc | Gut |
| jina-reranker-v2-base-multilingual | DE/EN | ~30ms/doc | Sehr gut |
| zerank-1 (Zeta Alpha) | Multi | ~25ms/doc | State of Art |
| bge-reranker-v2-m3 | Multi | ~35ms/doc | Sehr gut |

**Empfehlung:** `jina-reranker-v2-base-multilingual` für deutsche Dokumente

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf beiden KI-Analysen: **Option B (Mit Reranking)**

### Begründung (vorläufig)
- Beide Analysen identifizieren Suche als "Herzstück"
- Cross-Encoder ist State of the Art für Relevanz
- 200-300ms Latenz-Overhead ist akzeptabel

---

## Konsequenzen

### Wenn Option B gewinnt (Mit Reranking)
**Positiv:**
- Deutlich bessere Relevanz
- Weniger "Scrollen" durch Ergebnisse
- Bessere User Experience

**Negativ:**
- Höhere Latenz (~300ms mehr)
- Zusätzliche Modell-Abhängigkeit
- GPU-RAM für Reranker (~500MB)

### Wenn Option A bleibt (Ohne Reranking)
**Positiv:**
- Schnellere Suche
- Einfachere Architektur

**Negativ:**
- Suboptimale Relevanz bei ambigen Queries
- Mehr manuelle Filterung nötig

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision (VISION.md)? | [x] Ja - "Finde alles in < 1 Minute" |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Reranker-Modell dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Hybrid Search ADR: [ADR-008-hybrid-search.md](./ADR-008-hybrid-search.md)
- Vector Service: `scripts/vector_service.py`
