# Conductor (AI-Dataanalyzer-Researcher) - North Star PRD

**Version:** 1.0 (Derived from Vision)
**Status:** Active

## 1. Product Vision
To build a fully local, privacy-first "Internal Google" for 10TB+ of personal life data (documents, photos, videos, communications). It MUST run on consumer hardware (NVIDIA GPU) and provide sub-3-second retrieval times.

## 2. Core User Scenarios
1.  **"Where is that invoice?"** User types "Invoice for roof repair 2023" -> System returns the PDF, highlights the total, and shows the specific paragraph.
2.  **"What did we discuss?"** User types "Meeting about solar panels" -> System returns audio transcript snippets and meeting notes.
3.  **"Show me the video."** User types "Drone footage of vacation" -> System plays video starting at the relevant timestamp using `LocalMediaPreview`.

## 3. Scope & Constraints
-   **Local Only:** No Cloud APIs (except optional/approved ones).
-   **Privacy:** No data leaves the machine.
-   **Hardware:** Optimized for Single GPU (RTX 3090/4090) + CPU fallback.
-   **Stack:** Docker Compose (Microservices).
