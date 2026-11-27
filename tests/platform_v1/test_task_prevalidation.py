"""Provider-free tests for deterministic zero-LLM task pre-validation."""
from __future__ import annotations

from pathlib import Path
import subprocess
from types import SimpleNamespace

from reverse_agent.platform_v1.real_settlement import PRE_DISPATCH_ZERO_CLASSES, is_confirmed_pre_dispatch_zero
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_prevalidation import prevalidate_task


def test_prevalidate_task_catches_invalid_inputs_and_missing_paths(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.invalid"], cwd=repo, check=True)
    (repo / "app.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()

    bad = prevalidate_task(
        {"title": "  ", "repository": "badrepo", "context_need": 90_000},
        repo_dir=repo,
        base_ref="0" * 40,
        required_paths=["missing.py", "../outside.py"],
        max_context_tokens=100_000,
    )
    assert bad["ok"] is False
    assert bad["classification"] == "pre_validation_failed"
    assert {"empty_or_trivial_objective", "invalid_repository", "context_budget_exceeded", "invalid_base_ref"}.issubset(
        set(bad["reasons"])
    )
    assert any(r.startswith("missing_required_path:") for r in bad["reasons"])
    assert any(r.startswith("path_escapes_repo:") for r in bad["reasons"])

    good = prevalidate_task(
        {"title": "Fix bug in app.py", "repository": "dddd2024/Nerelan", "context_need": 20_000},
        repo_dir=repo,
        base_ref=head,
        required_paths=["app.py"],
        max_context_tokens=100_000,
    )
    assert good == {"ok": True, "reasons": [], "classification": ""}


def test_pre_validation_failed_class_settles_at_zero_cost() -> None:
    assert "pre_validation_failed" in PRE_DISPATCH_ZERO_CLASSES
    store = TaskStore(":memory:")
    task = store.create_task(title="Bad task", repository="dddd2024/Nerelan")
    assert is_confirmed_pre_dispatch_zero(
        store._conn,
        task.id,
        {"failure_classification": "pre_validation_failed", "failure_detail": "missing_required_path"},
    ) is True
    store._conn.close()
