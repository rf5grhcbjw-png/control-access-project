import sqlite3
from pathlib import Path

BLOCKS = ['A', 'B', 'C', 'D', 'E']
DB_PATH = Path(__file__).parent / 'control_access.db'


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS residents (
                username     TEXT PRIMARY KEY,
                password     TEXT NOT NULL,
                block        TEXT NOT NULL,
                biometric_id TEXT,
                reg_code     TEXT UNIQUE NOT NULL,
                created_at   TEXT DEFAULT (datetime('now', 'localtime'))
            );
            CREATE TABLE IF NOT EXISTS visitors (
                username         TEXT PRIMARY KEY,
                block            TEXT NOT NULL,
                host             TEXT NOT NULL,
                reason           TEXT,
                temporary_access TEXT NOT NULL DEFAULT 'active',
                created_at       TEXT DEFAULT (datetime('now', 'localtime'))
            );
            CREATE TABLE IF NOT EXISTS access_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT NOT NULL,
                granted   INTEGER NOT NULL,
                method    TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now', 'localtime'))
            );
        """)
        # Seed initial data if tables are empty
        if not conn.execute("SELECT 1 FROM residents").fetchone():
            conn.execute(
                "INSERT INTO residents (username, password, block, biometric_id, reg_code) VALUES (?, ?, ?, ?, ?)",
                ('cleiton', 'python123', 'A', 'BIO_001', 'A-0001')
            )
        if not conn.execute("SELECT 1 FROM visitors").fetchone():
            conn.execute(
                "INSERT INTO visitors (username, block, host, reason) VALUES (?, ?, ?, ?)",
                ('visitor_1', 'A', 'cleiton', 'visit')
            )


def next_reg_code(block: str) -> str:
    """Returns the next sequential registration code for a block, e.g. B-0003."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(CAST(SUBSTR(reg_code, 3) AS INTEGER)) AS max_num FROM residents WHERE block = ?",
            (block,)
        ).fetchone()
    number = (row['max_num'] or 0) + 1
    return f"{block}-{number:04d}"


init_db()
