# Safe refactor notes

## Data safety

The application treats `data/` as production user data. When an existing
database has not yet recorded the current schema version, startup creates a
unique, non-overwriting snapshot under
`data/backups/pre-migration-YYYYMMDD-HHMMSS/` containing `app.db`, `projects/`,
and `voices/` before additive migration runs. Migration version `1` is stored
in `app_settings.schema_version` and is idempotent. Project deletion creates a
full `pre-delete-project-*` snapshot first; if that backup fails, deletion is
not attempted.

`QWEN_TTS_DATA_DIR` is an explicit opt-in storage location. Without it, an
existing repository-local `data/app.db` always wins, preventing an upgrade from
silently opening an empty database. No automatic data move or orphan cleanup is
performed.

## Project context

`studio.project_context.ProjectContext` is the canonical UUID-based context.
`StudioService.switch_project_context()` validates the UUID and persists
`last_project_id`. Project-table selection reads the persisted ID in the row,
not a dynamically sorted row index. Browser page load refreshes all project
dropdowns from SQLite so newly created projects remain visible.

## Verification

```powershell
$env:PYTHONPATH = (Get-Location).Path
.venv\Scripts\python.exe scripts\migration_smoke.py
.venv\Scripts\python.exe scripts\data_integrity_check.py
```

The integrity check is read-only: missing asset paths are reported and records
are never deleted.
