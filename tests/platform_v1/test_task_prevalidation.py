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


def test_goal_service_launch_runs_prevalidation_and_blocks_before_routing(tmp_path: Path) -> None:
    from datetime import datetime, timedelta, timezone
    from reverse_agent.platform_v1.autonomy import AutonomyService, KNOWN_OPERATIONS
    from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
    from reverse_agent.platform_v1.control_store import PlatformControlStore
    from reverse_agent.platform_v1.goal_service import GoalService
    from reverse_agent.platform_v1.run_store import TaskStoreError

    store = TaskStore(tmp_path / "pv.sqlite3")
    control = PlatformControlStore(store)
    aut = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    now = datetime.now(timezone.utc)
    win = aut.activate({
        "policy_id": "pv-policy", "policy_revision": 1, "owner_identity": "o",
        "starts_at": (now - timedelta(seconds=5)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/Nerelan"], "capabilities": sorted(KNOWN_OPERATIONS),
        "confirmation": "ACTIVATE",
    })
    gs = GoalService(
        store=store, control_store=control,
        roster_resolver=lambda _r: (_ for _ in ()).throw(AssertionError("should prevalidate before routing")),
    )
    goal = gs.create({
        "title": "Valid title", "objective": "Bad", "repository": "dddd2024/Nerelan",
        "executor_kind": "opencode", "orchestration_mode": "single", "idempotency_key": "pv-1",
    })
    gs.plan(goal.id, expected_revision=1, tasks=[{"id": "A", "title": "Fix", "instruction": "Fix"}])
    gs.approve(goal.id, expected_revision=1)
    import pytest
    with pytest.raises(TaskStoreError, match="pre_validation_failed:empty_or_trivial_objective"):
        gs.launch(goal.id, expected_revision=1, window_id=win.id)
    store._conn.close()
