# User Acceptance Test (UAT) Plan: Neural Vault

> **Version:** 1.0
> **Stand:** 2025-12-26
> **Status:** Entwurf
> **Basiert auf:** RAGAS, TruLens, Arize Phoenix (RAG Evaluation Standards 2025)

---

## 1. Einleitung

### Zweck dieses Dokuments
Dieser UAT-Plan validiert, ob das "Neural Vault" System (lokales 10TB Suchsystem) im Alltag nützlich ist. Wir testen aus Anwender-Perspektive, nicht aus Backend-Sicht.

### Scope
- **In Scope:** Chat-UI, Filter-UI, API-Latenz, OCR-Qualität, RAG-Genauigkeit
- **Out of Scope:** Hardware-Performance (wird separat getestet)

---

## 2. Interface & Interaction Konzept

### 2.1 Kritische Schnittstellen

| Schnittstelle | Beschreibung | Primärer Use Case | Kritische UX-Frage |
| :--- | :--- | :--- | :--- |
| **Chat-UI** | Natürlichsprachliche Fragen stellen | Deep Research, Adhoc-Suche | Versteht das System Kontextfragen? |
| **Filter-UI** | Facettensuche: Dateityp, Datum, Ordner, Tags | Gezielte Navigation | Sind Filter kombinierbar? |
| **API** | n8n Workflows, externe Tools | Batch-Verarbeitung | Latenz konstant <500ms P95? |

### 2.2 Empfohlene UI-Basis

| Tool | Beschreibung | Lokal? | Repository |
| :--- | :--- | :--- | :--- |
| **LobeChat** | Multi-LLM Chat UI, Ollama-Support | ✅ | github.com/lobehub/lobe-chat |
| **SurfSense** | Perplexity-Alternative, RAG-fähig | ✅ | github.com/MODSetter/SurfSense |

**Empfehlung:** LobeChat als Basis-UI adaptieren.

---

## 3. Torture Test Szenarien

### 3.1 Szenario A: Der Kontext-Killer (Version Confusion)

**Objektiv:** Testen, ob das System verschiedene Versionen desselben Dokuments unterscheiden kann.

| Attribut | Wert |
| :--- | :--- |
| **Setup** | 50 Versionen desselben Vertrags (`Vertrag_V1.docx` bis `Vertrag_V50.docx`) |
| **Test-Query** | "Was ist die Kündigungsfrist im aktuellsten Vertrag?" |
| **Erwartetes Ergebnis** | Antwort basiert NUR auf V50.docx |
| **Fail-Kriterium** | Antwort mischt Infos aus mehreren Versionen |
| **Messung** | Context Precision (RAGAS) ≥ 80% |

**Mitigation:**
- Metadaten-Filter: `ORDER BY modified_date DESC LIMIT 1`
- Re-Ranking nach Aktualität

---

### 3.2 Szenario B: Der OCR-Härtetest

**Objektiv:** Testen der OCR-Qualität bei problematischen Dokumenten.

| Attribut | Wert |
| :--- | :--- |
| **Setup** | 20 Problemdokumente: Faxe, Handschrift, schiefe Scans, Wasserzeichen |
| **Test-Query** | "Zeige alle Rechnungen mit Betrag 127,50€" |
| **Erwartetes Ergebnis** | Auch Faxkopie mit "127,50" wird gefunden |
| **Fail-Kriterium** | OCR erkennt Betrag falsch (z.B. "12750" oder "l27,5O") |
| **Messung** | OCR Accuracy Rate ≥ 90% auf manuell gelabelten Docs |

**Test-Dokumente erstellen:**
- [ ] 5x Fax-Simulation (Pixelig, Rauschen)
- [ ] 5x Handschrift-Scans (iPad, Whiteboard)
- [ ] 5x Schiefe Scans (10-15° Rotation)
- [ ] 5x Wasserzeichen-PDFs

---

### 3.3 Szenario C: Needle in the Haystack

**Objektiv:** Einen einzigen Satz in 1.1M Dateien finden.

| Attribut | Wert |
| :--- | :--- |
| **Setup** | Ein Dokument enthält: "Der Schlüssel liegt unter der Fußmatte" |
| **Test-Query** | "Wo liegt der Schlüssel?" |
| **Erwartetes Ergebnis** | Exaktes Dokument + Zitat gefunden |
| **Fail-Kriterium** | Dokument nicht in Top-10 Ergebnissen |
| **Messung** | Context Recall (RAGAS) = 100% für diesen Fall |

**Benchmark-Referenz:** NoLiMa (2025) zeigt <50% Accuracy bei 32K+ Tokens ohne Keyword-Match.

---

## 4. Key Performance Indicators (KPIs)

### 4.1 RAG-Qualitätsmetriken

| Metrik | Beschreibung | Zielwert | Tool |
| :--- | :--- | :--- | :--- |
| **Faithfulness** | % der Aussagen durch Kontext belegt | ≥ 90% | RAGAS |
| **Groundedness** | Antwort im Context verankert? | ≥ 95% | TruLens |
| **Context Precision** | Relevante Chunks / Alle Chunks | ≥ 80% | RAGAS |
| **Context Recall** | Alle relevanten Infos gefunden? | ≥ 85% | RAGAS |
| **Answer Relevancy** | Beantwortet Antwort die Frage? | ≥ 90% | RAGAS |

