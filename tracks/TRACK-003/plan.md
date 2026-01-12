# Plan: Advanced Multi-LLM RAG Stack (Hardened Implementation)

## Phase 1: Pi Infrastructure
- [ ] **Step 1.1**: Redis Setup with Security
    - *Task*: Install Redis with password auth.
    - *Config*: `requirepass <strong_password>`.
    - *Schema*: Define keys: `job:queue`, `job:status:<id>`, `command:mode`, `heartbeat:laptop`.
- [ ] **Step 1.2**: FastAPI Receiver
    - *Task*: Create `receiver_api.py`.
    - *Endpoints*:
        - `POST /append` (atomic file append with UTF-8 validation).
        - `POST /heartbeat` (updates `heartbeat:laptop` with TTL).
        - `GET /next_job` (returns next pending job, marks as "locked").
    - *Security*: Validate auth token in header.

## Phase 2: Laptop Docker Stack (RTX 5090)
- [ ] **Step 2.1**: NVIDIA Docker Setup
    - *Task*: Install NVIDIA Container Toolkit on Windows.
    - *Test*: `docker run --gpus all nvidia/cuda:12.0-base nvidia-smi`.
- [ ] **Step 2.2**: `docker-compose.gpu.yml`
    - *Services*:
        - `whisper-worker`: `onerahmet/openai-whisper-asr-webservice:latest-gpu`.
        - `ollama`: `ollama/ollama` with GPU passthrough.
        - `syncer-bot`: Custom Python image.
- [ ] **Step 2.3**: Syncer Bot (`worker_node.py`)
    - *Features*:
        - **Command Polling**: Check Redis `command:mode` every 2s.
        - **Graceful Shutdown**: On `GAMING` mode, finish sentence, then sleep.
        - **File Isolation**: Copy to `/tmp/` before Whisper.
        - **Chunked Processing**: 5-min segments via `ffmpeg -ss -t`.
        - **Retry Logic**: 3 retries on network failure.

## Phase 3: Perplexica Dashboard (Pi-Hosted)
- [ ] **Step 3.1**: Streamlit App (`dashboard.py`)
    - *Auth*: PIN entry screen (4-digit, 3 attempts, 5-min lockout).
    - *Components*:
        - **GPU Telemetry Card**: VRAM, Temp (from Redis heartbeat).
        - **Mode Switcher**: 3 buttons with 2s debounce.
        - **Job Queue**: Virtualized table (max 50 visible rows).
        - **Live Log**: Last 20 log entries.
- [ ] **Step 3.2**: UX Safeguards
    - *Skeleton Loaders*: For all data-fetching components.
    - *Toast System*: Success/Error notifications with "Undo" (5s).
    - *Status Badges*: Include elapsed time (`Processing (12 min)`).
    - *Empty State*: Friendly illustration + "All caught up!" text.
- [ ] **Step 3.3**: Mobile Optimization
    - *Layout*: Stacked cards on `sm` breakpoint.
    - *FAB*: Floating "Gaming Mode" button (always visible).
    - *Touch Targets*: Min 48x48px for all buttons.

## Phase 4: Network & Security
- [ ] **Step 4.1**: Tailscale Setup
    - *Task*: Install Tailscale on Pi and Laptop.
    - *Config*: Enable MagicDNS for friendly names (`pi-home`, `laptop-gpu`).
- [ ] **Step 4.2**: Input Sanitization
    - *Task*: Add `sanitize_filename()` function.
    - *Rules*: Strip `../`, escape HTML, validate UTF-8.
- [ ] **Step 4.3**: Rate Limiting
    - *Task*: Limit `/append` to 10 requests/second per client.
    - *Tool*: `slowapi` library for FastAPI.

## Phase 5: Resilience & Logging
- [ ] **Step 5.1**: Graceful Shutdown Protocol
    - *Flow*:
        1. Dashboard sets `command:mode = SHUTDOWN_REQUESTED`.
        2. Worker finishes current sentence (max 5s).
        3. Worker sets `command:mode = GAMING`.
        4. Dashboard shows "Stopped Safely".
- [ ] **Step 5.2**: Log Management
    - *Location*: `/dev/shm/transcription.log` (RAM disk).
    - *Rotation*: Hourly sync to SD card, keep 7 days.
    - *Format*: JSON lines (`{"ts": ..., "event": ..., "file": ...}`).
- [ ] **Step 5.3**: Health Monitoring
    - *Heartbeat Check*: If `heartbeat:laptop` TTL expires → status = "Offline".
    - *Alert*: If offline > 1 hour, send notification (ntfy.sh).

## Phase 6: Testing & Validation
- [ ] **Step 6.1**: Unit Tests
    - *Coverage*: `sanitize_filename()`, `append_to_file()`, `parse_timestamp()`.
- [ ] **Step 6.2**: Integration Tests
    - *Scenario*: Full transcription cycle with simulated disconnect.
- [ ] **Step 6.3**: Manual QA Checklist
    - Run all test cases from spec (TC-01 to TC-08).
