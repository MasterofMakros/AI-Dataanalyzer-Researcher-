# ADR-021: Tabellen-Suche - Raw Text vs. Data Narrator

## Status
**Proposed** - A/B-Test erforderlich (ABT-N02)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Neues Konzept das fehlt"
- **Gemini 3 Pro:** "Data Narrator - CSV/Excel → KI-Zusammenfassung"

---

## Kontext und Problemstellung

Aktueller Zustand:
- CSV/Excel werden als "roher Text" indexiert
- Spaltenköpfe und Werte vermischt
- LLM erhält "Token-Salat"

**Beispiel Problem:**
```
# Roher Text aus Excel
Name,Betrag,Datum
Bauhaus,127.50,2024-12-15
OBI,89.90,2024-12-18
```

**Was LLM sieht:** Unstrukturierter Text ohne Kontext

**Was LLM braucht:** "Tabelle mit 2 Baumarkt-Rechnungen, Gesamtsumme 217.40€"

**Kritikalität:** NEW FEATURE - Notwendig für sinnvolle Suche in strukturierten Daten

---

## Entscheidungstreiber (Decision Drivers)

* **LLM-Verständnis:** KI muss Tabelleninhalte verstehen
* **Suchrelevanz:** Suche "Ausgaben über 100€" muss funktionieren
* **Speichereffizienz:** Nicht alle 10.000 Zeilen speichern

---

## Betrachtete Optionen

1. **Option A (Baseline):** Roher Text (aktuell)
2. **Option B (Kandidat):** Data Narrator (statistische Zusammenfassung)
3. **Option C:** Strukturierte JSON-Speicherung

---

## A/B-Test Spezifikation

### Test-ID: ABT-N02

```yaml
hypothese:
  these: "Data Narrator ermöglicht semantische Suche in Tabellen"
  null_hypothese: "Roher Text ist für Suche ausreichend"

baseline:
  implementierung: "CSV/Excel → Plain Text → LanceDB"
  metriken:
    - name: "query_accuracy"
      beschreibung: "Kann Frage 'Höchster Wert in Spalte X?' beantwortet werden?"
      aktueller_wert: "~20% (meist 'nicht gefunden')"
    - name: "semantic_search_relevance"
      beschreibung: "Finden 'alle Rechnungen über 100€'"
      aktueller_wert: "Niedrig"

kandidat:
  implementierung: |
    import pandas as pd
    from typing import Optional

    def narrate_table(
        df: pd.DataFrame,
        file_path: str,
        max_preview_rows: int = 20
    ) -> str:
        """
        Generiert natürlichsprachliche Beschreibung einer Tabelle.

        Returns:
            Markdown-Text für LLM-Kontext und Suche
        """
        narrative = []

        # 1. Basis-Info
        narrative.append(f"# Tabelle: {Path(file_path).name}")
        narrative.append(f"")
        narrative.append(f"## Übersicht")
        narrative.append(f"- **Zeilen:** {len(df)}")
        narrative.append(f"- **Spalten:** {', '.join(df.columns)}")

        # 2. Spaltentypen und Statistik
        narrative.append(f"")
        narrative.append(f"## Spalten-Analyse")

        for col in df.columns:
            col_type = df[col].dtype
            if pd.api.types.is_numeric_dtype(df[col]):
                stats = df[col].describe()
                narrative.append(
                    f"- **{col}** (Numerisch): "
                    f"Min={stats['min']:.2f}, Max={stats['max']:.2f}, "
                    f"Durchschnitt={stats['mean']:.2f}, Summe={df[col].sum():.2f}"
                )
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                narrative.append(
                    f"- **{col}** (Datum): "
                    f"Von {df[col].min()} bis {df[col].max()}"
                )
            else:
                unique = df[col].nunique()
                top_values = df[col].value_counts().head(5).to_dict()
                narrative.append(
                    f"- **{col}** (Text): {unique} eindeutige Werte. "
                    f"Häufigste: {top_values}"
                )

        # 3. Preview
        narrative.append(f"")
        narrative.append(f"## Vorschau (erste {min(max_preview_rows, len(df))} Zeilen)")
        narrative.append(df.head(max_preview_rows).to_markdown(index=False))

        # 4. Auffälligkeiten
        narrative.append(f"")
        narrative.append(f"## Auffälligkeiten")

        # Höchste/Niedrigste Werte
        for col in df.select_dtypes(include=['number']).columns:
            max_row = df.loc[df[col].idxmax()]
            narrative.append(f"- Höchster **{col}**: {max_row.to_dict()}")

        return "\n".join(narrative)
  erwartete_verbesserung:
    - "query_accuracy: >= 80%"
    - "semantic_search_relevance: Hoch"
    - "LLM kann Fragen zu Tabellen beantworten"

testbedingungen:
  daten:
    - "20 CSV-Dateien (Kontoauszüge, Inventarlisten)"
    - "20 Excel-Dateien (Rechnungen, Reports)"
  test_queries:
    - "Was ist die höchste Ausgabe?"
    - "Wie viele Einträge sind über 100€?"
    - "Wann war die letzte Transaktion?"
    - "Welcher Lieferant hat die meisten Rechnungen?"

erfolgskriterien:
  primaer: "query_accuracy Kandidat > 70%"
  sekundaer: "Narrative-Länge < 5000 Tokens (LLM-Limit)"
  tertiaer: "Generation-Zeit < 1s pro Tabelle"

testscript: |
  # tests/ab_test_data_narrator.py

  def test_table_question_answering(
      search_client,
      llm_client,
      test_queries: list
  ) -> dict:
      """Testet ob LLM Tabellen-Fragen beantworten kann."""

      results = {"correct": 0, "total": len(test_queries)}

      for query in test_queries:
          # Suche relevante Tabellen
          docs = search_client.search(query["question"], top_k=3)

          # LLM mit Kontext fragen
          context = "\n\n".join([d["content"] for d in docs])
          answer = llm_client.complete(
              f"Kontext:\n{context}\n\nFrage: {query['question']}\nAntwort:"
          )

          # Gegen Ground Truth prüfen
          if query["expected_answer"].lower() in answer.lower():
              results["correct"] += 1

      results["accuracy"] = results["correct"] / results["total"]
      return results
```

