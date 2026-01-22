from __future__ import annotations

from pathlib import Path

from app.db.sqlite import get_connection


def migrate(db_path: Path) -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    conn = get_connection(db_path)
    with conn:
        conn.executescript(schema_sql)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);"
        )
        cur = conn.execute("SELECT COUNT(*) AS c FROM schema_version")
        count = cur.fetchone()["c"]
        if count == 0:
            conn.execute("INSERT INTO schema_version (version) VALUES (1)")
    conn.close()
