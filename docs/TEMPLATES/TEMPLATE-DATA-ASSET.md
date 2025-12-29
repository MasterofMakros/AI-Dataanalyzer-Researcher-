# TEMPLATE: Data Asset Registration

> **Für jede neue Datenquelle, die in Neural Vault integriert wird.**
> **Kopiere dieses Template nach `docs/data-assets/ASSET-XXX-titel.md`**

---

# ASSET-XXX: [Name der Datenquelle]

<!-- 
ANLEITUNG:
- Ersetze XXX mit der nächsten fortlaufenden Nummer.
- Jeder Ordner/Datenbestand auf "Laufwerk F:" bekommt ein eigenes Asset-Dokument.
- Beispiel: "ASSET-001: 12 Datenpool Mediathek"
-->

## Metadaten

| Attribut | Wert |
| :--- | :--- |
| **Asset-ID** | ASSET-XXX |
| **Erstellt** | YYYY-MM-DD |
| **Letztes Update** | YYYY-MM-DD |
| **Verantwortlicher Owner** | [Name / Rolle] |
| **Status** | [Aktiv / Archiviert / Geplant] |

---

## 📁 Quelle

| Attribut | Beschreibung |
| :--- | :--- |
| **Pfad** | `F:\[Pfad zum Ordner]` |
| **Ursprung** | [z.B. "Export aus Synology NAS", "Download von X", "Eigene Erstellung"] |
| **Typ** | [z.B. "Backup", "Mediathek", "Dokumente", "Projektdaten"] |

---

## 📊 Technische Details

### Format & Größe

| Attribut | Wert |
| :--- | :--- |
| **Primäre Formate** | [z.B. ".mkv, .mp4, .srt"] |
| **Anzahl Dateien** | [z.B. "~5.000"] |
| **Gesamtgröße** | [z.B. "1.2 TB"] |
| **Ordnertiefe (Max)** | [z.B. "7 Ebenen"] |

### Struktur

```
[Ordnername]/
├── [Unterordner 1]/    # Beschreibung
├── [Unterordner 2]/    # Beschreibung
└── ...
```

### Bekannte Probleme / Besonderheiten

<!-- Gibt es Eigenheiten bei diesen Daten? -->

- [ ] Enthält passwortgeschützte Archive (.rar, .7z)
- [ ] Enthält beschädigte / unlesbare Dateien
- [ ] Uneinheitliche Namenskonvention
- [ ] Duplikate vermutet
- [ ] [Weitere Besonderheiten]

---

## 🛡️ Datenschutz & Compliance (PII-Check)

<!-- WICHTIG: Personenbezogene Daten erfordern besondere Behandlung! -->

### Enthält personenbezogene Daten (PII)?

- [ ] **Ja** → Siehe Maßnahmen unten
- [ ] **Nein** → Keine besonderen Maßnahmen

### Art der PII (falls zutreffend)

| PII-Typ | Vorhanden? | Beispiel |
| :--- | :--- | :--- |
| Namen | [ ] Ja / [ ] Nein | [z.B. "In E-Mail-Signaturen"] |
| E-Mail-Adressen | [ ] Ja / [ ] Nein | |
| Telefonnummern | [ ] Ja / [ ] Nein | |
| Adressen | [ ] Ja / [ ] Nein | |
| Finanzinformationen | [ ] Ja / [ ] Nein | [z.B. "Kontoauszüge"] |
| Gesundheitsdaten | [ ] Ja / [ ] Nein | |
| Biometrische Daten | [ ] Ja / [ ] Nein | [z.B. "Fotos mit Gesichtern"] |

### Schutzmaßnahmen

<!-- Welche Maßnahmen werden ergriffen? -->

- [ ] Zugriff eingeschränkt auf Owner
- [ ] Verschlüsselung (at rest)
- [ ] Anonymisierung vor Indexierung
- [ ] Keine Cloud-Verarbeitung (lokal only)
- [ ] [Weitere Maßnahmen]

---

## 📅 Lebenszyklus

### Update-Frequenz

| Frage | Antwort |
| :--- | :--- |
| Wird regelmäßig aktualisiert? | [ ] Ja / [ ] Nein (statisch) |
| Update-Intervall | [z.B. "Täglich", "Monatlich", "Nie"] |
| Quelle der Updates | [z.B. "Automatischer Sync", "Manueller Import"] |

### Aufbewahrungsfrist

| Frage | Antwort |
| :--- | :--- |
| Aufbewahrungspflicht? | [ ] Ja (gesetzlich) / [ ] Nein |
| Aufbewahrungsdauer | [z.B. "10 Jahre (Steuer)", "Unbegrenzt", "Bis manuell gelöscht"] |
| Löschprozedur | [z.B. "Sicheres Löschen nach Frist"] |

---

## 🔄 Integration in Neural Vault

### Indexierungs-Status

| Frage | Antwort |
| :--- | :--- |
| Indexiert in Qdrant? | [ ] Ja / [ ] Nein / [ ] Geplant |
| Indexiert in Meilisearch? | [ ] Ja / [ ] Nein / [ ] Geplant |
| OCR-Verarbeitung nötig? | [ ] Ja / [ ] Nein |
| Whisper-Transkription nötig? | [ ] Ja / [ ] Nein |

### Verarbeitungs-Pipeline

<!-- Welche Schritte sind für die Integration nötig? -->

1. [ ] Duplikat-Check (SHA-256)
2. [ ] Format-Normalisierung
3. [ ] OCR / Transcription
4. [ ] Embedding-Generierung
5. [ ] Index-Upload

### Priorität

| Priorität | Begründung |
| :--- | :--- |
| [Hoch / Mittel / Niedrig] | [z.B. "Enthält Rechnungen, die durchsuchbar sein müssen"] |

---

## 📝 Changelog

| Datum | Änderung | Autor |
| :--- | :--- | :--- |
| YYYY-MM-DD | Initiale Registrierung | [Name] |
| YYYY-MM-DD | [Beschreibung der Änderung] | [Name] |

---

## 🔗 Verknüpfte Dokumente

- ADRs: [Falls Technologie-Entscheidung für dieses Asset]
- Runbooks: [Falls spezieller Ingest-Prozess]
- Andere Assets: [Falls Daten miteinander verknüpft sind]
