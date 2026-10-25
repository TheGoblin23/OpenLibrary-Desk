import sqlite3
from pathlib import Path

DEFAULT_PATH = Path.home() / ".openlibrary-desk" / "library.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS materials(
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL, author TEXT DEFAULT '', description TEXT DEFAULT '',
  file_path TEXT UNIQUE, format TEXT DEFAULT '', material_type TEXT DEFAULT 'Documento',
  reading_status TEXT DEFAULT 'Pendiente', progress INTEGER DEFAULT 0,
  added_at TEXT, last_opened_at TEXT, favorite INTEGER DEFAULT 0,
  file_hash TEXT, category TEXT DEFAULT '', tags TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_title ON materials(title);
CREATE INDEX IF NOT EXISTS ix_author ON materials(author);
CREATE INDEX IF NOT EXISTS ix_format ON materials(format);
CREATE INDEX IF NOT EXISTS ix_hash ON materials(file_hash);
"""

def connect(path=DEFAULT_PATH):
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con
