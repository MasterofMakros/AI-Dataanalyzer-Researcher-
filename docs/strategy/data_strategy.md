# Data Strategy: The 7.1TB Legacy Deep Dive

> **Core Philosophy:** "Zero-Copy & Energy Efficiency". We do not duplicate 7TB of data. We bring the compute to the data, employing the most efficient algorithms (Rust-based) and hardware accelerators (Ryzen NPU) to minimize energy/IO footprint.

## 1. The Challenge (Audit Results)
*   **Total Volume:** 7.1 TB / 1.1M Files.
*   **Critical Clusters:**
    *   📂 **Archives:** 3.3 TB (.rar/.7z) - "The Black Box".
    *   📂 **Video:** 1.6 TB (.mkv/.mp4) - High redundancy suspected.
    *   📂 **Communication:** 65k Files (.eml) - Unstructured knowledge.
    *   📂 **Web Knowledge:** 166k Files (.html) - Scraping scraps.

---

## 2. High-Efficiency Processing Pipeline (Local & Green)

### A. Archives (3.3 TB) -> Strategy: "Virtual Mounting"
*   **Problem:** Decompressing 3.3TB requires ~7TB temp space and massive CPU/IO energy.
*   **Expert Solution:** **Ratarmount** (Python/FUSE).
    *   *Mechanism:* Mounts RAR/7z archives as a read-only Virtual Filesystem.
    *   *Efficiency:* **Zero-Copy**. Data is read on-demand. No extraction phase.
    *   *Energy:* 100% savings on extraction writing energy.
    *   *Status:* Use this to index content without exploding storage.

### B. Video Deduplication (1.6 TB) -> Strategy: "Perceptual Pruning"
*   **Problem:** Finding exact and visual duplicates in 4K video consumes massive compute for decoding.
*   **Expert Solution:** **Czkawka** (Rust) + **FFmpeg** (Hardware Accel).
    *   *Mechanism:* Czkawka uses fast hashing for exact dupes. For visual dupes, we generate low-res keyframes (1 per minute) using FFmpeg via **Ryzen Video Engine (VCN)**.
    *   *Efficiency:* Offloading decoding to VCN (ASIC) is ~10x more energy efficient than CPU decoding.
    *   *Action:* Delete identified visual duplicates (keep highest bitrate).

### C. Communication (65k EMLs) -> Strategy: "Vector-Lite Search"
*   **Problem:** Indexing 65k unstructured texts requires fast ingest and low-latency search.
*   **Expert Solution:** **Qdrant** (Rust).
    *   *Mechanism:* A specialized search engine optimized for speed and typo-tolerance.
    *   *Efficiency:* Rust backend ensures minimal RAM footprint compared to Java-based Elasticsearch.
    *   *Action:* Parse EMLs to JSONL -> Ingest to Qdrant running on Mini-PC.

---

## 3. Hardware Alignment (Ryzen AI 9 HX 370)

| Task | Hardware Unit | Usage Strategy |
| :--- | :--- | :--- |
| **Indexing / Embedding** | **NPU (XDNA 2)** | Offload embedding generation (Llama/BERT) to NPU. Saves CPU for OS. |
| **Video Decoding** | **iGPU (Radeon 890M)** | Use VCN (Video Core Next) for thumb/keyframe generation. |
| **Database I/O** | **NVMe (PCIe 5.0)** | High-IOPS random read for Qdrant/Qdrant lookups. |
| **Cold Storage** | **HDD (SATA)** | Spin down when not in active ingest to save energy. |

---

## 4. Execution Roadmap (The Cleanup)

1.  **Phase 1: The Purge (Video)**
    *   Run `Czkawka` on `F:\` to identifying exact duplicates.
    *   Run `Visual-Dedup-Script` (FFmpeg) on pure video folders.
    *   *Goal:* Recover ~300-500 GB space.

2.  **Phase 2: The Map (Archives)**
    *   Install `ratarmount`.
    *   Mount the 3.3TB RARs to `Z:\Virtual_Archives`.
    *   Run Indexing Script on `Z:\`.

3.  **Phase 3: The Brain (Text/Web)**
    *   Ingest 65k EMLs into Qdrant.
    *   Filter 166k HTMLs (remove boilerplates) -> Qdrant (Low Priority).