### 4.2 Performance-Metriken

| Metrik | Beschreibung | Zielwert | Messmethode |
| :--- | :--- | :--- | :--- |
| **Time to First Token** | Zeit bis erste Antwort | < 500ms | Arize Phoenix Trace |
| **E2E Latency (P95)** | 95. Perzentil Gesamtzeit | < 3s | Arize Phoenix |
| **Retrieval Latency** | Qdrant Query-Zeit | < 50ms | Qdrant Metrics |
| **OCR Time per Page** | Surya Processing | < 2.5s | Script Benchmark |

### 4.3 UX-Metriken

| Metrik | Beschreibung | Zielwert |
| :--- | :--- | :--- |
| **Clicks to Answer** | Interaktionen bis Lösung | ≤ 2 |
| **Zero Result Rate** | Anfragen ohne Ergebnis | < 5% |
| **Reformulation Rate** | Umformulierte Anfragen | < 20% |

---

## 5. Bug Hunter Checkliste

### Bekannte UX-Probleme bei RAG-Systemen

| # | Problem | Symptom | Test |
| :--- | :--- | :--- | :--- |
| 1 | Falsche Seitenzahlen | Zitat zeigt auf falsche Seite | Manueller Vergleich |
| 2 | Synonyme ignoriert | "Rechnung" ≠ "Invoice" | Query-Expansion-Test |
| 3 | Filter nicht kombinierbar | "2024" + ".pdf" = 0 Ergebnisse | Kombinationsmatrix |
| 4 | Alte Versionen bevorzugt | Ältere Docs vor neueren | Kontext-Killer-Test |
| 5 | Halluzinierte Fakten | Info nicht im Kontext | Faithfulness ≥ 90% |
| 6 | Abbruch bei langen Antworten | Nach 500 Tokens abgeschnitten | Max-Token-Test |
| 7 | Encoding-Probleme | "Müller" → "M?ller" | UTF-8 Validierung |
| 8 | Leere Chunks | OCR liefert leere Strings | Chunk-Validierung |
| 9 | Datum-Parsing-Fehler | "01.12.2024" als US-Format | Lokalisierung DE |
| 10 | Silent Failures | Indexierung scheitert still | Error-Logging prüfen |

---

## 6. Test-Durchführung

### 6.1 Voraussetzungen

```bash
# Evaluation-Frameworks installieren
pip install ragas arize-phoenix trulens

# Testdaten-Ordner erstellen
mkdir -p F:\conductor\test-data\{version-confusion,ocr-hardtest,needle}
```

### 6.2 Test-Phasen

| Phase | Fokus | Dauer | Ergebnis |
| :--- | :--- | :--- | :--- |
| **Phase 1: Unit Tests** | Einzelne Komponenten (OCR, Retrieval) | 1 Tag | Komponenten-Report |
| **Phase 2: Integration Tests** | Pipeline E2E | 2 Tage | Integration-Report |
| **Phase 3: UAT** | Reale User-Szenarien | 3 Tage | UAT-Report |
| **Phase 4: Stress Test** | 1000 parallele Anfragen | 1 Tag | Performance-Report |

### 6.3 Testdaten-Erstellung

**Kontext-Killer (50 Versionen):**
```python
for i in range(1, 51):
    create_contract(f"Vertrag_V{i}.docx", 
                    kuendigungsfrist=f"{i} Monate")
```

**OCR-Härtetest:**
- Nutze echte Scans aus `F:\99 Datenpool Archiv`
- Ergänze mit künstlich degradierten PDFs

**Needle:**
```python
create_unique_document("needle.txt", 
    content="Der Schlüssel liegt unter der Fußmatte.")
```

---

## 7. Erfolgskriterien

### Definition of Done (UAT bestanden)

- [ ] **Alle KPIs im Zielbereich** (siehe Tabelle 4.1-4.3)
- [ ] **Keine Showstopper-Bugs** (Bug Hunter Liste)
- [ ] **Torture Tests bestanden:**
  - [ ] Kontext-Killer: Context Precision ≥ 80%
  - [ ] OCR-Härtetest: Accuracy ≥ 90%
  - [ ] Needle: Recall = 100%
- [ ] **UX-Feedback positiv** (User kann Rechnung in <1 Min finden)

---

## 8. Verknüpfte Dokumente

- [VISION.md](../VISION.md) - Projektziele & Non-Goals
- [DOCUMENTATION_STANDARD.md](DOCUMENTATION_STANDARD.md) - Definition of Done
- [ADR-005-ocr-strategy.md](ADR/ADR-005-ocr-strategy.md) - OCR-Entscheidungen
- [test_invoice_search.py](../tests/test_invoice_search.py) - Automatisierte Tests

---

## 9. Changelog

| Datum | Änderung | Autor |
| :--- | :--- | :--- |
| 2025-12-26 | Initiale Version | Expertenteam |

---

*Dieses Dokument wird nach jeder Test-Runde aktualisiert.*
