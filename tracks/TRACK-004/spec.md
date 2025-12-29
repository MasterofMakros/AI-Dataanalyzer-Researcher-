# Track Spec: Smart Media Handling & Transcription

## Problem
The user has ~4,000 mixed media files (MP4, MP3, OGG, AVI) on a Raspberry Pi 4.
1.  **Volume**: Too many to transcribe all.
2.  **Formats**: Chaotic mix (requires normalization).
3.  **Hardware**: Pi 4 cannot run real-time transcription for everything.

## Solution: "Tiered Transcription" Pipeline

### 1. The Gatekeeper (Format Normalization)
*   User uploads *any* format to `_Inbox_Sorting`.
*   System uses `ffmpeg` to standarize audio track:
    *   `16kHz Mono WAV` (Optimal for Whisper).
    *   Strips video track to save processing power.

### 2. The Filter (Smart Selection)
We classify files by **Duration** and **Location**:
*   **Tier 1 (Priority)**: Files in `09 Projekte` or `_Inbox`. Duration < 60 min. -> **Full Transcript**.
*   **Tier 2 (Metadata)**: Files > 60 min (likely Movies/Podcasts). -> **Generate Summary only** (first 5 min) OR Metadata only.
*   **Tier 3 (Ignored)**: Files in `12 Mediathek\Filme`. -> **Skip**.

### 3. The Worker
*   **Engine**: `whisper.cpp` (Quantized for Pi) or `faster-whisper`.
*   **Output**: Generates `filename.mp4.transcript.md` sidecar.
*   **Indexing**: Qdrant indexes the `.md` file, NOT the audio.

## Perplexity Integration
*   The "Search Tool" on the laptop reads these sidecar `.md` files.
*   User asks: "What did I say about the Telekom contract?" -> AI finds the transcript.
