# ADR-011: Dateinamen-Strategie - Auto-Rename vs. Metadata-Layer

## Status
**Proposed** - A/B-Test erforderlich (ABT-R03)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Umbenennung ist destruktiv - Original verloren"
- **Gemini 3 Pro:** "Nicht explizit adressiert"

---

## Kontext und Problemstellung

Aktuelle Implementierung in `quality_gates.py`:
- Generiert Smart Filename: `2024-12-26_Finanzen_Bauhaus_Gartenmaterial.pdf`
- Datei wird physisch umbenannt
- Original-Name nur in `shadow_ledger.db` gespeichert

**Problem:**
- Destruktive Operation (nicht rückgängig ohne DB)
- Externe Tools (Suche, Backup) verlieren Referenz
- Bei DB-Verlust: Original-Namen weg

**Kritikalität:** RED BUTTON - Potenzieller Datenverlust

---

## Entscheidungstreiber (Decision Drivers)

* **Reversibilität:** Änderungen müssen rückgängig machbar sein
* **Kompatibilität:** Externe Tools müssen weiter funktionieren
* **Suchbarkeit:** Smart Names verbessern Auffindbarkeit

---

## Betrachtete Optionen

1. **Option A (Baseline):** Physische Umbenennung
2. **Option B (Kandidat):** Metadata-Layer (virtueller Name)
3. **Option C:** Symlinks mit Smart Names

---

## A/B-Test Spezifikation

### Test-ID: ABT-R03

```yaml
hypothese:
  these: "Metadata-Layer bietet gleiche Suchbarkeit ohne Destruktivität"
  null_hypothese: "Physische Umbenennung ist für Suche notwendig"

baseline:
  implementierung: "smart_ingest.py mit physischem Rename"
  metriken:
    - name: "search_relevance"
      beschreibung: "Relevanz bei Suche nach Smart Name"
      messmethode: "Qdrant query, manuelles Review"
    - name: "rollback_success"
      beschreibung: "Erfolgsrate beim Wiederherstellen"
      aktueller_wert: "Abhängig von DB-Integrität"
    - name: "external_tool_compat"
      beschreibung: "Funktionieren Windows Search, Backup-Tools?"
      aktueller_wert: "Eingeschränkt (neue Namen)"

kandidat:
  implementierung: "Metadata-Layer in LanceDB/SQLite"
  schema: |
    {
      "sha256": "abc123...",
      "original_filename": "IMG_2024.jpg",
      "smart_name": "2024-12-26_Privat_Urlaub_Mallorca.jpg",
      "display_name": "smart_name",  # Für UI
      "physical_name": "original_filename"  # Unverändert
    }
  erwartete_verbesserung:
    - "rollback_success: 100% (Original unverändert)"
    - "external_tool_compat: 100% (Original-Namen bleiben)"
    - "search_relevance: Gleich (über Metadata-Suche)"

testbedingungen:
  daten: "200 Dateien verschiedener Typen"
  szenarien:
    - "Suche nach Smart Name in UI"
    - "Suche nach Original Name in Windows"
    - "Rollback nach 'falscher' Kategorisierung"
    - "Backup-Tool (robocopy) Kompatibilität"

erfolgskriterien:
  primaer: "search_relevance Kandidat >= Baseline"
  sekundaer: "rollback_success = 100%"
  tertiaer: "external_tool_compat = 100%"

testscript: |
  # tests/ab_test_filename.py

  def test_search_both_names(search_client, file_id: str) -> dict:
      """Testet ob sowohl Original als auch Smart Name gefunden werden."""
      metadata = get_metadata(file_id)

      results_smart = search_client.search(metadata["smart_name"])
      results_original = search_client.search(metadata["original_filename"])

      return {
          "smart_name_found": file_id in [r["id"] for r in results_smart],
          "original_name_found": file_id in [r["id"] for r in results_original]
      }

  def test_rollback(file_id: str) -> bool:
      """Testet Rollback auf Original-Zustand."""
      # Bei Metadata-Layer: Nur display_name ändern
      # Bei physischem Rename: Datei zurückbenennen
      return perform_rollback(file_id)
```

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf Claude-Analyse: **Option B (Metadata-Layer)**

### Begründung (vorläufig)
- "Content-addressed storage" Philosophie: SHA-256 ist der wahre Identifier
- Physischer Dateiname ist nur ein Attribut, kein Identifier
- Keine destruktiven Operationen = weniger Risiko

---

## Konsequenzen

### Wenn Option B gewinnt (Metadata-Layer)
**Positiv:**
- 100% reversibel
- Externe Tools funktionieren unverändert
- Backup-Kompatibilität

**Negativ:**
- UI muss "virtuellen Namen" anzeigen
- Windows Explorer zeigt Original-Namen

### Wenn Option A bleibt (Physisches Rename)
**Positiv:**
- Sofort sichtbar im Explorer
- Keine zusätzliche Abstraktionsschicht

**Negativ:**
- Destruktiv
- Rollback komplex
- DB-Abhängigkeit für Original-Namen

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision (VISION.md)? | [x] Ja - Datensicherheit ist Kernziel |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Metadata-Schema dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Quality Gates: `scripts/quality_gates.py`
- Smart Ingest: `scripts/smart_ingest.py`
