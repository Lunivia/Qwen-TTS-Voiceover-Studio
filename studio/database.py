from __future__ import annotations

import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import DB_PATH


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS voice_requests (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            position INTEGER NOT NULL,
            name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            audition_text TEXT NOT NULL,
            language TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'candidate',
            voice_id TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(project_id, name)
        );

        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL REFERENCES voice_requests(id) ON DELETE CASCADE,
            seed INTEGER NOT NULL,
            wav_path TEXT NOT NULL,
            preview_path TEXT NOT NULL,
            selected INTEGER NOT NULL DEFAULT 0,
            shortlisted INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS voices (
            id TEXT PRIMARY KEY,
            project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            prompt TEXT,
            language TEXT NOT NULL,
            ref_text TEXT,
            reference_wav TEXT NOT NULL,
            preview_mp3 TEXT NOT NULL,
            prompt_path TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS batch_items (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            voice_id TEXT NOT NULL REFERENCES voices(id) ON DELETE RESTRICT,
            position INTEGER NOT NULL,
            text TEXT NOT NULL,
            language TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            output_wav TEXT,
            output_mp3 TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_candidates_request ON candidates(request_id);
        CREATE INDEX IF NOT EXISTS idx_voices_project ON voices(project_id);
        CREATE INDEX IF NOT EXISTS idx_batch_project_status ON batch_items(project_id, status);

        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id TEXT PRIMARY KEY,
            project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            action TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_activity_project ON activity_log(project_id, created_at DESC);
        """
        with self._lock, self.connection() as connection:
            connection.executescript(schema)
            request_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(voice_requests)").fetchall()
            }
            if "updated_at" not in request_columns:
                connection.execute("ALTER TABLE voice_requests ADD COLUMN updated_at TEXT")
                connection.execute("UPDATE voice_requests SET updated_at=created_at WHERE updated_at IS NULL")
            if "position" not in request_columns:
                connection.execute("ALTER TABLE voice_requests ADD COLUMN position INTEGER")
                connection.execute(
                    """
                    UPDATE voice_requests
                    SET position=(
                        SELECT COUNT(*) FROM voice_requests AS earlier
                        WHERE earlier.project_id=voice_requests.project_id
                          AND earlier.rowid<=voice_requests.rowid
                    )
                    WHERE position IS NULL
                    """
                )
            if "direct_output_mp3" not in request_columns:
                connection.execute("ALTER TABLE voice_requests ADD COLUMN direct_output_mp3 TEXT")
            if "direct_candidate_id" not in request_columns:
                connection.execute("ALTER TABLE voice_requests ADD COLUMN direct_candidate_id TEXT")
            candidate_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(candidates)").fetchall()
            }
            if "shortlisted" not in candidate_columns:
                connection.execute("ALTER TABLE candidates ADD COLUMN shortlisted INTEGER NOT NULL DEFAULT 0")
            connection.execute(
                "UPDATE batch_items SET status='pending', error='应用上次运行时中断，已自动恢复到等待状态' WHERE status='running'"
            )
        self.backup()

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> None:
        with self._lock, self.connection() as connection:
            connection.execute(sql, parameters)

    def executemany(self, sql: str, parameters: list[tuple[Any, ...]]) -> None:
        with self._lock, self.connection() as connection:
            connection.executemany(sql, parameters)

    def fetch_one(self, sql: str, parameters: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self._lock, self.connection() as connection:
            row = connection.execute(sql, parameters).fetchone()
        return dict(row) if row else None

    def fetch_all(self, sql: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._lock, self.connection() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self.fetch_one("SELECT value FROM app_settings WHERE key=?", (key,))
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.execute(
            """
            INSERT INTO app_settings(key,value,updated_at) VALUES(?,?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at
            """,
            (key, value, utc_now()),
        )

    def log_activity(
        self,
        project_id: str | None,
        entity_type: str,
        entity_id: str | None,
        action: str,
        detail: str = "",
    ) -> None:
        self.execute(
            "INSERT INTO activity_log(id,project_id,entity_type,entity_id,action,detail,created_at) VALUES(?,?,?,?,?,?,?)",
            (self.new_id(), project_id, entity_type, entity_id, action, detail, utc_now()),
        )

    def backup(self) -> Path:
        backup_dir = self.path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d")
        destination = backup_dir / f"app-{stamp}.db"
        with self._lock:
            source_connection = sqlite3.connect(self.path)
            backup_connection = sqlite3.connect(destination)
            try:
                source_connection.backup(backup_connection)
            finally:
                backup_connection.close()
                source_connection.close()
        backups = sorted(backup_dir.glob("app-*.db"), key=lambda item: item.name, reverse=True)
        for old_backup in backups[14:]:
            old_backup.unlink(missing_ok=True)
        return destination
