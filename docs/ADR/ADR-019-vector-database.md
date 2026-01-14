# ADR-019: Vector Database - Qdrant vs. LanceDB für Scale

**Status**
Accepted (Qdrant-Only)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Qdrant empfohlen" (vor Gemini-Input)
- **Gemini 3 Pro:** "LanceDB ('Neural Spine') für Massendaten, Qdrant bei >100k zu viel RAM"

---

## Kontext und Problemstellung

Aktuelle Implementierung:
- Qdrant (Docker: qdrant/qdrant) als primäre Vector DB
- LanceDB im neural-worker als "Neural Spine"
- Zwei parallele Systeme

**Problem laut Gemini:**
- Qdrant verbraucht viel RAM bei > 100k Dokumenten
- LanceDB ist für Massendaten optimiert (Column Store)

**Kritikalität:** BLUE BUTTON - Skalierbarkeit sicherstellen

---

## Entscheidungstreiber (Decision Drivers)

* **Skalierbarkeit:** 500k+ Dokumente müssen funktionieren
* **RAM-Effizienz:** Homelab hat begrenzte Ressourcen (32GB)
* **Query-Latenz:** Suche muss schnell bleiben

---

## Betrachtete Optionen

1. **Option A (Baseline):** Nur Qdrant
2. **Option B (Kandidat):** Nur LanceDB
3. **Option C:** Hybrid (Qdrant für Hot Data, LanceDB für Archive)

---

## Tool-Vergleich

| Feature | Qdrant | LanceDB |
|---------|--------|---------|
| RAM bei 100k Docs | ~2-4GB | ~500MB |
| RAM bei 500k Docs | ~10-20GB | ~2-3GB |
| Query Latenz | ~10-50ms | ~50-100ms |
| Batch Insert | Mittel | Sehr schnell |
| Filtering | Sehr gut | Gut |
| Persistence | Disk + Memory | Disk-native |
| Clustering | Ja (distributed) | Nein |

---

## A/B-Test Spezifikation

### Test-ID: ABT-B05

```yaml
hypothese:
  these: "LanceDB ist bei >100k Dokumenten RAM-effizienter ohne signifikanten Latenz-Nachteil"
  null_hypothese: "Qdrant ist auch bei Scale die bessere Wahl"

baseline:
  implementierung: "Qdrant (Port 6335/6336)"
  metriken:
    - name: "ram_usage_100k"
      beschreibung: "RAM bei 100.000 Vektoren"
      messmethode: "docker stats"
      aktueller_wert: "~2-3GB"
    - name: "ram_usage_500k"
      beschreibung: "RAM bei 500.000 Vektoren"
      aktueller_wert: "EXTRAPOLIERT ~10-15GB"
    - name: "query_latency_p50"
      beschreibung: "Median Query-Zeit"
      aktueller_wert: "~20ms"
    - name: "insert_throughput"
      beschreibung: "Vektoren/Sekunde beim Insert"
      aktueller_wert: "~500/s"

kandidat:
  implementierung: "LanceDB (im neural-worker)"
  erwartete_verbesserung:
    - "ram_usage_500k: < 4GB"
    - "query_latency_p50: < 100ms"
    - "insert_throughput: >= 1000/s"

testbedingungen:
  hardware: "32GB RAM, NVMe SSD"
  daten:
    - "Phase 1: 10.000 Vektoren"
    - "Phase 2: 100.000 Vektoren"
    - "Phase 3: 500.000 Vektoren (wenn möglich)"
  vektor_dimension: "1024 (nomic-embed-text)"

erfolgskriterien:
  primaer: "ram_usage_500k LanceDB < ram_usage_500k Qdrant * 0.5"
  sekundaer: "query_latency_p50 LanceDB < 2 * Qdrant"
  tertiaer: "insert_throughput LanceDB >= Qdrant"

testscript: |
  # tests/ab_test_vector_db.py

  import time
  import numpy as np
  import psutil

  def benchmark_vector_db(db_client, num_vectors: int, vector_dim: int = 1024):
      """Benchmarkt Vector DB für Insert und Query."""

      # 1. Insert Benchmark
      vectors = np.random.rand(num_vectors, vector_dim).astype(np.float32)
      metadata = [{"id": i, "text": f"doc_{i}"} for i in range(num_vectors)]

      start = time.perf_counter()
      db_client.upsert(vectors, metadata)
      insert_time = time.perf_counter() - start

      # 2. RAM messen
      ram_mb = psutil.Process().memory_info().rss / 1024 / 1024

      # 3. Query Benchmark
      query_vector = np.random.rand(vector_dim).astype(np.float32)
      latencies = []

      for _ in range(100):
          start = time.perf_counter()
          results = db_client.search(query_vector, top_k=10)
          latencies.append((time.perf_counter() - start) * 1000)

      return {
          "num_vectors": num_vectors,
          "insert_time_s": insert_time,
          "insert_throughput": num_vectors / insert_time,
          "ram_mb": ram_mb,
          "query_latency_p50_ms": np.percentile(latencies, 50),
          "query_latency_p99_ms": np.percentile(latencies, 99)
      }
```

---

## Hybrid-Architektur (Option C)

```python
class HybridVectorStore:
    """
    Qdrant für Hot Data (letzte 30 Tage)
    LanceDB für Cold Data (Archiv)
    """

    def __init__(self):
        self.hot_store = QdrantClient("localhost", port=6333)
        self.cold_store = lancedb.connect("/lancedb_storage")
        self.hot_cutoff_days = 30

    def search(self, query_vector, top_k=10):
        # Suche zuerst in Hot Store
        hot_results = self.hot_store.search(query_vector, limit=top_k)

        if len(hot_results) < top_k:
            # Ergänze aus Cold Store
            cold_results = self.cold_store.search(query_vector, limit=top_k)
            return self._merge_results(hot_results, cold_results, top_k)

        return hot_results

    def migrate_to_cold(self):
        """Verschiebt alte Vektoren von Qdrant nach LanceDB."""
        cutoff = datetime.now() - timedelta(days=self.hot_cutoff_days)
        old_vectors = self.hot_store.get_older_than(cutoff)
        self.cold_store.insert(old_vectors)
        self.hot_store.delete(old_vectors.ids)
```

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf Gemini-Analyse: **Option C (Hybrid)**

### Begründung (vorläufig)
- Gemini explizit: "LanceDB für Massendaten, Qdrant für Chat"
- Hybrid nutzt Stärken beider Systeme
- RAM-Effizienz bei Scale kritisch für Homelab

---

## Konsequenzen

### Wenn Option C gewinnt (Hybrid)
**Positiv:**
- RAM-Effizienz bei Scale
- Schnelle Queries für aktuelle Daten
- Archiv skaliert unbegrenzt

**Negativ:**
- Komplexere Architektur
- Migration-Job erforderlich
- Zwei Systeme zu warten

### Wenn Option A bleibt (Nur Qdrant)
**Positiv:**
- Einfachere Architektur
- Einheitliche API

**Negativ:**
- RAM-Probleme bei > 200k Dokumenten
- Teures Hardware-Upgrade nötig

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision ([product/vision.md](../product/vision.md))? | [x] Ja - Skalierbarkeit ist Kernziel |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Hot/Cold Migration dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Vector Database ADR: [ADR-001-vector-database.md](./ADR-001-vector-database.md)
- Neural Worker: `docker/neural-worker/` (LanceDB)
- Docker Compose: `docker-compose.yml` (Qdrant)