---

## Beispiel-Output

**Input:** `Kontoauszug_2024.csv` (500 Zeilen)

**Data Narrator Output:**
```markdown
# Tabelle: Kontoauszug_2024.csv

## Übersicht
- **Zeilen:** 500
- **Spalten:** Datum, Beschreibung, Betrag, Saldo

## Spalten-Analyse
- **Datum** (Datum): Von 2024-01-02 bis 2024-12-28
- **Beschreibung** (Text): 342 eindeutige Werte. Häufigste: {'Amazon': 45, 'Rewe': 38}
- **Betrag** (Numerisch): Min=-1500.00, Max=3200.00, Durchschnitt=-127.50, Summe=-63750.00
- **Saldo** (Numerisch): Min=1234.56, Max=15678.90, Durchschnitt=8456.78

## Vorschau (erste 20 Zeilen)
| Datum      | Beschreibung    | Betrag  | Saldo    |
|------------|-----------------|---------|----------|
| 2024-01-02 | Gehalt          | 3200.00 | 15678.90 |
| 2024-01-03 | Miete           | -950.00 | 14728.90 |
...

## Auffälligkeiten
- Höchster **Betrag**: {'Datum': '2024-01-02', 'Beschreibung': 'Gehalt', 'Betrag': 3200.0}
- Niedrigster **Betrag**: {'Datum': '2024-03-15', 'Beschreibung': 'Versicherung', 'Betrag': -1500.0}
```

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf Gemini-Analyse: **Option B (Data Narrator)**

### Begründung (vorläufig)
- Gemini: "Statt rohe CSV zu speichern, generiert ein Skript eine Beschreibung"
- Claude: "Fehlte komplett im System"
- Notwendig für sinnvolle Q&A über Tabellendaten

---

## Konsequenzen

### Wenn Option B gewinnt (Data Narrator)
**Positiv:**
- LLM versteht Tabellen
- Semantische Suche funktioniert
- Speicherplatz gespart (Zusammenfassung statt alle Zeilen)

**Negativ:**
- Zusätzliche Verarbeitungszeit
- Detailverlust bei großen Tabellen
- Pandas-Abhängigkeit

### Wenn Option A bleibt (Raw Text)
**Positiv:**
- Einfacher
- Alle Daten vorhanden

**Negativ:**
- LLM kann keine Fragen beantworten
- Token-Limit-Probleme bei großen Tabellen

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision (VISION.md)? | [x] Ja - "Suche in allen Formaten" |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Narrator-Konfiguration dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Format Processing: [FORMAT_PROCESSING_SPEC.md](../FORMAT_PROCESSING_SPEC.md)
- Neural Worker: `docker/neural-worker/`
