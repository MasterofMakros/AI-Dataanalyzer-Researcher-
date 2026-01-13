# Runbook: Troubleshooting

> Ziel: Häufige Start- und Healthcheck-Probleme schnell lösen.

## Compose-Status prüfen
```bash
docker compose ps
```

## Logs anzeigen
```bash
docker compose logs conductor-api
docker compose logs neural-search-api
docker compose logs perplexica
```

## Healthchecks manuell prüfen
```bash
curl http://localhost:8010/health
curl http://localhost:8040/health
curl http://localhost:3100
```

## Qdrant erreichbar?
```bash
curl http://localhost:6335/collections
```
