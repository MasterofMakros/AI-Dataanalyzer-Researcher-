# Plan: Smart Media Handling

## Phase 1: The Normalizer (FFMPEG)
- [ ] **Step 1.1**: Create `normalize_audio.py`
    - *Task*: Script that recursively scans folders.
    - *Action*: Converts non-WAV audio to 16kHz Mono WAV (temp file).
## Phase 2: The Compute Node Setup (Laptop/5090)
- [ ] **Step 2.1**: Deploy Docker Stack on Windows
    - *Stack*: `ollama` (GPU), `whisper-server` (GPU).
    - *Config*: Enable NVIDIA Container Toolkit.
- [ ] **Step 2.2**: The "Resilient Worker" Script
    - *Task*: Create `worker_node.py`.
    - *Logic*:
        - Connect to Pi (SSH/Tailscale).
        - Scan `_Inbox` for media.
        - **Chunked Processing**: Split audio into 5-minute segments using `ffmpeg` (on Laptop).
        - Transcribe -> Upload Segment -> Verify -> Delete Local Segment.
    - *Benefit*: If crash happens, only last 5-min segment is lost.

## Phase 3: The Pi "State Manager"
- [ ] **Step 3.1**: Job Logger
    - *Task*: Pi maintains `transcription_state.json`.
    - *Status*: `file_path`: `last_wip_timestamp`.
- [ ] **Step 3.2**: Partial Result Handler
    - *Task*: Ensure `_transcript.md` updates are atomic (append-only).
