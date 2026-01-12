# ADR-003: Architektur-Diagramme (Mermaid)

## Status
**Akzeptiert** (2025-12-26)

## Kontext
Wir brauchen ein Tool, um Architektur-Diagramme als Code zu verwalten ("Docs-as-Code"). Das Tool soll einfach in Markdown integrierbar sein und ohne separate Server-Infrastruktur funktionieren.

## Entscheidung
Wir nutzen **Mermaid** als primäres Diagramm-Tool.

## Begründung
*   **Native Markdown-Integration:** GitHub, GitLab und VSCode rendern Mermaid-Diagramme direkt.
*   **Keine Installation:** Funktioniert im Browser/Editor ohne Java-Runtime oder Server.
*   **AI-Unterstützung:** VSCode Extension "Mermaid Chart" generiert Diagramme aus Prompts.
*   **Ausreichend für C4:** Kann Context- und Container-Level Diagramme abbilden.

### Quellen (Stand Dez 2025)
*   [mermaid.js.org](https://mermaid.js.org): Offizielle Dokumentation.
*   [medium.com](https://medium.com): "Mermaid with AI-powered diagramming".

## Konsequenzen
*   **Positiv:** Geringe Einstiegshürde. Diagramme leben direkt im `README.md`.
*   **Negativ:** Weniger Layout-Kontrolle als Structurizr. Für sehr komplexe C4-Modelle evtl. unzureichend.

## Alternativen (abgelehnt)
| Alternative | Grund für Ablehnung |
| :--- | :--- |
| **Structurizr** | Overkill für Einzelpersonen-Projekt. Erfordert DSL-Lernkurve und separates Hosting. |
| **PlantUML** | Benötigt Java-Runtime. Komplexere Syntax als Mermaid. |
| **Draw.io** | Kein "as-Code". Binäre Dateien, schlechte Diff-Fähigkeit in Git. |
