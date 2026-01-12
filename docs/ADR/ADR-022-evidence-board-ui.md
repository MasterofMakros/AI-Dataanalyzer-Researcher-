# ADR-022: Search UI - Ergebnisliste vs. Evidence Board

## Status
**Proposed** - A/B-Test erforderlich (ABT-N03)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Evidence Board mit PDF-Ausschnitten, Timestamps, Bounding Boxes"
- **Gemini 3 Pro:** "Neural Deck - Split Screen mit Reasoning Stream + Evidence Board"

---

## Kontext und Problemstellung

Aktuelle UI (`search_ui.py` mit Gradio):
- Einfache Textsuche
- Ergebnisse als Liste mit Dateinamen
- Keine Vorschau der relevanten Stellen

**Problem:**
- User muss jedes Dokument öffnen um Relevanz zu prüfen
- Keine Validierung der KI-Antwort
- Zeitaufwändig bei vielen Treffern

**Verbesserungspotential (Perplexity-Style):**
- Inline-Zitate mit Quellenangabe
- Vorschau der relevanten Passage
- Video-Timestamps, Bild-Ausschnitte

**Kritikalität:** NEW FEATURE - Wesentlich für Benutzerfreundlichkeit

---

## Entscheidungstreiber (Decision Drivers)

* **Validierbarkeit:** User muss KI-Antwort prüfen können
* **Effizienz:** Schnelles Finden ohne viele Klicks
* **Multi-Modal:** PDF, Video, Audio, Bilder unterstützen

---

## Betrachtete Optionen

1. **Option A (Baseline):** Einfache Ergebnisliste (Gradio)
2. **Option B (Kandidat):** Evidence Board mit Split Screen (React)
3. **Option C:** Terminal-basiertes Interface

---

## A/B-Test Spezifikation

### Test-ID: ABT-N03

```yaml
hypothese:
  these: "Evidence Board reduziert Zeit bis zur Antwort-Validierung um 50%"
  null_hypothese: "Einfache Liste ist ausreichend effizient"

baseline:
  implementierung: "Gradio search_ui.py"
  metriken:
    - name: "time_to_validate"
      beschreibung: "Zeit bis User Antwort-Quelle findet"
      messmethode: "User Study mit Stoppuhr"
      aktueller_wert: "~60-120 Sekunden"
    - name: "clicks_to_validate"
      beschreibung: "Anzahl Klicks bis zur Quelle"
      aktueller_wert: "~3-5 Klicks"
    - name: "user_satisfaction"
      beschreibung: "Subjektive Zufriedenheit (1-5)"
      aktueller_wert: "~3/5"

kandidat:
  implementierung: |
    // React Component: EvidenceBoard.tsx

    interface Source {
      id: string;
      file_path: string;
      file_type: "pdf" | "video" | "audio" | "image" | "text";
      evidence: {
        text: string;
        page?: number;
        bbox?: [number, number, number, number];  // PDF highlight
        timestamp_start?: number;  // Video/Audio
        timestamp_end?: number;
      };
      relevance_score: number;
    }

    interface AnswerWithSources {
      answer: string;
      citations: Array<{
        text: string;
        source_id: string;
        footnote_number: number;
      }>;
      sources: Source[];
    }

    const EvidenceBoard: React.FC<{data: AnswerWithSources}> = ({data}) => {
      return (
        <div className="flex h-screen">
          {/* Left: Answer with inline citations */}
          <div className="w-1/2 p-4 overflow-y-auto">
            <h2>Antwort</h2>
            <AnswerWithCitations
              answer={data.answer}
              citations={data.citations}
              onCitationClick={(id) => highlightSource(id)}
            />
          </div>

          {/* Right: Evidence sources */}
          <div className="w-1/2 p-4 overflow-y-auto bg-gray-50">
            <h2>Quellen</h2>
            {data.sources.map(source => (
              <SourceCard
                key={source.id}
                source={source}
                onView={() => openPreview(source)}
              />
            ))}
          </div>
        </div>
      );
    };

    const SourceCard: React.FC<{source: Source}> = ({source}) => {
      switch(source.file_type) {
        case "pdf":
          return <PDFPreview
            file={source.file_path}
            page={source.evidence.page}
            highlight={source.evidence.bbox}
          />;
        case "video":
          return <VideoClip
            file={source.file_path}
            start={source.evidence.timestamp_start}
            end={source.evidence.timestamp_end}
          />;
        case "audio":
          return <AudioSnippet
            file={source.file_path}
            start={source.evidence.timestamp_start}
            transcript={source.evidence.text}
          />;
        default:
          return <TextSnippet text={source.evidence.text} />;
      }
    };
  erwartete_verbesserung:
    - "time_to_validate: < 30 Sekunden"
    - "clicks_to_validate: 1 Klick"
    - "user_satisfaction: >= 4/5"

testbedingungen:
  methodik: "User Study mit 5 Testpersonen"
  aufgaben:
    - "Finde die Quelle für 'Rechnung vom Dezember'"
    - "Validiere ob die Antwort zur Frage 'Wann läuft mein Vertrag aus?' stimmt"
    - "Finde die Stelle im Video wo X erwähnt wird"
  messung:
    - "Zeit pro Aufgabe"
    - "Anzahl Klicks"
    - "Nachher-Befragung: Zufriedenheit"

erfolgskriterien:
  primaer: "time_to_validate < 30s (50% schneller)"
  sekundaer: "user_satisfaction >= 4/5"
  tertiaer: "Alle Medientypen funktionieren"
```

---

## API-Spezifikation für Evidence Board

```yaml
# POST /api/v1/search
request:
  query: "Wann läuft mein Handyvertrag aus?"
  include_evidence: true
  top_k: 10

response:
  answer: "Ihr Handyvertrag bei Telekom läuft am 15.03.2025 aus. [1]"
  citations:
    - text: "Vertragslaufzeit: 24 Monate, Beginn: 15.03.2023"
      source_id: "doc_abc123"
      footnote: 1
  sources:
    - id: "doc_abc123"
      file_path: "F:/_Archiv/Verträge/Telekom_2023.pdf"
      file_type: "pdf"
      evidence:
        text: "Vertragslaufzeit: 24 Monate, Beginn: 15.03.2023"
        page: 2
        bbox: [100, 450, 400, 480]
      download_url: "/api/files/doc_abc123/preview"
      relevance_score: 0.95
```

---

## Entscheidung

**PENDING** - User Study erforderlich

### Vorläufige Empfehlung
Basierend auf beiden KI-Analysen: **Option B (Evidence Board)**

### Begründung (vorläufig)
- Gemini: "Neural Deck mit Split Screen"
- Claude: "PDF-Ausschnitte, Timestamps, Bounding Boxes"
- Perplexity zeigt: Evidence-basierte UX ist der Standard

---

## Konsequenzen

### Wenn Option B gewinnt (Evidence Board)
**Positiv:**
- Schnelle Validierung
- Vertrauen in KI-Antworten
- Multi-Modal Support

**Negativ:**
- Höherer Entwicklungsaufwand (React statt Gradio)
- Backend-Anpassungen für Evidence-Extraktion
- Mehr Speicher für Vorschauen

### Wenn Option A bleibt (Einfache Liste)
**Positiv:**
- Schneller zu entwickeln
- Weniger Komplexität

**Negativ:**
- Schlechte User Experience
- Keine Validierungsmöglichkeit
- Nicht "State of the Art"

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision (VISION.md)? | [x] Ja - "Benutzerfreundliche Suche" |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Frontend-Stack dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Search UI: `scripts/search_ui.py`
- Mission Control: `mission_control_v2/`
