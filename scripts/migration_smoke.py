"""Non-destructive migration/idempotence check using an isolated temporary DB."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import studio.database as database_module
from studio.database import Database


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="qwentts-migration-") as raw:
        root = Path(raw)
        db_path = root / "data" / "app.db"
        db_path.parent.mkdir(parents=True)
        connection = sqlite3.connect(db_path)
        connection.execute("CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
        connection.execute("CREATE TABLE app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)")
        connection.execute("INSERT INTO projects VALUES ('legacy', 'Legacy', 'draft', '2026-01-01', '2026-01-01')")
        connection.commit()
        connection.close()

        database_module.PROJECT_DIR = root / "data" / "projects"
        database_module.VOICE_DIR = root / "data" / "voices"
        database_module.PROJECT_DIR.mkdir(parents=True)
        database_module.VOICE_DIR.mkdir(parents=True)
        first = Database(db_path)
        assert first.get_setting("schema_version") == "1"
        assert first.fetch_one("SELECT name FROM projects WHERE id='legacy'")
        second = Database(db_path)
        assert second.get_setting("schema_version") == "1"
        assert second.fetch_one("SELECT name FROM projects WHERE id='legacy'")
        print("MIGRATION_SMOKE_OK")


if __name__ == "__main__":
    main()
