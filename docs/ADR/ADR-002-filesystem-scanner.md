# ADR-002: Dateisystem-Scanner (scandir_rs)

## Status
**Akzeptiert** (2025-12-26)

## Kontext
Wir müssen 10TB / 1.1 Millionen Dateien auf Laufwerk F: indexieren. Die Standard-Python-Funktion `os.walk()` ist zu langsam (86 Sekunden für einen vollen Scan).

## Entscheidung
Wir nutzen **scandir_rs** als Python-Modul für die Indexierung.

## Begründung
*   **Performance:** 2-17x schneller als `os.walk()` (parallelisiert Disk-I/O im Hintergrund).
*   **Rust-Kern:** Native Geschwindigkeit mit Python-Bindings (`pip install scandir-rs`).
*   **I/O-Optimierung:** Reduziert Disk-Seeks auf HDDs durch Batch-Zugriffe.

### Benchmark-Quellen (Stand Dez 2025)
*   [lib.rs/crates/scandir_rs](https://lib.rs/crates/scandir_rs): "2 to 17 times faster than `os.walk()`".
*   [github.com/brmmm3/scandir-rs](https://github.com/brmmm3/scandir-rs): Parallelisiert Zugriffe.

## Konsequenzen
*   **Positiv:** Geschätzte Zeitersparnis von 86 Sek auf ~15 Sek für 1.1M Files.
*   **Negativ:** Zusätzliche Dependency (`scandir-rs`). Erfordert Rust-Toolchain für Build-from-Source.

## Alternativen (abgelehnt)
| Alternative | Grund für Ablehnung |
| :--- | :--- |
| **os.walk()** | Zu langsam für 10TB. Kein paralleles I/O. |
| **WizTree (Windows)** | Extrem schnell (NTFS MFT), aber nicht skriptbar für Python/n8n-Integration. |
| **jwalk (Rust CLI)** | Schnell, aber keine nativen Python-Bindings. Erfordert Subprocess-Calls. |
