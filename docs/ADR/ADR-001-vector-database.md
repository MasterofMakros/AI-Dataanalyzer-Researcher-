# ADR-001: Vektor-Datenbank (Qdrant)

## Status
**Akzeptiert** (2025-12-26)

## Kontext
Wir brauchen eine Vektordatenbank für 10TB+ Daten mit Hybrid-Suche (Keyword + Semantic). Die Datenbank muss lokal auf einer einzelnen Maschine (Ryzen AI Mini-PC) laufen.

## Entscheidung
Wir wählen **Qdrant** (Rust-basiert).

## Begründung
*   **Query Latency:** 10-30ms pro Anfrage (für unser SLA "<3 Sekunden" mehr als ausreichend).
*   **Rich Metadata Filtering:** Kritisch für Anfragen wie "Zeige Rechnungen von 2024".
*   **Geringer RAM-Footprint:** Rust ist effizienter als Java (Elasticsearch) oder C++ (Milvus) für Single-Node-Deployments.
*   **Docker-Deployment:** Trivial (`docker run qdrant/qdrant`).
*   **Hybrid Search:** Native Unterstützung für BM25 + Dense Vectors (seit 2024).

### Benchmark-Quellen (Stand Dez 2025)
*   [qdrant.tech/benchmarks](https://qdrant.tech/benchmarks): 4x RPS Gewinn gegenüber Alternativen.
*   [f22labs.com](https://f22labs.com/blog/milvus-vs-qdrant): Niedrigere Query-Latenz als Milvus bei vergleichbarer Recall-Rate.

## Konsequenzen
*   **Positiv:** Schnell, energieeffizient, einfaches Deployment.
*   **Negativ:** Kleinere Community als Elasticsearch. Weniger Enterprise-Plugins.

## Alternativen (abgelehnt)
| Alternative | Grund für Ablehnung |
| :--- | :--- |
| **Elasticsearch** | Zu RAM-hungrig (Java). Overhead für Single-Node. |
| **Milvus** | Distributed-Architektur, erfordert Kubernetes für volle Leistung. Overkill. |
| **LanceDB** | Embedded, gut für Edge. Aber: Weniger Filtering-Optionen als Qdrant. Als Cache für n8n evaluieren. |
