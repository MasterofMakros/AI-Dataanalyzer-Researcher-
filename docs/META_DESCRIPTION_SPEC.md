# Spezifikation: Meta-Beschreibungen

> **Wie ausführlich muss eine Meta-Beschreibung sein?**

*Stand: 2025-12-26*

---

## 1. Die Rolle der Meta-Beschreibung

### Was sie ist:
Eine **menschenlesbare Zusammenfassung** (2-5 Sätze), die erklärt:
- **WAS** ist das für eine Datei?
- **WORUM** geht es inhaltlich?
- **WER/WAS** sind die wichtigsten Entitäten?

### Was sie NICHT ist:
- ❌ Die einzige durchsuchbare Information (Volltext wird AUCH durchsucht!)
- ❌ Eine verkürzte Version des Volltexts
- ❌ Eine Liste von Keywords

---

## 2. Warum die Qualität wichtig ist

```
┌───────────────────────────────────────────────────────────────────────┐
│                    SUCH-ARCHITEKTUR                                   │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ EBENE 1: VOLLTEXT (extracted_text)                              │ │
│  │ → Jedes einzelne Wort durchsuchbar                              │ │
│  │ → Kann NIEMALS "übersprungen" werden                            │ │
│  │ → Findet: "Rechnungsnummer 2024-12345"                          │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                              ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ EBENE 2: META-BESCHREIBUNG                                      │ │
│  │ → Zusammenfassung für SEMANTISCHE Suche                         │ │
│  │ → Verbessert Ranking bei vagen Anfragen                         │ │
│  │ → Findet: "Gartenartikel" auch wenn nicht wörtlich im Text     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                              ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ EBENE 3: ENTITIES & TAGS                                        │ │
│  │ → Strukturierte Daten für Filter                                │ │
│  │ → Findet: "Rechnungen > 100€ von Bauhaus"                      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

**Fazit:** Eine Datei wird NIEMALS "übersprungen", weil die Meta-Beschreibung zu kurz ist. Der Volltext wird immer durchsucht. Aber eine gute Meta-Beschreibung **verbessert das Ranking** bei vagen Anfragen.

---

## 3. Qualitätsstufen

### ❌ SCHLECHT (zu kurz, zu vage)

```json
{
  "meta_description": "Eine Rechnung."
}
```
**Problem:** Keine Entitäten, kein Kontext, keine Unterscheidung zu anderen Rechnungen.

### ⚠️ AKZEPTABEL (Minimum)

```json
{
  "meta_description": "Bauhaus-Rechnung über 127€ vom 12.05.2024."
}
```
**Enthält:** Vendor, Betrag, Datum. Aber: Was wurde gekauft?

### ✅ GUT (Standard)

```json
{
  "meta_description": "Eine Eingangsrechnung von Bauhaus über 127,50€ für Gartengeräte (Gartenschlauch, Schaufel). Rechnungsdatum: 12.05.2024, Fälligkeit: 26.05.2024."
}
```
**Enthält:** Vendor, Betrag, Kategorie, Gegenstände, Datum, Fälligkeit.

### 🌟 EXZELLENT (Optimal)

```json
{
  "meta_description": "Eingangsrechnung #2024-12345 von Bauhaus (Baumarkt) über 127,50 EUR für Gartengeräte. Gekaufte Artikel: Gartenschlauch 25m, Klappspaten. Rechnungsdatum 12.05.2024, Zahlung fällig bis 26.05.2024. Zahlungsart: Überweisung. Projekt: Gartenumgestaltung 2024."
}
```

---

## 4. Mindestanforderungen pro Dateityp

### 📄 Dokumente (PDF, DOCX)

| Pflichtfeld | Beispiel |
| :--- | :--- |
| **Dokumenttyp** | "Eingangsrechnung", "Vertrag", "Angebot" |
| **Hauptakteur** | "von Bauhaus", "mit Vermieter" |
| **Kerninhalt** | "über Gartengeräte", "für Mietwohnung" |
| **Datum** | "vom 12.05.2024" |
| **Betrag** (wenn vorhanden) | "über 127,50€" |

**Template:**
```
[Dokumenttyp] [Hauptakteur] über/für [Kerninhalt]. 
[Optional: Schlüsseldetails]. [Datum].
```

**Beispiele:**
- "Mietvertrag mit Immobilien Schmidt für die Wohnung Musterstr. 12. Kaltmiete 850€, Laufzeit unbefristet. Unterzeichnet am 01.03.2020."
- "Kontoauszug Sparkasse für Konto DE89... vom November 2024. Endsaldo: 3.456,78€. 47 Buchungen."

---

### 🖼️ Bilder

| Pflichtfeld | Beispiel |
| :--- | :--- |
| **Was ist zu sehen?** | "Ein Golden Retriever am Strand" |
| **Wo?** (wenn bekannt) | "in Barcelona" |
| **Wann?** | "am 15.08.2024" |
| **Wer?** (wenn Personen) | "mit Familie Müller" |
| **Anlass?** (wenn erkennbar) | "Sommerurlaub" |

**Template:**
```
[Was ist zu sehen] [wo] [wann]. [Optional: Kontext/Anlass].
```

**Beispiele:**
- "Strandfoto aus Barcelona bei Sonnenuntergang. Golden Retriever spielt im Wasser. Sommerurlaub August 2024."
- "Screenshot einer Fehlermeldung in Docker Desktop. WSL2-Fehler 'Cannot start container'. Aufgenommen am 15.01.2024 während Tutorial-Erstellung."

---

### 🎥 Videos

| Pflichtfeld | Beispiel |
| :--- | :--- |
| **Worum geht es?** | "Tutorial über Docker-Installation" |
| **Hauptthemen** | "Installation, Konfiguration, Troubleshooting" |
| **Dauer** | "30 Minuten" |
| **Zielgruppe** (wenn bekannt) | "für Einsteiger" |

**Template:**
```
[Thema] ([Dauer]). [Hauptthemen]. [Optional: Zielgruppe/Kontext].
```

**Beispiele:**
- "Docker-Tutorial für Windows (30 Min). Behandelt: Download, Installation, WSL2-Setup, häufige Fehler. Für Einsteiger geeignet."
- "Geburtstagsvideo von Oma Helga (5 Min). Aufgenommen am 75. Geburtstag in München. Anwesend: Familie, Freunde."

---

### 🎵 Audio (Voice Memos, Podcasts)

| Pflichtfeld | Beispiel |
| :--- | :--- |
| **Worum geht es?** | "Ideensammlung für Q4-Projekt" |
| **Erwähnte Personen** | "Sarah vom Vertrieb" |
| **Erwähnte Themen** | "Budget, Timeline, Marketing" |
| **Action Items** (wenn vorhanden) | "Budget klären, Meeting planen" |

**Template:**
```
[Art der Aufnahme] vom [Datum]: [Hauptthema]. 
Erwähnt: [Personen/Themen]. [Optional: Action Items].
```

**Beispiele:**
- "Voice Memo vom 15.08.2024: Ideen für Q4-Marketingkampagne. Erwähnt werden Sarah (Vertrieb), Budget-Freigabe Ende Oktober, Deadline 28.11. Action Items: Budget-Status klären."
- "Podcast-Episode 'Tech Weekly' #142 (45 Min). Themen: KI-Entwicklung 2024, OpenAI News, Interview mit Dr. Schmidt von der TU München."

---

### 📧 E-Mails

| Pflichtfeld | Beispiel |
| :--- | :--- |
| **Von/An** | "Von: supplier@bauhaus.de" |
| **Betreff** | "Angebot Gartengeräte" |
| **Kerninhalt** | "Angebot über 500€ für Gartengeräte" |
| **Anhänge** (wenn vorhanden) | "1 PDF-Anhang: Angebot.pdf" |
| **Handlungsbedarf?** | "Antwort bis 30.09. erforderlich" |

**Template:**
```
E-Mail von [Absender]: "[Betreff]". [Kerninhalt]. 
[Optional: Anhänge, Handlungsbedarf].
```

---

## 5. Längen-Empfehlungen

| Dateityp | Minimum | Optimal | Maximum |
| :--- | :--- | :--- | :--- |
| **Einfaches Dokument** | 50 Zeichen | 150 Zeichen | 300 Zeichen |
| **Komplexes Dokument** | 100 Zeichen | 250 Zeichen | 500 Zeichen |
| **Foto** | 30 Zeichen | 100 Zeichen | 200 Zeichen |
| **Video/Audio** | 80 Zeichen | 200 Zeichen | 400 Zeichen |
| **E-Mail** | 50 Zeichen | 150 Zeichen | 300 Zeichen |

---

## 6. Qualitätsprüfung (Quality Gate)

Im Quality Gate wird geprüft:

```python
def check_meta_description_quality(meta: str, content_type: str) -> tuple[bool, str]:
    """
    Prüft die Qualität der Meta-Beschreibung.
    Returns: (passed, reason)
    """
    
    # 1. Mindestlänge
    min_length = {
        "application/pdf": 50,
        "image/": 30,
        "video/": 80,
        "audio/": 50,
        "message/": 50
    }
    
    for mime_prefix, min_len in min_length.items():
        if content_type.startswith(mime_prefix):
            if len(meta) < min_len:
                return False, f"Zu kurz ({len(meta)}/{min_len} Zeichen)"
    
    # 2. Keine generischen Phrasen
    banned_phrases = [
        "Eine Datei",
        "Ein Dokument",
        "Eine Rechnung",  # Ohne weitere Details
        "Ein Foto",
        "Ein Video"
    ]
    if meta.strip() in banned_phrases:
        return False, "Zu generisch, keine Details"
    
    # 3. Enthält mindestens eine Entität
    # (wird über extracted_entities geprüft, nicht hier)
    
    return True, "OK"
```

---

## 7. Zusammenfassung

### Die goldene Regel:

> **Die Meta-Beschreibung muss genug Kontext liefern, dass ein Mensch ohne die Datei zu öffnen weiß, worum es geht.**

### Checkliste für gute Meta-Beschreibungen:

- [ ] **WAS?** - Art des Dokuments/Mediums
- [ ] **WER?** - Hauptakteure (Personen, Firmen)
- [ ] **WORUM?** - Kerninhalt/Thema
- [ ] **WANN?** - Datum (wenn relevant)
- [ ] **WIE VIEL?** - Beträge, Mengen (wenn relevant)
- [ ] **SO WHAT?** - Warum ist es wichtig? (Kontext)

### Keine Angst vor "Überspringen":

Der **Volltext wird IMMER durchsucht**. Die Meta-Beschreibung ist ein Bonus für:
1. Besseres Ranking bei vagen Anfragen
2. Schnellere Vorschau in Suchergebnissen
3. Semantische Suche ("Gartenartikel" findet "Gartenschlauch")

---

*Dieses Dokument definiert die Qualitätsstandards für Meta-Beschreibungen im Neural Vault.*
