# Error Classification System

Das Error Classification System ermöglicht die automatische Unterscheidung zwischen **fehlerhaften Quelldateien** und **Verarbeitungsfehlern** in der Neural Vault Pipeline.

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FEHLER-KLASSIFIKATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📁 QUELLDATEI-FEHLER          ⚙️ VERARBEITUNGS-FEHLER             │
│  ─────────────────────         ──────────────────────              │
│  • Leere Datei                 • OCR fehlgeschlagen                │
│  • Korrupte Datei              • Transkription fehler              │
│  • Falsches Format             • Konvertierung fehler              │
│  • Verschlüsselt               • Parsing fehler                    │
│  • Nicht gefunden              │                                   │
│                                │                                   │
│  → Kein Retry                  │  🔧 INFRASTRUKTUR-FEHLER          │
│  → Datei ersetzen              │  ────────────────────             │
│                                │  • Service nicht erreichbar       │
│                                │  • Timeout                        │
│                                │  • Speicherüberlauf               │
│                                │  • Abhängigkeit fehlt             │
│                                │                                   │
│                                │  → Auto-Retry                     │
│                                │  → Service prüfen                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Komponenten

### 1. SourceFileValidator

Validiert Quelldateien **vor** der Verarbeitung.

```python
from extraction_worker import SourceFileValidator

validator = SourceFileValidator()
result = validator.validate("/path/to/file.pdf")

# Ergebnis:
# {
#     'valid': True/False,
#     'errors': ['FILE_NOT_FOUND', 'EMPTY_FILE', ...],
#     'warnings': ['MAGIC_MISMATCH', 'SUSPICIOUSLY_SMALL'],
#     'file_health': 'healthy' | 'missing' | 'empty' | 'corrupted' | 'mislabeled' | 'inaccessible'
# }
```

#### Prüfungen

| Prüfung | Fehlercode | Beschreibung |
|---------|------------|--------------|
| Existenz | `FILE_NOT_FOUND` | Datei existiert nicht |
| Größe | `EMPTY_FILE` | Datei hat 0 Bytes |
| Lesbarkeit | `PERMISSION_DENIED` | Keine Leserechte |
| Magic Bytes | `MAGIC_MISMATCH` | Extension passt nicht zum Inhalt |
| PDF-Header | `PDF_INVALID_HEADER` | PDF beginnt nicht mit %PDF |
| PDF-Verschlüsselung | `PDF_ENCRYPTED` | PDF ist passwortgeschützt |
| PDF-Ende | `PDF_TRUNCATED` | PDF enthält kein %%EOF |
| ZIP-Integrität | `ZIP_CORRUPTED` | ZIP-Archiv ist beschädigt |
| ZIP-CRC | `ZIP_CRC_ERROR` | CRC-Prüfsumme fehlerhaft |

### 2. ErrorClassifier

Klassifiziert Exceptions basierend auf Fehlermeldungen.

```python
from extraction_worker import ErrorClassifier, ErrorSource, ErrorType

classifier = ErrorClassifier()
classified = classifier.classify(
    exception=some_exception,
    context={'file_path': '/path/to/file', 'worker': 'image-worker'}
)

# Ergebnis:
# ClassifiedError(
#     source=ErrorSource.SOURCE_FILE,
#     error_type=ErrorType.FILE_CORRUPTED,
#     message="cannot identify image file",
#     recoverable=False,
#     retry_recommended=False
# )
```

#### Fehlerquellen (ErrorSource)

| Quelle | Beschreibung | Retry? |
|--------|--------------|--------|
| `SOURCE_FILE` | Problem mit der Quelldatei | ❌ Nein |
| `PROCESSING` | Problem in der Verarbeitung | ✅ Ja |
| `INFRASTRUCTURE` | Problem mit Services | ✅ Ja |
| `UNKNOWN` | Unbekannter Fehler | ✅ Ja |

#### Fehlertypen (ErrorType)

**Quelldatei-Fehler:**
- `FILE_NOT_FOUND` - Datei nicht gefunden
- `FILE_EMPTY` - Leere Datei
- `FILE_CORRUPTED` - Beschädigte Datei
- `FILE_ENCRYPTED` - Verschlüsselte Datei
- `FILE_FORMAT_MISMATCH` - Falsches Format
- `FILE_PERMISSION_DENIED` - Keine Rechte

**Verarbeitungs-Fehler:**
- `EXTRACTION_FAILED` - Extraktion fehlgeschlagen
- `OCR_FAILED` - OCR fehlgeschlagen
- `TRANSCRIPTION_FAILED` - Transkription fehlgeschlagen
- `CONVERSION_FAILED` - Konvertierung fehlgeschlagen
- `PARSING_FAILED` - Parsing fehlgeschlagen

**Infrastruktur-Fehler:**
- `SERVICE_UNAVAILABLE` - Service nicht erreichbar
- `TIMEOUT` - Zeitüberschreitung
- `OUT_OF_MEMORY` - Speichermangel
- `DEPENDENCY_MISSING` - Abhängigkeit fehlt

