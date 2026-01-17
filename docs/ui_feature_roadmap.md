# Perplexica UI Feature Roadmap (Ergänzungen & Nicht-Ziele)

## Ziel
Diese Roadmap leitet aus der bestehenden Dokumentation ab, **welche UI-Features ergänzt werden sollten**, welche **nicht** implementiert werden dürfen, und **wie der Ist-Stand** dazu passt. Alle Punkte sind auf vorhandene Docs/ADRs abgestützt.

---

## 1) Empfohlene UI-Erweiterungen (priorisiert)

### 🚨 P0: Critical Usability (Startup & Visibility)

#### 1. Setup-Wizard (Onboarding)
**Status:** COMPLETED (v3.37.0) · **Priorität:** Kritisch (P0)
**Warum:** Aktuell ist Perplexica ohne manuelle Config kaum nutzbar.
**Umsetzung:** 3-Schritt-Wizard (Connect Provider -> Auto-Detect Models -> Test Request).

#### 2. System Status Dashboard
**Status:** COMPLETED (v3.37.0) · **Priorität:** Kritisch (P0)
**Warum:** "200 OK" reicht nicht; Nutzer müssen wissen, ob Qdrant/Ollama läuft.
**Umsetzung:** Ampel-System für alle Microservices (UI, API, Neural Search, Vector DB).

#### 3. Request Execution Trace (Reasoning Steps)
**Status:** COMPLETED (v3.37.0) · **Priorität:** Hoch (P1) -> Upgrade zu P0
**Warum:** Nutzer vertrauen dem System nicht ("Halluziniert es gerade?").
**Umsetzung:** Sichtbare Schritte "Router -> Search -> Rerank -> Synthesis" mit Zeitstempel.

---

### 🎨 Visual & Functional Polish (P1/Standard)

#### 4. Evidence Board (React)
**Status:** PROPOSED (ADR-022) · **Priorität:** Hoch

**Warum:** Quellenvalidierung soll in <30s möglich sein, weniger Klicks, bessere Multi-Modal-Unterstützung (PDF, Audio, Video, Bilder). Das Evidence Board ist als Ziel-UX definiert und explizit als wesentliche Verbesserung beschrieben. 

**Umsetzungsskizze (aus ADR-022):** Split-Screen mit Antwort + Quellenkarten, inklusive Highlights/Timestamps/BBox. 

**Abhängigkeiten:** API-Response muss `sources` + `evidence` liefern (page/bbox/timestamps). 

**Nachweis:** ADR-022 beschreibt Design, A/B-Test und API-Schema.【F:docs/ADR/ADR-022-evidence-board-ui.md†L1-L173】

---

### 2. Prozess-Transparenz (Search Progress)
**Status:** Konzept (NEURAL_SEARCH_UI_CONCEPT) · **Priorität:** Hoch

**Warum:** Der Suchprozess soll transparent sein, um Vertrauen zu erhöhen (Analyse → Suche → Lesen → Synthese). 

**Umsetzung:** Progress-Komponente mit klaren Schritten/Status und optionalen Detailanzeigen (z. B. gefundene Dokumente). 

**Nachweis:** UI-Konzept mit Search-Progress Animationen.【F:docs/NEURAL_SEARCH_UI_CONCEPT.md†L9-L120】

---

### 3. Source Preview Cards (Multi-Modal)
**Status:** Konzept (NEURAL_SEARCH_UI_CONCEPT) · **Priorität:** Mittel

**Warum:** Schnellere Validierung der Quellen ohne Dokument-Download. 

**Umsetzung:** Karten für PDF/Audio/Video/Bild mit Ausschnitten, OCR-Highlights oder Timestamps. 

**Nachweis:** Detail-Layouts und Interaktionen im UI-Konzept.【F:docs/NEURAL_SEARCH_UI_CONCEPT.md†L123-L253】

---

### 4. Trust-but-Verify Panel
**Status:** Konzept · **Priorität:** Mittel

**Warum:** Erhöht Glaubwürdigkeit, indem Aussagen direkt mit Quellen verknüpft werden. 

**Umsetzung:** Markierter Text + „verifiziert durch X Quellen“ UI. 

**Nachweis:** UI-Konzept beschreibt die Verifikation als UX-Feature.【F:docs/NEURAL_SEARCH_UI_CONCEPT.md†L256-L330】

---

### 5. Filter-UI (Facettensuche)
**Status:** Pflichtbestandteil im UAT-Plan · **Priorität:** Hoch

**Warum:** Laut UAT Plan ist Filter-UI Teil des Scope (Dateityp, Datum, Ordner, Tags). 

**Umsetzung:** Facettenpanel + kombinierbare Filter, mit klaren UX-Tests. 

**Nachweis:** UAT Plan listet Filter-UI als kritische Schnittstelle.【F:docs/UAT_PLAN.md†L19-L37】

---

## 2) Features, die **nicht** implementiert werden sollen

### Knowledge-Graph-UI (Graph-Visualisierung)
**Status:** Abgelehnt / Deprecated

**Begründung:** Zu wenig Nutzwert, hoher UI-Overhead; im Anti-Roadmap explizit verboten. 

**Alternative:** Related Documents statt Graph-Visualisierung. 

**Nachweise:**
- Anti-Roadmap: Graph UI ist „Red Button“.【F:docs/ANTI-ROADMAP.md†L166-L176】
- Component Status: Graph-Visualisierung ist deprecated.【F:docs/COMPONENT_STATUS.md†L67-L83】
- ADR-013: Related Documents als bessere Alternative.【F:docs/ADR/ADR-013-knowledge-graph-usage.md†L16-L112】

---

## 3) Ist-Stand (kurz)

**Bereits umgesetzt:**
- Perplexica UI als aktives Frontend (v2.x).【F:docs/COMPONENT_STATUS.md†L94-L105】
- Chat, Suche, Citations & Widgets als Kern-UI-Flows dokumentiert.【F:ui/perplexica/docs/architecture/README.md†L1-L26】【F:ui/perplexica/docs/architecture/WORKING.md†L11-L69】
- Feature-Scope inkl. Uploads, Bild/Video-Suche, Discover, History in README genannt.【F:ui/perplexica/README.md†L11-L41】

**Noch fehlend (gemäß Roadmap):**
- Evidence Board (UI + API-Shape)
- Search-Progress / Prozess-Transparenz
- Source Preview Cards
- Trust-but-Verify Panel
- Filter-UI (Facettensuche)

---

## 4) Nächste Schritte (empfohlen)

1. **Evidence Board MVP** (React) + API-Response-Erweiterung für `sources/evidence`. 
2. **Progress-UI** an den Recherche-Status koppeln. 
3. **Source Preview Cards** für PDF/Text zuerst, danach Audio/Video/Bild. 
4. **Filter-UI** implementieren und mit UAT-Metriken testen. 
5. **Trust-but-Verify Panel** als optionaler UI-Abschnitt. 

---

## 5) Erfolgskriterien (aus UAT/ADR)
- Validation-Time < 30s (Evidence Board)【F:docs/ADR/ADR-022-evidence-board-ui.md†L58-L153】
- Klicks bis Quelle ≤ 1-2 (Evidence Board + Filter)【F:docs/ADR/ADR-022-evidence-board-ui.md†L58-L153】【F:docs/UAT_PLAN.md†L19-L37】
- Filter-UI kombinierbar (UAT-Checklist)【F:docs/UAT_PLAN.md†L19-L37】

