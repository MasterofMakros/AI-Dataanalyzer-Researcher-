# Track Spec: Advanced Multi-LLM RAG Stack (Hardened Edition)

## Problem
The user has a **Raspberry Pi 4** (Storage/Server) and a **Laptop with RTX 5090 24GB** (Compute Beast). 
**Critical Challenges**:
1.  Stability: Laptop may go offline mid-transcription.
2.  Resilience: Progress must never be lost.
3.  UX: Mobile control must be responsive and error-proof.
4.  Security: Prevent unauthorized access via Tailscale network.

---

## Solution Architecture: "The Power Plant Model" (v2.0 Hardened)

### 1. The Storage Node (Raspberry Pi 4)
*   **Role**: Single Source of Truth (Data + State + Command Center).
*   **Services**:
    *   **Nextcloud**: Files (Read-Only for Worker).
    *   **Redis**: Tracks job status + stores commands + heartbeat.
    *   **Streamlit Dashboard**: The "Command Center" UI.
    *   **Receiver API (FastAPI)**: Accepts streamed text chunks with atomic writes.

### 2. The Compute Node (Laptop / RTX 5090)
*   **Role**: Stateless AI Worker.
*   **Stack (Docker with NVIDIA Toolkit)**:
    *   **`whisper-worker`**: Whisper Large-v3 (CUDA).
    *   **`llm-server`**: Ollama (Llama 3 70B).
    *   **`syncer-bot`**: Python Agent (Resilient).
*   **Workflow (Hardened)**:
    1.  Bot polls Redis for `command_mode` (CRUNCH/OFFICE/GAMING).
    2.  If `GAMING`: Bot enters sleep loop (checks every 5s).
    3.  If `CRUNCH`: Bot fetches next job from queue.
    4.  **File Isolation**: Copies file to local `/tmp/` before processing (avoids SMB lock).
    5.  Transcribes in 5-minute chunks.
    6.  **Atomic Upload**: After each chunk, calls Pi's `/append` API.
    7.  **Graceful Shutdown**: On `STOP` command, finishes current sentence, then sleeps.

### 3. Perplexica Dashboard (Pi-Hosted, Mobile-First)
*   **Tech**: Streamlit + Redis + shadcn/ui design principles.
*   **Access**: Tailscale VPN (`http://100.x.y.z:8501`).
*   **Authentication**: 4-digit PIN stored in Redis (hashed).

---

## Error Mitigation Strategies

### A. Race Condition Prevention
| Issue | Solution |
|:---|:---|
| Mode switch during write | `SHUTDOWN_REQUESTED` flag + 5s grace period before hard stop |
| Multiple clicks on button | **Debounce**: Disable button for 2s after click |
| Heartbeat micro-outage | **3-Tier Status**: "Online" → "Connecting..." (30s) → "Offline" (60s+) |

### B. Data Integrity
| Issue | Solution |
|:---|:---|
| SMB file lock conflict | Worker copies to `/tmp/` first, works on local copy |
| Partial UTF-8 corruption | Whisper outputs full sentences; API validates UTF-8 before append |
| Duplicate transcription | Redis job lock with TTL; only 1 worker can claim a job |

### C. UX Safeguards
| Issue | Solution |
|:---|:---|
| Empty state confusion | Friendly "All caught up!" message with illustration |
| Accidental skip | Toast with 5s "Undo" button |
| Slow network loading | Skeleton loaders for all components |
| Status ambiguity | Badge shows elapsed time: `Processing (12 min)` |

### D. Security
| Issue | Solution |
|:---|:---|
| Unauthorized access | PIN authentication on dashboard load |
| Path traversal in filenames | Validate: path must start with `/mnt/nextcloud/` |
| XSS in filenames | `html.escape()` all user-provided strings |
| Log injection | Structured logging (JSON), no raw string concat |

### E. Performance
| Issue | Solution |
|:---|:---|
| 10k+ files in queue | **Virtualized DataTable** (only render visible rows) |
| Redis memory overflow | TTL on heartbeat keys (5 min), cleanup job for old logs |
| SD card wear | Logs written to RAM disk (`/dev/shm/`), synced hourly |

---

## Test Case Matrix

| ID | Scenario | Expected Behavior | Priority |
|:---|:---|:---|:---|
| TC-01 | Laptop offline mid-transcription | `partial.md` preserved, resume on reconnect | P0 |
| TC-02 | User clicks "Gaming Mode" during write | Graceful stop after current sentence | P0 |
| TC-03 | Rapid button clicks (5x in 1s) | Only 1 command executed | P1 |
| TC-04 | Filename with emoji `🎵song.mp3` | Displays correctly (UTF-8) | P1 |
| TC-05 | Queue empty | "All done!" message, no error | P2 |
| TC-06 | Tailscale disconnects during use | "Reconnecting..." overlay, auto-retry | P1 |
| TC-07 | PIN entered incorrectly 3x | 5-minute lockout | P1 |
| TC-08 | File > 2GB transcribed | Chunked processing works, no crash | P0 |