### 3. Integration in Worker

Jeder Worker verwendet automatisch das Classification System:

```python
class BaseExtractionWorker:
    MAX_RETRIES = 3
    
    def __init__(self, ...):
        self.file_validator = SourceFileValidator()
        self.error_classifier = ErrorClassifier()
    
    async def process_job(self, job):
        try:
            # Verarbeitung...
        except Exception as e:
            classified = self.error_classifier.classify(e, context)
            
            if classified.retry_recommended and job.retries < MAX_RETRIES:
                # Retry
                await self.queue_manager.enqueue(self.input_queue, job)
            else:
                # DLQ mit Klassifikation
                await self.queue_manager.move_to_dlq_classified(self.dlq, job, classified)
```

## DLQ-Analyse

Der DLQ enthält jetzt erweiterte Informationen:

```json
{
    "id": "1768079014317-0",
    "path": "F:\\_Inbox\\test_image.heic",
    "filename": "test_image.heic",
    "error": "cannot identify image file",
    "error_source": "source_file",
    "error_type": "file_corrupted",
    "recoverable": false,
    "retry_recommended": false,
    "classification_details": {
        "file_path": "F:\\_Inbox\\test_image.heic",
        "extension": "heic",
        "worker": "image-worker-1",
        "retries": 0
    }
}
```

### Analyse-Befehle

```powershell
# Alle Fehler nach Quelle gruppieren
docker exec conductor-redis redis-cli -a change_me_in_prod XRANGE "dlq:extract" - + |
    Select-String '"error_source"'

# Nur Quelldatei-Fehler
docker exec conductor-redis redis-cli -a change_me_in_prod XRANGE "dlq:extract" - + |
    Select-String '"source_file"'

# Nur retryable Fehler
docker exec conductor-redis redis-cli -a change_me_in_prod XRANGE "dlq:extract" - + |
    Select-String '"retry_recommended": true'
```

## Entscheidungslogik

```
┌─────────────────────────────────────────────────────────────────┐
│                     FEHLER AUFGETRETEN                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  Fehler klassifizieren        │
              │  (ErrorClassifier.classify)   │
              └───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
    ┌─────────────────┐           ┌─────────────────────┐
    │ retry_recommended│           │ retry_recommended   │
    │     = FALSE      │           │      = TRUE         │
    └─────────────────┘           └─────────────────────┘
              │                               │
              │                   ┌───────────┴───────────┐
              │                   │                       │
              │                   ▼                       ▼
              │         ┌─────────────────┐    ┌─────────────────┐
              │         │ retries < MAX?   │    │ retries >= MAX  │
              │         └─────────────────┘    └─────────────────┘
              │                   │                       │
              │                   ▼                       │
              │         ┌─────────────────┐               │
              │         │ RE-QUEUE        │               │
              │         │ mit retries + 1 │               │
              │         └─────────────────┘               │
              │                                           │
              └───────────────────┬───────────────────────┘
                                  │
                                  ▼
                    ┌────────────────────────┐
                    │ DLQ mit Klassifikation │
                    │ (move_to_dlq_classified)│
                    └────────────────────────┘
```

## Best Practices

### 1. Vor der Verarbeitung validieren

```python
validation = self.file_validator.validate(job.path)
if not validation['valid']:
    # Sofort in DLQ, kein Retry
    classified = ClassifiedError(
        source=ErrorSource.SOURCE_FILE,
        error_type=ErrorType.FILE_CORRUPTED,
        message=f"Pre-validation failed: {validation['errors']}",
        recoverable=False,
        retry_recommended=False
    )
    await self.queue_manager.move_to_dlq_classified(self.dlq, job, classified)
    return
```

### 2. Infrastruktur-Fehler erkennen

Infrastruktur-Fehler sind oft temporär. Das System:
- Führt bis zu 3 Retries durch
- Wartet exponentiell länger zwischen Retries
- Loggt detaillierte Informationen

### 3. DLQ regelmäßig analysieren

```powershell
# Wöchentlicher Report
$dlq = docker exec conductor-redis redis-cli -a change_me_in_prod XLEN "dlq:extract"
Write-Host "DLQ Einträge: $dlq"

# Nach Quelldatei-Fehlern filtern (diese erfordern manuelle Aktion)
docker exec conductor-redis redis-cli -a change_me_in_prod XRANGE "dlq:extract" - + |
    Select-String '"source_file"' | Measure-Object
```

## Erweiterung

Um neue Fehlermuster hinzuzufügen:

```python
# In ErrorClassifier
SOURCE_FILE_PATTERNS = {
    ErrorType.FILE_CORRUPTED: [
        # Bestehende Muster...
        'mein_neues_muster',
    ],
}
```

## Siehe auch

- [DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md) - Systemarchitektur
- [README.md](../README.md) - Projektübersicht
- [extraction_worker.py](../docker/workers/extraction_worker.py) - Implementierung
