
import os
from pathlib import Path

# Base Directory: Can be set via env var, defaults to F:/conductor for Windows
# For Linux: /opt/conductor
BASE_DIR = Path(os.getenv("CONDUCTOR_ROOT", "F:/conductor"))

# Core Paths
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
SCRIPTS_DIR = BASE_DIR / "scripts"

# Data Storage
INBOX_DIR = Path(os.getenv("CONDUCTOR_INBOX", "F:/_Inbox"))
QUARANTINE_DIR = Path(os.getenv("CONDUCTOR_QUARANTINE", "F:/_Quarantine"))
ARCHIVE_DIR = Path(os.getenv("CONDUCTOR_ARCHIVE", "F:/_Archiv"))
TEST_POOL_DIR = Path(os.getenv("CONDUCTOR_TESTPOOL", "F:/_TestPool"))
TEST_SUITE_DIR = Path(os.getenv("CONDUCTOR_TESTSUITE", "F:/_TestSuite"))

# Ledger
LEDGER_DB_PATH = DATA_DIR / "shadow_ledger.db"

# URLs (Service endpoints)
TIKA_URL = os.getenv("TIKA_URL", "http://localhost:9998/tika")
MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6335")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11435")
NEURAL_WORKER_URL = os.getenv("NEURAL_WORKER_URL", "http://localhost:8005")

# Ensure core dirs exist
for p in [BASE_DIR, CONFIG_DIR, DATA_DIR, DOCS_DIR, SCRIPTS_DIR]:
    p.mkdir(parents=True, exist_ok=True)
