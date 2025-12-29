# Glossar: Neural Vault

> **Erklärung aller projektspezifischen Begriffe und Metaphern.**

Dieses Dokument hilft neuen Teammitgliedern, die Sprache des Projekts zu verstehen.

---

## Architektur-Begriffe

| Begriff | Bedeutung |
| :--- | :--- |
| **Neural Vault** | Der Projektname. Ein "Tresor" für deine Daten, der sie mit "neuronalem" (KI-basiertem) Verständnis durchsuchbar macht. |
| **The Power Plant** | Metapher für die Hardware-Architektur. Das Ryzen AI Mini-PC ist das "Kraftwerk", das die Rechenleistung liefert. |
| **Shadow Ledger** | Die SQLite-Datenbank, die als "Schattenbuch" alle Datei-Metadaten (Hash, Pfad, Status) protokolliert. Unabhängig vom Dateisystem selbst. |
| **Guardian** | Metapher für die automatisierten Agenten (n8n Workflows, Cron-Jobs), die 24/7 Dateien überwachen und organisieren. |
| **Consigliere** | Metapher für das "Daily Briefing" Feature (Phase 2+). Wie ein Berater, der dir morgens die wichtigsten Infos zusammenfasst. |

---

## Technologie-Stack

| Begriff | Bedeutung |
| :--- | :--- |
| **n8n** | Open-Source Workflow-Automatisierungs-Tool. Das "Zentrale Nervensystem", das alle Aktionen orchestriert. |
| **Qdrant** | Vektordatenbank (in Rust). Speichert semantische Embeddings für die Suche ("Finde ähnliche Dokumente"). |
| **Meilisearch** | Volltextsuchmaschine (in Rust). Schneller als Elasticsearch, ideal für E-Mails und Dokumente. |
| **Ollama** | Lokaler LLM-Runner. Führt Modelle wie Llama3 oder Mistral auf deiner Hardware aus. |
| **Tika** | Apache-Projekt zur Dateityp-Erkennung und Textextraktion (1400+ Formate). |
| **Immich** | Open-Source Google-Photos-Alternative für lokales Foto/Video-Management mit KI-Features (Gesichtserkennung). |
| **Ratarmount** | Tool zum "virtuellen Mounten" von Archiven (.rar, .7z) ohne Entpacken. |
| **Czkawka** | Rust-basiertes Tool zur Duplikat-Erkennung (Audio, Video, Bilder). |
| **scandir_rs** | Rust-basierter Dateisystem-Scanner mit Python-Bindings. Schneller als `os.walk()`. |

---

## Workflow-Begriffe

| Begriff | Bedeutung |
| :--- | :--- |
| **Magic Inbox** | Der `_Inbox` Ordner in Nextcloud/F:/. Neue Dateien, die hier landen, werden automatisch analysiert und einsortiert. |
| **Smart Ingestion** | Der Prozess, bei dem eine neue Datei analysiert (OCR, CLIP, Whisper), klassifiziert (LLM), umbenannt und verschoben wird. |
| **Tier 1 / Tier 2 Parser** | Mehrstufiges Parsing: Tier 1 = schnelle Triage (Tika). Tier 2 = tiefes Parsing für komplexe Dokumente (Docling). |
| **Two-Zone Model** | Architekturkonzept: 🟢 Active Zone (`_Inbox`) = Auto-Sortierung. 🔵 Passive Zone (Rest) = Nur Indexierung. |
| **Quality Gates** | 6 automatische Prüfungen, die jede Datei passieren muss, bevor sie verschoben wird. |
| **Quarantine** | Ordnerstruktur (`_Quarantine/`) für problematische Dateien, die nicht verarbeitet werden konnten. |
| **Confidence Threshold** | KI-Schwellenwert (70%). Darunter wird User via Telegram gefragt. |
| **Shadow Ledger** | Die SQLite-Datenbank, die als "Schattenbuch" alle Datei-Metadaten (Hash, Pfad, Original-Name) protokolliert. |

---

## Daten-Begriffe

| Begriff | Bedeutung |
| :--- | :--- |
| **Hot Data** | Daten, auf die häufig zugegriffen wird (Indizes, Datenbanken). Liegt auf schneller NVMe SSD. |
| **Cold Data** | Daten, auf die selten zugegriffen wird (Originaldateien, Archive). Liegt auf der 18TB HDD. |
| **Exact Duplicate** | Dateien mit identischem SHA-256 Hash. Werden automatisch gelöscht. |
| **Visual Duplicate** | Bilder/Videos, die visuell ähnlich aussehen (Perceptual Hash). Werden nur getaggt, nicht automatisch gelöscht. |
| **Semantic Duplicate** | Dokumente mit ähnlichem Inhalt (Vektor-Ähnlichkeit > 95%). Werden als "Related" verlinkt. |

---

## Projekt-Management

| Begriff | Bedeutung |
| :--- | :--- |
| **Conductor** | Der Codename des Projekts (historisch). Bezieht sich auf den "Dirigenten", der alle Komponenten orchestriert. |
| **Track** | Eine Projektphase oder ein Arbeitspaket (z.B. "TRACK-005: Neural Vault"). |
| **ADR** | Architecture Decision Record. Dokumentiert, *warum* eine technische Entscheidung getroffen wurde. Siehe `docs/ADR/`. |

---

*Letzte Aktualisierung: 2025-12-26*
