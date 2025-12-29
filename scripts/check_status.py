import sqlite3
import pandas as pd
from tabulate import tabulate

from config.paths import LEDGER_DB_PATH

conn = sqlite3.connect(LEDGER_DB_PATH)
df = pd.read_sql_query("SELECT status, embedding_status, COUNT(*) as count FROM files GROUP BY status, embedding_status", conn)
print(tabulate(df, headers='keys', tablefmt='psql'))
conn.close()
