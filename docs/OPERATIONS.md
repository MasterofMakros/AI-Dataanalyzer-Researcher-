# Operations Manual

> **Neural Vault Conductor** - System Operations Guide
> Target Audience: DevOps, System Admins

---

## 1. System Status & Health Checks

### Quick Health Check
Run the status command in the scripts directory:
```bash
./scripts/start_pipeline.sh --status
# or on Windows
.\scripts\start_pipeline.ps1 -Status
```

### Critical Endpoints
| Component | URL | Health Check |
|-----------|-----|--------------|
| **Mission Control** | `http://localhost:3000` | `/health` |
| **API** | `http://localhost:8010` | `/health` |
| **Neural Search** | `http://localhost:8040` | `/health` |
| **Vector DB (Qdrant)** | `http://localhost:6335` | `/healthz` |
| **Search (Meili)** | `http://localhost:7700` | `/health` |

---

## 2. Backup & Restore Procedures

### 2.1 What to Backup
The system state is persisted in Docker Volumes. Critical volumes:
- `postgres_data` (n8n workflow state)
- `qdrant_data` (Vector embeddings)
- `meilisearch_data` (Search index)
- `conductor_api_data` (Feedback & Config)

### 2.2 Backup Script
Use the provided backup utility (if available) or standard Docker volume backup:

```bash
# Backup Volume to Tarball
docker run --rm -v postgres_data:/volume -v $(pwd):/backup alpine tar -czf /backup/postgres_backup.tar.gz -C /volume .
docker run --rm -v qdrant_data:/volume -v $(pwd):/backup alpine tar -czf /backup/qdrant_backup.tar.gz -C /volume .
```

### 2.3 Restore Script
**WARNING**: This will overwrite existing data. Stop services first.

```bash
docker compose stop
docker run --rm -v postgres_data:/volume -v $(pwd):/backup alpine sh -c "rm -rf /volume/* && tar -xzf /backup/postgres_backup.tar.gz -C /volume"
docker compose start
```

---

## 3. Maintenance & Updates

### 3.1 Updating Images
To pull the latest images defined in `docker-compose.yml`:
```bash
docker compose pull
docker compose up -d
```

### 3.2 Cleaning Up (Pruning)
Remove unused containers, networks, and dangling images:
```bash
docker system prune -f
```
To remove unused volumes (CAUTION: deletes data):
```bash
docker volume prune -f
```

---

## 4. Troubleshooting

### Issue: "Ports already allocated"
**Symptoms**: Docker fails to start with "Bind for 0.0.0.0:8010 failed".
**Solution**:
1. Check what's running: `docker ps`
2. Stop rogue containers: `docker stop <container_id>`
3. Check system processes (Windows): `netstat -ano | findstr :8010`

### Issue: "GPU not found"
**Symptoms**: Logs show "Using CPU fallback" or `nvidia-smi` fails.
**Solution**:
1. Verify NVIDIA Drivers are installed.
2. Verify Docker Desktop has GPU support enabled (WSL2 integration).
3. Run: `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi`

### Issue: "Meilisearch Key Invalid"
**Symptoms**: API logs show 401/403 errors connecting to Search.
**Solution**:
1. Check `.env` for `MEILI_MASTER_KEY`.
2. Ensure the key is at least 16 chars.
3. Restart Meilisearch: `docker compose restart meilisearch`

---

## 5. Security Best Practices
- **Secrets**: Never commit `.env` to Git. Use `.env.example`.
- **Network**: Prod ports should bind to `127.0.0.1` unless behind a secure proxy (Traefik).
- **Users**: Run containers as non-root where possible (future work).
