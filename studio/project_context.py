from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The single project identity shared by every workbench surface."""

    current_project_id: str
    name: str
    status: str

