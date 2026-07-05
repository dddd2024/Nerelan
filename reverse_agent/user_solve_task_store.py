from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .user_solve_task_lifecycle import validate_task_payload


DEMO_TASK_ID_RE = re.compile(r"^demo_[a-z0-9_]+$")


def validate_demo_task_id(task_id: str) -> str:
    text = str(task_id or "").strip()
    if not DEMO_TASK_ID_RE.fullmatch(text):
        raise ValueError("task_id must match demo_[a-z0-9_]+")
    return text


def demo_task_path(state_dir: str | Path, task_id: str) -> Path:
    safe_id = validate_demo_task_id(task_id)
    root = Path(state_dir)
    return root / "solve_tasks" / f"{safe_id}.json"


def validate_demo_task_path(state_dir: str | Path, path: str | Path) -> Path:
    root = (Path(state_dir) / "solve_tasks").resolve()
    candidate = Path(path)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (Path(state_dir).parent / candidate).resolve()
    if root not in resolved.parents:
        raise ValueError("task path must stay under project_state/solve_tasks")
    if not resolved.name.startswith("demo_") or resolved.suffix != ".json":
        raise ValueError("task path must be project_state/solve_tasks/demo_*.json")
    validate_demo_task_id(resolved.stem)
    return resolved


def write_demo_task(state_dir: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_task_payload(payload)
    if result["validation_status"] != "PASSED":
        raise ValueError("; ".join(result["errors"]))
    path = demo_task_path(state_dir, result["task_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "schema_version": 1,
        "write_status": "PASSED",
        "path": _project_path(path),
        "task_id": result["task_id"],
        "arbitrary_persistence": False,
    }


def read_demo_task(state_dir: str | Path, task_id: str) -> dict[str, Any]:
    path = demo_task_path(state_dir, task_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("task payload must be an object")
    result = validate_task_payload(payload)
    if result["validation_status"] != "PASSED":
        raise ValueError("; ".join(result["errors"]))
    return payload


def list_demo_tasks(state_dir: str | Path) -> list[dict[str, Any]]:
    root = Path(state_dir) / "solve_tasks"
    if not root.exists():
        return []
    tasks = []
    for path in sorted(root.glob("demo_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            validation = validate_task_payload(payload)
            tasks.append({
                "path": _project_path(path),
                "task_id": str(payload.get("task_id") or ""),
                "status": str(payload.get("status") or ""),
                "validation_status": validation["validation_status"],
                "errors": validation["errors"],
            })
    return tasks


def _project_path(path: Path) -> str:
    text = str(path).replace("\\", "/")
    marker = "project_state/"
    idx = text.find(marker)
    return text[idx:] if idx >= 0 else text
