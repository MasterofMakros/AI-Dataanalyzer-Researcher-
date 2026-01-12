# Ebook-Parser Benchmarks (MOBI/AZW/DjVu)

Diese Übersicht dokumentiert die per Web-Recherche identifizierten Parser, die als Referenz-Implementierungen für Text-Extraktion und Metadaten-Parsing gelten. Sie dient als Grundlage für die Implementierung des `ebook-parser` Services.

## MOBI/AZW/AZW3

**Empfohlener Parser:** KindleUnpack

**Begründung (Quelle):** KindleUnpack ist das De-facto-Tool zum Entpacken von MOBI/AZW/AZW3-Containern, da es die Kindle-Containerstruktur und die eingebetteten HTML/XHTML/OPF-Dateien explizit unterstützt.

**Quellen:**
- KindleUnpack Projektseite (Format-Support + Nutzung als Unpacker): <https://github.com/kevinhendricks/KindleUnpack>
- KindleUnpack README (Workflows + containerbasierte Extraktion): <https://github.com/kevinhendricks/KindleUnpack#readme>

**Metriken (aus Quellen ableitbar):**
- **Format-Abdeckung:** MOBI, AZW, AZW3 (als Kindle-Containerformate). Quelle: KindleUnpack README.
- **Extraktions-Granularität:** Text (HTML/XHTML), Metadaten (OPF). Quelle: KindleUnpack README.

## DjVu

**Empfohlener Parser:** DjVuLibre (`djvutxt`)

**Begründung (Quelle):** DjVuLibre ist die Referenz-Implementierung für DjVu und enthält `djvutxt` als offizielles Tool zur Text-Extraktion.

**Quellen:**
- DjVuLibre Projektbeschreibung + Tools: <https://djvu.sourceforge.net/>
- DjVuLibre Tools-Dokumentation (`djvutxt`): <https://djvu.sourceforge.net/doc/man/djvutxt.html>

**Metriken (aus Quellen ableitbar):**
- **Format-Abdeckung:** DjVu (offizielles Referenz-Toolset). Quelle: DjVuLibre Dokumentation.
- **Text-Extraktion:** `djvutxt` liefert plain text aus DjVu-Seiten. Quelle: djvutxt Manpage.

## Notizen zur Nutzung im Projekt

- **MOBI/AZW/AZW3**: Text wird aus entpackten HTML/XHTML-Dateien extrahiert, Metadaten aus OPF.
- **DjVu**: Text wird über `djvutxt` extrahiert, Seitenanzahl optional über `djvused`.
