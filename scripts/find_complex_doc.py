import sqlite3
import pandas as pd

from config.paths import LEDGER_DB_PATH

conn = sqlite3.connect(str(LEDGER_DB_PATH))
query = """
    SELECT original_filename, original_path 
    FROM files 
    WHERE original_filename LIKE '%Tabelle%' 
       OR original_filename LIKE '%Bilanz%' 
       OR original_filename LIKE '%Rechnung%'
       OR original_filename LIKE '%Liste%'
    LIMIT 5
"""
try:
    df = pd.read_sql_query(query, conn)
    print(df.to_string())
except Exception as e:
    print(f"Error: {e}")
conn.close()
