# DB Parser Research (MDB/ACCDB/DBF/SQLite)

## Top Parser Candidates

### MDB/ACCDB
- **mdbtools**: CLI suite (`mdb-tables`, `mdb-schema`, `mdb-export`) for schema/row extraction.
- **Jackcess (Java)**: Strong Microsoft Access support; more advanced than mdbtools for complex Access features.
- **UCanAccess (Java)**: JDBC driver that wraps Jackcess for SQL access.

### DBF
- **dbfread (Python)**: Lightweight reader for DBF tables.
- **dbf (Python)**: Full DBF read/write implementation (useful for test fixtures).

### SQLite
- **sqlite3 (built-in)**: Standard Python module; reliable schema + data reads.
- **SQLite CLI**: Alternative for bulk export when embedding Python is not desired.

## Benchmark Notes
- **mdbtools**: Best open-source CLI for quick schema/CSV export; performance depends on Access file size.
- **Jackcess/UCanAccess**: More complete Access compatibility; best for complex schemas but heavier (JVM).
- **dbfread**: Fast enough for lightweight tables; use read-only mode for memory savings.
- **sqlite3**: Embedded engine; fast for schema + row counts with indexes.

## Service Implementation Notes
- Container uses `mdbtools` binaries for MDB/ACCDB and `dbfread` for DBF.
- SQLite uses the built-in `sqlite3` module for schema + export.
