# Komponenten-Updates (Tika, WhisperX)

Dieses Projekt pinnt Versionen für eingebettete Komponenten über `.env`-Variablen,
so dass Updates reproduzierbar und steuerbar bleiben.

## Was wird gepinnt?

| Komponente | Variable | Verwendung |
| --- | --- | --- |
| Apache Tika (Docker) | `TIKA_TAG` | `docker-compose.yml`, `docker-compose.intelligence.yml` |
| WhisperX (PyPI) | `WHISPERX_VERSION` | Build-Arg in `infra/docker/whisperx-api/Dockerfile` |
| Faster-Whisper (deprecated) | `FASTER_WHISPER_TAG`, `FASTER_WHISPER_CUDA_TAG` | Docker Image-Tags (Legacy) |

> Hinweis: WhisperX ist der empfohlene Standard. Die Faster-Whisper-Container bleiben nur
> als Legacy-Profil verfügbar.

## Update-Workflow

1. **Versionen prüfen** (nur lesen):

```bash
python scripts/update_component_versions.py --env-file .env
```

2. **Pins aktualisieren** (schreibt in `.env`):

```bash
python scripts/update_component_versions.py --env-file .env --apply
```

3. **Docker neu bauen/ziehen**:

```bash
docker compose build whisperx
docker compose pull tika
```

## Hinweise

- Die Update-Skripte fragen die GitHub-Releases (Fallback: Tags) ab.
- Falls keine `.env` existiert, zuerst `.env.example` kopieren.
- Für reproduzierbare Builds sollten die Pins bewusst gepflegt werden (nicht dauerhaft `latest`).
