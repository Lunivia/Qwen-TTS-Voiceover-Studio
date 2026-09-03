"""Remove only Voice Studio records created by the automated QA smoke test."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from studio.config import DATA_DIR, PROJECT_DIR, TEMP_DIR, VOICE_DIR
from studio.database import Database


def remove_inside_data(path: Path) -> None:
    resolved = path.resolve()
    resolved.relative_to(DATA_DIR.resolve())
    if resolved.exists():
        shutil.rmtree(resolved)


def main() -> None:
    database = Database()
    projects = database.fetch_all("SELECT id,name FROM projects WHERE name LIKE '系统验收-%'")
    for project in projects:
        voices = database.fetch_all("SELECT id FROM voices WHERE project_id=?", (project["id"],))
        database.execute("DELETE FROM projects WHERE id=?", (project["id"],))
        for voice in voices:
            database.execute("DELETE FROM voices WHERE id=?", (voice["id"],))
            remove_inside_data(VOICE_DIR / voice["id"])
        remove_inside_data(PROJECT_DIR / project["id"])
        print(f"Removed QA project: {project['name']}")
    remove_inside_data(TEMP_DIR / "selftest")


if __name__ == "__main__":
    main()
