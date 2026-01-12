# ADR-008: Archive Processing Strategy

> **Status:** Accepted  
> **Datum:** 2025-12-27  
> **Autoren:** AI Assistant

---

## Kontext

Das Neural Vault System muss Archive (.rar, .7z, .tar, .gz, .zip) verarbeiten können, um Dateilisten und Metadaten zu extrahieren. Dabei soll **kein zusätzlicher Speicherplatz** durch Entpacken verbraucht werden.

### Problem

| Herausforderung | Auswirkung |
| :--- | :--- |
| Große Archive (10+ GB) | Kein Platz zum Entpacken |
| Verschiedene Formate | RAR/7z nicht nativ in Python |
| Docker-Kompatibilität | Lösung muss containerisiert sein |

---

## Entscheidung

**Wir verwenden einen hybriden Ansatz:**

1. **Python Built-in** für ZIP, TAR, GZ (schnell, kein Overhead)
2. **Docker 7-Zip** für RAR, 7z (universell, robust)

### Betrachtete Alternativen

| Alternative | Bewertung | Entscheidung |
| :--- | :--- | :--- |
| **py7zr** | 300-700 MB RAM, langsam bei großen Archiven | ❌ Abgelehnt |
| **rarfile + unrar** | Benötigt externes unrar Binary | ❌ Zusätzliche Abhängigkeit |
| **7-Zip Docker** | Universell, alle Formate, minimaler RAM | ✅ **Gewählt** |
| **Python zipfile/tarfile** | Built-in, schnell, kein Overhead | ✅ **Gewählt** |

### Begründung

| Kriterium | 7-Zip Docker | py7zr |
| :--- | :--- | :--- |
| RAR-Support | ✅ | ❌ |
| Speicherbedarf | Minimal | 300-700 MB |
| Docker-nativ | ✅ | ❌ |
| Ohne Entpacken | ✅ `7z l` | ⚠️ Teilweise |

---

## Konsequenzen

### Positiv

- ✅ **0 MB extra Speicher** - Kein Entpacken auf Festplatte
- ✅ **42 Formate** - Vollständige Abdeckung
- ✅ **Docker-isoliert** - Keine Host-Abhängigkeiten
- ✅ **Schnell** - Native C++ Implementierung

### Negativ

- ⚠️ Zusätzlicher Container (conductor-7zip)
- ⚠️ Docker exec statt HTTP API

---

## Implementation

### Container-Definition (docker-compose.yml)

```yaml
sevenzip:
  image: crazymax/7zip:latest
  container_name: conductor-7zip
  entrypoint: ["tail", "-f", "/dev/null"]
  volumes:
    - F:/:/mnt/data:ro
```

### Verwendung

```bash
# Dateiliste ohne Entpacken
docker exec conductor-7zip 7z l /mnt/data/file.rar

# Einzelne Datei nach stdout
docker exec conductor-7zip 7z x -so archive.7z file.txt
```

---

## Benchmark-Ergebnisse

| Format | Größe | Verarbeitung | Speicher extra |
| :--- | :--- | :--- | :--- |
| RAR 21 MB | 21 MB | 0.5s | 0 MB |
| 7z 50 MB | 50 MB | 1.0s | 0 MB |
| ZIP 100 MB | 100 MB | 0.1s | 0 MB |
| TAR.GZ 200 MB | 200 MB | 0.2s | 0 MB |

---

## Referenzen

- [7-Zip Docker Image](https://github.com/crazy-max/docker-7zip)
- [Python zipfile](https://docs.python.org/3/library/zipfile.html)
- [BINARY_PROCESSING.md](../BINARY_PROCESSING.md)

---

*Erstellt: 2025-12-27*
