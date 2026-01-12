# Legacy Components

This directory contains archived components that have been superseded by the `docker/` microservices architecture or are no longer actively maintained.

## Contents

- `backend_api/`: Old Python API implementation. Superseded by `docker/conductor-api`.
- `infrastructure/`: Old deployment scripts. Now handled by root `docker-compose.yml`.
- `n8n_stack/`: Separate n8n deployment. Now integrated in main `docker-compose.yml`.
- `services/`: Old service definitions.
- `worker_node/`: Standalone Python worker. Superseded by `docker/workers` and `docker/document-processor`.

**Note:** Do not develop new features in these folders. Refer to them only for migration logic.
