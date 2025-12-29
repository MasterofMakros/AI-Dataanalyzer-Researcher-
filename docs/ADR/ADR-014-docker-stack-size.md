# ADR-014: Docker Stack - 17 Container vs. 8 Core Container

## Status
**Proposed** - A/B-Test erforderlich (ABT-R06)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Nextcloud, Immich sind optional - Core Stack: 8 Container max"
- **Gemini 3 Pro:** "Nicht explizit adressiert, aber 'Service-based Architecture' erwähnt"

---

## Kontext und Problemstellung

Aktuelle `docker-compose.yml` enthält:
1. traefik
2. postgres
3. redis
4. n8n
5. qdrant
6. meilisearch
7. tika
8. ollama
9. whisper
10. ffmpeg-api
11. tesseract-ocr
12. parser-service
13. sevenzip
14. neural-worker
15. nextcloud
16. nextcloud-db
17. (potentiell weitere)

**Problem:**
- Hoher RAM-Bedarf (~16GB+ für alle)
- Lange Startup-Zeit
- Komplexität für Homelab

**Kritikalität:** RED BUTTON - Ressourcen-Overhead

---

## Entscheidungstreiber (Decision Drivers)

* **Ressourcen:** Homelab hat begrenzte Hardware (32GB RAM)
* **Komplexität:** Weniger Container = einfacher zu warten
* **Funktionalität:** Kernfeatures müssen erhalten bleiben

---

## Betrachtete Optionen

1. **Option A (Baseline):** Alle 17 Container
2. **Option B (Kandidat):** 8 Core Container + optionale Profile
3. **Option C:** Monolith (alles in einem Container)

---

## Container-Klassifikation

### Core (Immer erforderlich)
| Container | Funktion | RAM | Kritikalität |
|-----------|----------|-----|--------------|
| postgres | Metadaten-DB | 256MB | KRITISCH |
| redis | Cache/Queue | 128MB | KRITISCH |
| meilisearch | Fulltext-Suche | 512MB | KRITISCH |
| neural-worker | NER, Embedding | 4GB | KRITISCH |
| tika | Dokument-Parsing | 1GB | HOCH |
| n8n | Workflow Engine | 768MB | MITTEL |

**Core Total: ~6.7GB RAM**

### Optional (Profile-basiert)
| Container | Funktion | RAM | Wann benötigt |
|-----------|----------|-----|---------------|
| qdrant | Vector DB (Hot) | 1GB | Nur wenn LanceDB nicht reicht |
| ollama | Local LLM | 8GB | Nur für Q&A, nicht Klassifikation |
| whisper | Audio-Transkription | 4GB | Nur für Audio/Video |
| nextcloud + db | File Sync | 768MB | Nur für Remote-Zugriff |
| traefik | Reverse Proxy | 128MB | Nur für Multi-Service-Routing |

### Entfernbar (Redundant)
| Container | Grund |
|-----------|-------|
| tesseract-ocr | Docling im neural-worker ersetzt dies |
| ffmpeg-api | Kann on-demand via Subprocess |
| sevenzip | Kann on-demand via Subprocess |
| parser-service | In neural-worker integriert |

---

## A/B-Test Spezifikation

### Test-ID: ABT-R06

```yaml
hypothese:
  these: "8 Core Container bieten gleiche Funktionalität bei weniger Ressourcen"
  null_hypothese: "Alle Container sind für Kernfunktionen erforderlich"

baseline:
  implementierung: "docker-compose.yml mit allen Services"
  metriken:
    - name: "total_ram_usage"
      beschreibung: "RAM-Nutzung aller Container"
      messmethode: "docker stats --no-stream"
      aktueller_wert: "~12-16GB (geschätzt)"
    - name: "startup_time"
      beschreibung: "Zeit bis alle Container healthy"
      aktueller_wert: "~2-5 Minuten"
    - name: "feature_coverage"
      beschreibung: "Welche Features funktionieren?"
      aktueller_wert: "100%"

kandidat:
  implementierung: |
    # docker-compose.yml mit Profiles

    services:
      # Core (immer gestartet)
      postgres:
        profiles: ["core"]
      redis:
        profiles: ["core"]
      # ...

      # Optional
      ollama:
        profiles: ["llm"]
      whisper:
        profiles: ["media"]
      nextcloud:
        profiles: ["sync"]

    # Start-Befehle:
    # docker compose --profile core up -d        # Minimal
    # docker compose --profile core --profile llm up -d  # Mit LLM
  erwartete_verbesserung:
    - "total_ram_usage: < 8GB (Core only)"
    - "startup_time: < 1 Minute"
    - "feature_coverage: 90% (Kern-Features)"

testbedingungen:
  hardware: "32GB RAM System"
  szenarien:
    - "Core-Only: Ingest 1000 Dateien"
    - "Core+LLM: Q&A Session mit 50 Fragen"
    - "Core+Media: 10 Audio-Dateien transkribieren"
    - "Full Stack: Alle Features parallel"

erfolgskriterien:
  primaer: "total_ram_usage Core < 8GB"
  sekundaer: "feature_coverage Core >= 85%"
  tertiaer: "startup_time Core < 60s"

testscript: |
  # tests/ab_test_docker_stack.sh

  #!/bin/bash

  # Baseline messen
  docker compose up -d
  sleep 120  # Warten bis healthy
  docker stats --no-stream --format "{{.MemUsage}}" > baseline_ram.txt
  docker compose down

  # Kandidat messen
  docker compose --profile core up -d
  sleep 60
  docker stats --no-stream --format "{{.MemUsage}}" > candidate_ram.txt
  docker compose down

  # Vergleich
  python compare_ram_usage.py baseline_ram.txt candidate_ram.txt
```

---

## Vorgeschlagene docker-compose.override.yml

```yaml
# docker-compose.override.yml für Profile-Support

version: '3.8'

# Definiere welche Services zu welchem Profil gehören
x-profiles:
  core: &core
    profiles:
      - core
      - default

  llm: &llm
    profiles:
      - llm
      - full

  media: &media
    profiles:
      - media
      - full

  sync: &sync
    profiles:
      - sync

services:
  postgres:
    <<: *core
  redis:
    <<: *core
  meilisearch:
    <<: *core
  neural-worker:
    <<: *core
  tika:
    <<: *core
  n8n:
    <<: *core

  qdrant:
    <<: *llm
  ollama:
    <<: *llm

  whisper:
    <<: *media
  ffmpeg-api:
    <<: *media

  nextcloud:
    <<: *sync
  nextcloud-db:
    <<: *sync
```

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf Claude-Analyse: **Option B (Profiles)**

### Begründung (vorläufig)
- Flexibilität: Nutzer wählt was er braucht
- Ressourcen: Core-Only für Entwicklung/Test
- Keine Funktionsverlust: Alle Container weiterhin verfügbar

---

## Konsequenzen

### Wenn Option B gewinnt (Profiles)
**Positiv:**
- Deutlich geringerer RAM-Bedarf im Alltag
- Schnellerer Start
- Einfacheres Debugging

**Negativ:**
- Komplexere Dokumentation
- Nutzer muss Profile verstehen

### Wenn Option A bleibt (Alle Container)
**Positiv:**
- Einfaches `docker compose up`
- Alle Features immer verfügbar

**Negativ:**
- Hoher RAM-Bedarf
- Lange Startzeit
- Viele ungenutzte Services laufen

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision (VISION.md)? | [x] Ja - Effizienz ist Kernziel |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Profile-Nutzung dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Docker Compose: `docker-compose.yml`
- Erfolgsalgorithmus: "17 Container = All-in gegen die Wand"
