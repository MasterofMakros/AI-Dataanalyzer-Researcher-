# TEMPLATE: Architecture Decision Record (ADR)

> **Basierend auf MADR 4.0.0 (2024)**
> **Kopiere dieses Template nach `docs/ADR/ADR-XXX-titel.md`**

---

# ADR-XXX: [Titel der Entscheidung]

<!-- 
ANLEITUNG:
- Ersetze XXX mit der nächsten fortlaufenden Nummer.
- Der Titel sollte imperativ sein, z.B. "Use Qdrant for Vector Search".
- Fokussiere auf EINE Entscheidung pro ADR.
-->

## Status

<!-- Wähle EINEN Status: -->
**[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]**

<!-- Falls Superseded, verlinke das neue ADR -->

## Lifecycle

<!-- Für Features die implementiert werden: -->
| Phase | Status | Datum |
|-------|--------|-------|
| Proposed | ✅ | YYYY-MM-DD |
| Experimental | ⏳ | - |
| Active | ⏳ | - |
| Deprecated | ⏳ | - |
| Removed | ⏳ | - |

## Versionierung

| Feld | Wert |
|------|------|
| **Version** | 1.0.0 |
| **Supersedes** | [ADR-XXX](./ADR-XXX.md) oder "Keine" |
| **Superseded by** | "Keine" oder [ADR-YYY](./ADR-YYY.md) |
| **A/B-Test ID** | ABT-XXX oder "Kein Test" |
| **Feature Flag** | `FEATURE_NAME` oder "Kein Flag" |

## Datum
YYYY-MM-DD

## Entscheider
<!-- Wer hat diese Entscheidung getroffen? -->
- [Name / Rolle]

---

## Kontext und Problemstellung

<!-- 
Beschreibe in 2-3 Sätzen:
- Was ist das Problem?
- Warum müssen wir jetzt eine Entscheidung treffen?
- Welche Constraints/Anforderungen gibt es?
-->

[Beschreibung des Kontexts und der Problemstellung]

---

## Entscheidungstreiber (Decision Drivers)

<!-- Welche Faktoren haben die Entscheidung beeinflusst? -->

* [Treiber 1, z.B. "Performance: Sub-second Latency erforderlich"]
* [Treiber 2, z.B. "Privacy: Keine Cloud-Dienste erlaubt"]
* [Treiber 3, z.B. "Kosten: Open Source bevorzugt"]

---

## Betrachtete Optionen

<!-- Liste alle ernsthaft erwogenen Alternativen auf -->

1. [Option 1]
2. [Option 2]
3. [Option 3]

---

## Entscheidung

**Wir wählen [Option X]: [Kurzbeschreibung]**

### Begründung
<!-- Warum diese Option und nicht die anderen? -->

[Begründung der Entscheidung]

### Quellen / Benchmarks
<!-- Verlinke Recherche-Ergebnisse -->

- [Quelle 1: URL oder Titel]
- [Quelle 2: URL oder Titel]

---

## Konsequenzen

### Positiv
<!-- Was wird durch diese Entscheidung besser? -->
- [Positiver Effekt 1]
- [Positiver Effekt 2]

### Negativ
<!-- Welche Trade-offs/Nachteile gibt es? -->
- [Negativer Effekt / Trade-off 1]
- [Negativer Effekt / Trade-off 2]

### Neutral
<!-- Auswirkungen, die weder positiv noch negativ sind -->
- [Neutrale Auswirkung, z.B. "Erfordert Anpassung des Deployment-Scripts"]

---

## Compliance-Check (PO-Absegnung)

<!-- Der Product Owner bestätigt, dass diese Entscheidung zur Vision passt -->

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision (VISION.md)? | [ ] Ja / [ ] Nein |
| Verstößt gegen Non-Goals? | [ ] Ja / [ ] Nein |
| Erfordert Runbook-Update? | [ ] Ja / [ ] Nein |

**PO-Signatur:** _________________ Datum: _________

---

## Alternativen (Detaillierte Bewertung)

<!-- Optional: Ausführlichere Analyse der Alternativen -->

### Option 1: [Name]
- **Pro:** [Vorteile]
- **Contra:** [Nachteile]
- **Fazit:** [Warum abgelehnt?]

### Option 2: [Name]
- **Pro:** [Vorteile]
- **Contra:** [Nachteile]
- **Fazit:** [Warum abgelehnt?]

---

## Verknüpfte Dokumente

<!-- Verlinke relevante andere ADRs, Runbooks, etc. -->

- Related ADRs: [ADR-XXX](./ADR-XXX-titel.md)
- Runbooks: [RUNBOOK-XXX](../runbooks/RUNBOOK-XXX-titel.md)
- Code: [Link zum relevanten Code]
