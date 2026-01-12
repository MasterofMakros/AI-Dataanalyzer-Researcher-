# examples/docker_patterns

## Purpose
Explains how Docker Compose services and profiles are structured in Conductor.

## What to copy
- **Profiles:** Use `profiles: [gpu, intelligence]` to segment heavy services.
- **Healthchecks:** Use `curl -f http://localhost:PORT/health` conventions.
- **Resources:** Always define `deploy.resources.limits`.

## Links to real files
- [docker-compose.yml](../../docker-compose.yml) (Main definition)
