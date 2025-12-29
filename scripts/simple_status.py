import sqlite3
from config.paths import LEDGER_DB_PATH

conn = sqlite3.connect(LEDGER_DB_PATH)
res = conn.execute("SELECT COUNT(*) FROM files WHERE status='indexed_pilot'").fetchone()
total = res[0]
res2 = conn.execute("SELECT COUNT(*) FROM files WHERE status='indexed_pilot' AND embedding_status='DONE'").fetchone()
done = res2[0]
print(f"PILOT_PROGRESS:{done}/{total}")
conn.close()
