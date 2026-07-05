"""State hygiene planning helpers.

This module is intentionally a thin facade over the non-destructive state
governance builders.  It does not implement cleanup-apply.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .state_governance import build_cleanup_plan, build_retention_policy


def build_state_hygiene_retention_bundle(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    policy = build_retention_policy(state_dir=state_dir, write_result=write_result)
    cleanup_plan, cleanup_summary = build_cleanup_plan(state_dir=state_dir, write_result=write_result)
    return {
        "retention_policy": policy,
        "cleanup_plan": cleanup_plan,
        "cleanup_plan_summary": cleanup_summary,
        "cleanup_apply_allowed": False,
        "destructive_operation_performed": False,
    }
