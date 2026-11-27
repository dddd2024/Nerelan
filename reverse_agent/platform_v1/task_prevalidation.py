"""Deterministic zero-LLM pre-dispatch validation for admitted tasks."""
from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence


def prevalidate_task(
    task: Mapping[str, Any] | Any,
    *,
    repo_dir: Path | str | None = None,
    base_ref: str = "",
    required_paths: Sequence[str] = (),
    max_context_tokens: int | None = None,
) -> dict[str, Any]:
    """Validate task metadata and workspace prerequisites before spending any LLM call.

    Returns ``{"ok": bool, "reasons": list[str], "classification": str}``.
    When ``ok`` is False, callers block with ``"pre_validation_failed"`` so real
    settlement records zero model spend cleanly.
    """
    reasons: list[str] = []

    def _get(field: str, default: Any = None) -> Any:
        if isinstance(task, Mapping):
            return task.get(field, default)
        return getattr(task, field, default)

    title = str(_get("title") or _get("objective") or "").strip()
    if len(title) < 4:
        reasons.append("empty_or_trivial_objective")

    repository = str(_get("repository") or "").strip()
    if not repository or ("/" not in repository and not Path(repository).exists()):
        reasons.append("invalid_repository")

    context_need = _get("context_need")
    if (
        isinstance(context_need, int)
        and isinstance(max_context_tokens, int)
        and max_context_tokens > 0
        and context_need > int(max_context_tokens * 0.7)
    ):
        reasons.append("context_budget_exceeded")

    if repo_dir is not None:
        root = Path(repo_dir)
        if not root.exists() or not root.is_dir():
            reasons.append("repo_dir_missing")
        else:
            if base_ref and (root / ".git").exists():
                proc = subprocess.run(
                    ["git", "-C", str(root), "rev-parse", "--verify", f"{base_ref}^{{commit}}"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode != 0:
                    reasons.append("invalid_base_ref")
            root_resolved = root.resolve()
            for rel in required_paths:
                if not isinstance(rel, str) or not rel.strip():
                    reasons.append("invalid_required_path")
                    continue
                target = (root_resolved / rel.strip()).resolve()
                try:
                    target.relative_to(root_resolved)
                except ValueError:
                    reasons.append(f"path_escapes_repo:{rel}")
                    continue
                if not target.exists():
                    reasons.append(f"missing_required_path:{rel}")

    return {
        "ok": not reasons,
        "reasons": reasons,
        "classification": "pre_validation_failed" if reasons else "",
    }
