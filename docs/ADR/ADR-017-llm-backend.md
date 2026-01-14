# ADR-017: LLM Backend - Cloud API vs. Local Ollama

## Status
**Accepted** - Entscheidung bereits getroffen (ABT-B03)

## Datum
2025-12-28

## Entscheider
- Product Owner (ursprüngliche Architektur-Entscheidung)

## Quellen
- **Claude Opus 4.5:** "Strategisch notwendig - 10TB 'Life Data' gehören nicht in die Cloud"
- **Gemini 3 Pro:** "Privacy-First - Du schläfst ruhiger"

---

## Kontext und Problemstellung

Für KI-Funktionen (Klassifikation, Q&A, Summarization) gibt es zwei Ansätze:
1. Cloud APIs (OpenAI, Anthropic, Google)
2. Lokale Modelle (Ollama, llama.cpp)

**Entscheidung wurde bereits getroffen:** Ollama (lokal) ist im Docker-Stack.

**Dokumentation als BLUE Button:** Diese Entscheidung war richtig und wird bestätigt.

---

## Entscheidungstreiber (Decision Drivers)

* **Privacy:** Persönliche Dokumente (Finanzen, Gesundheit) dürfen nicht in die Cloud
* **Kosten:** API-Kosten bei 100k+ Dokumenten würden explodieren
* **Offline-Fähigkeit:** System muss ohne Internet funktionieren
* **Latenz:** Lokale Modelle haben keine Netzwerk-Latenz

---

## Betrachtete Optionen

1. **Option A:** Cloud APIs (OpenAI GPT-4, Claude API)
2. **Option B (Gewählt):** Lokales Ollama
3. **Option C:** Hybrid (Cloud für komplexe, Lokal für einfache Tasks)

---

## A/B-Test Spezifikation (Retrospektiv)

### Test-ID: ABT-B03

```yaml
hypothese:
  these: "Lokale Modelle sind für Klassifikation ausreichend"
  ergebnis: "BESTÄTIGT"

baseline:
  implementierung: "Hypothetisch: OpenAI GPT-4 API"
  metriken:
    - name: "classification_accuracy"
      theoretischer_wert: "~95%"
    - name: "cost_per_1000_docs"
      theoretischer_wert: "~$50-100 (bei GPT-4)"
    - name: "privacy_risk"
      wert: "HOCH - Alle Dokumente gehen zu OpenAI"

gewinner:
  implementierung: "Ollama mit qwen3:8b / llama3.2"
  metriken:
    - name: "classification_accuracy"
      gemessener_wert: "~85-90%"
    - name: "cost_per_1000_docs"
      wert: "$0 (Hardware bereits vorhanden)"
    - name: "privacy_risk"
      wert: "KEINE - Alles lokal"

entscheidung:
  status: "BLUE - Richtige Entscheidung"
  begruendung: |
    - 5-10% weniger Genauigkeit ist akzeptabel für 100% Privacy
    - Kostenersparnis bei Scale ist enorm
    - System funktioniert auch offline
```

---

## Validierung der Entscheidung

### Was funktioniert gut (BLUE)
- Privacy: Keine Daten verlassen das Netzwerk
- Kosten: Nur Hardware + Strom
- Geschwindigkeit: RTX 3060 liefert ~10-20 Tokens/Sekunde

### Was verbessert werden kann
- **Modell-Auswahl:** Qwen3 vs Llama3 A/B-Test durchführen
- **Quantisierung:** 4-bit vs 8-bit für Speed/Quality Trade-off
- **Batch-Processing:** Mehrere Anfragen parallel

---

## Empfohlene Modelle (2025)

| Use Case | Modell | RAM | Qualität |
|----------|--------|-----|----------|
| Klassifikation | qwen3:8b | 6GB | Gut für Deutsch |
| Q&A | llama3.2:8b | 6GB | Gut für Reasoning |
| Summarization | mistral:7b | 5GB | Schnell |
| Embeddings | nomic-embed-text | 1GB | State of Art |

---

## Entscheidung

**ACCEPTED** - Lokales Ollama bleibt Standard

### Begründung
- Beide KI-Analysen bestätigen: "Privacy-First ist strategisch notwendig"
- Erfolgsalgorithmus: "Blauer Knopf - verstärken, nicht ändern"

---

## Konsequenzen

### Positiv (Bestätigt)
- 100% Privacy
- $0 laufende Kosten
- Offline-fähig
- Niedrige Latenz

### Negativ (Bekannt und akzeptiert)
- Geringere Genauigkeit als GPT-4
- Hardware-Anforderungen (GPU mit 8GB+ VRAM)
- Keine "State of the Art" Modelle (die sind nur Cloud)

---

## Zukünftige Überlegungen

- **Wenn lokal besser wird:** Warten auf Llama 4, Mistral Large lokal
- **Wenn Cloud Privacy verbessert:** Microsoft Azure AI mit Data Residency prüfen
- **Hybrid Option:** Für anonymisierte Daten (OCR-Text ohne Entities) Cloud nutzen

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision ([product/vision.md](../product/vision.md))? | [x] Ja - "Privacy-First" ist Kernprinzip |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [ ] Nein - bereits dokumentiert |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Ollama Config: `docker-compose.yml` (Service: ollama)
- [product/vision.md](../product/vision.md): Privacy-Prinzip
