from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError


def _payload(**overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "policy_id": "policy-1", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=2)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task", "open_draft_pr"],
        "max_concurrent_tasks": 2, "max_tasks": 8, "max_retries": 1,
        "confirmation": "ACTIVATE",
    }
    payload.update(overrides)
    return payload


def test_window_requires_owner_confirmation_and_bounded_policy():
    control = PlatformControlStore(TaskStore(":memory:"))
    service = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    with pytest.raises(TaskStoreError, match="confirmation"):
        service.activate(_payload(confirmation=""))
    with pytest.raises(TaskStoreError, match="duration"):
        service.activate(_payload(expires_at=(datetime.now(timezone.utc) + timedelta(days=8)).isoformat()))
    active = service.activate(_payload())
    assert active.status == "ACTIVE"
    assert service.status()["autonomy_enabled"] is True


def test_policy_evaluation_is_server_side_and_receipted():
    control = PlatformControlStore(TaskStore(":memory:"))
    service = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = service.activate(_payload())
    assert service.authorize(
        window_id=window.id, operation="execute_task", repository="dddd2024/reverse-agent",
        subject_id="task-1", input_payload={"task_id": "task-1"},
    )
    assert not service.authorize(
        window_id=window.id, operation="execute_task", repository="elsewhere/repo",
        subject_id="task-2", input_payload={"task_id": "task-2"},
    )
    summary = service.summary(window.id)
    assert summary["operations"] == {"allowed": 1, "denied": 1, "total": 2}
    assert all(receipt["input_digest"] and "task_id" not in receipt for receipt in summary["receipts"])


def test_operation_receipt_persists_bounded_nonsecret_identity_snapshot():
    control = PlatformControlStore(TaskStore(":memory:"))
    service = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = service.activate(_payload())
    receipt = control.append_receipt(
        window_id=window.id,
        operation_type="resume_write_gate",
        capability="execute_task",
        repository="dddd2024/reverse-agent",
        subject_id="task-identity",
        decision="allowed",
        reason="identity_checked",
        input_payload={"task_id": "task-identity"},
        identities={
            "execution_authority_sha": "a" * 64,
            "planning_sha": "b" * 64,
            "claim_epoch": 7,
        },
    )
    assert receipt.identities == {
        "execution_authority_sha": "a" * 64,
        "planning_sha": "b" * 64,
        "claim_epoch": "7",
    }
    summary = service.summary(window.id)
    assert summary["receipts"][0]["identities"]["planning_sha"] == "b" * 64

    with pytest.raises(TaskStoreError, match="sensitive_control_field_rejected"):
        control.append_receipt(
            window_id=window.id,
            operation_type="resume_write_gate",
            capability="execute_task",
            repository="dddd2024/reverse-agent",
            subject_id="task-secret",
            decision="denied",
            reason="reject secret shaped identity",
            input_payload={"task_id": "task-secret"},
            identities={"api_token": "must-not-persist"},
        )


def _identity_bound_resume_setup(*, plan_for_run: str, blank_reservation: bool = False):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    service = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = service.activate(_payload(
        policy_id=f"identity-{plan_for_run}-{blank_reservation}",
        capabilities=["execute_task", "resume_task"],
        max_token_units=1000,
        per_task_token_reservation=400,
        provider_quota_state="OBSERVED",
    ))
    task = store.create_task(
        title="identity-bound-resume",
        repository="dddd2024/reverse-agent",
        executor_kind="opencode",
        orchestration_mode="single",
    )
    first_epoch, _ = control.claim_task(
        window_id=window.id,
        task_id=task.id,
        owner="old-owner",
        lease_ms=60_000,
        execution_authority_sha="auth-A",
        planning_sha="plan-A",
    )
    control._conn.execute(
        "UPDATE platform_coordinator_claims SET expires_at_ms = 0 WHERE task_id = ?",
        (task.id,),
    )
    store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="expired-durable-owner",
        execution_authority_sha="auth-A",
        planning_sha=plan_for_run,
    )
    store.set_state(task.id, "INTERRUPTED")
    if blank_reservation:
        control._conn.execute(
            "UPDATE platform_coordinator_claims SET execution_authority_sha = '', "
            "planning_sha = '' WHERE task_id = ?",
            (task.id,),
        )
        control._conn.execute(
            "UPDATE platform_budget_reservations SET execution_authority_sha = '', "
            "planning_sha = '' WHERE task_id = ? AND state = 'ACTIVE'",
            (task.id,),
        )
    return store, control, window, task, first_epoch


def test_resume_budget_claim_planning_mismatch_fails_before_mutation_and_is_receipted():
    store, control, window, task, first_epoch = _identity_bound_resume_setup(
        plan_for_run="plan-B"
    )
    before = control.get_window(window.id)
    with pytest.raises(TaskStoreError, match="budget_claim_planning_identity_mismatch"):
        control.claim_task(
            window_id=window.id,
            task_id=task.id,
            owner="new-owner",
            lease_ms=60_000,
            execution_authority_sha="auth-A",
            planning_sha="plan-B",
        )

    claim = control._conn.execute(
        "SELECT owner, epoch FROM platform_coordinator_claims WHERE task_id = ?",
        (task.id,),
    ).fetchone()
    reservation = control._conn.execute(
        "SELECT claim_epoch, planning_sha FROM platform_budget_reservations "
        "WHERE task_id = ? AND state = 'ACTIVE'",
        (task.id,),
    ).fetchone()
    after = control.get_window(window.id)
    assert dict(claim) == {"owner": "old-owner", "epoch": first_epoch}
    assert dict(reservation) == {
        "claim_epoch": first_epoch,
        "planning_sha": "plan-A",
    }
    assert after.retries_used == before.retries_used

    receipt = control.list_receipts(window_id=window.id, limit=1)[0]
    assert receipt.operation_type == "resume_write_gate"
    assert receipt.decision == "denied"
    assert receipt.reason == "budget_claim_planning_identity_mismatch"
    assert receipt.identities["current_planning_sha"] == "plan-B"
    assert receipt.identities["durable_planning_sha"] == "plan-B"
    assert receipt.identities["reservation_planning_sha"] == "plan-A"


def test_legacy_unbound_resume_reservation_is_atomically_bound_when_run_matches():
    _, control, window, task, first_epoch = _identity_bound_resume_setup(
        plan_for_run="plan-A", blank_reservation=True
    )
    epoch, _ = control.claim_task(
        window_id=window.id,
        task_id=task.id,
        owner="new-owner",
        lease_ms=60_000,
        execution_authority_sha="auth-A",
        planning_sha="plan-A",
    )
    assert epoch == first_epoch + 1
    reservation = control._conn.execute(
        "SELECT claim_epoch, execution_authority_sha, planning_sha "
        "FROM platform_budget_reservations WHERE task_id = ? AND state = 'ACTIVE'",
        (task.id,),
    ).fetchone()
    assert dict(reservation) == {
        "claim_epoch": epoch,
        "execution_authority_sha": "auth-A",
        "planning_sha": "plan-A",
    }
    receipt = control.list_receipts(window_id=window.id, limit=1)[0]
    assert receipt.decision == "allowed"
    assert receipt.reason == "resume_claim_legacy_identity_bound"
    assert receipt.identities["legacy_reservation_identity_bound"] == "true"


def test_usage_budget_policy_is_explicit_and_hard_admission_is_reported():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    service = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = service.activate(_payload(
        max_token_units=1000,
        per_task_token_reservation=400,
        max_cost_micro_units=500000,
        per_task_cost_reservation=200000,
        provider_quota_state="OBSERVED",
        adjacent_secret="SECRET-SENTINEL-NEVER-PERSIST",
    ))
    summary = service.summary(window.id)
    assert summary["budget"]["enforcement_class"] == "HARD_ADMISSION_ENFORCED"
    assert summary["budget"]["remaining_token_units"] == 1000
    assert summary["budget"]["remaining_cost_micro_units"] == 500000
    assert summary["budget"]["provider_quota_state"] == "OBSERVED"
    persisted = " ".join(
        str(tuple(row))
        for row in store._conn.execute("SELECT * FROM platform_autonomous_windows")
    )
    assert "SECRET-SENTINEL-NEVER-PERSIST" not in persisted
    with pytest.raises(TaskStoreError, match="invalid_autonomy_budget"):
        AutonomyService(
            control_store=PlatformControlStore(TaskStore(":memory:")),
            capabilities=CapabilityRegistry(),
        ).activate(_payload(policy_id="policy-bool", max_token_units=True))
    with pytest.raises(TaskStoreError, match="invalid_autonomy_budget_pair"):
        AutonomyService(
            control_store=PlatformControlStore(TaskStore(":memory:")),
            capabilities=CapabilityRegistry(),
        ).activate(_payload(
            policy_id="policy-unpaired",
            max_token_units=100,
            per_task_token_reservation=0,
        ))


def test_legacy_window_schema_migrates_in_place_and_replay_is_noop(tmp_path):
    store = TaskStore(str(tmp_path / "legacy.sqlite3"))
    store._conn.executescript(
        """
        CREATE TABLE platform_autonomous_windows (
            id TEXT PRIMARY KEY,
            policy_id TEXT NOT NULL,
            policy_revision INTEGER NOT NULL,
            policy_digest TEXT NOT NULL,
            owner_identity TEXT NOT NULL,
            confirmation TEXT NOT NULL,
            starts_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            status TEXT NOT NULL,
            repositories_json TEXT NOT NULL,
            capabilities_json TEXT NOT NULL,
            max_concurrent_tasks INTEGER NOT NULL,
            max_tasks INTEGER NOT NULL,
            max_retries INTEGER NOT NULL,
            tasks_started INTEGER NOT NULL DEFAULT 0,
            tasks_completed INTEGER NOT NULL DEFAULT 0,
            retries_used INTEGER NOT NULL DEFAULT 0,
            stop_reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(policy_id, policy_revision)
        );
        """
    )
    now = datetime.now(timezone.utc).isoformat()
    store._conn.execute(
        "INSERT INTO platform_autonomous_windows VALUES "
        "('legacy-window', 'legacy-policy', 1, 'digest', 'owner', 'ACTIVATE', ?, ?, "
        "'STOPPED', '[\"dddd2024/reverse-agent\"]', '[\"execute_task\"]', "
        "1, 2, 0, 1, 1, 0, 'owner_stopped', ?, ?)",
        (now, now, now, now),
    )
    control = PlatformControlStore(store)
    legacy = control.get_window("legacy-window")
    assert legacy.policy_id == "legacy-policy"
    assert legacy.enforcement_class == "POST_RUN_OBSERVED"
    assert legacy.max_token_units == 0
    changes = store._conn.total_changes
    PlatformControlStore(store)
    assert store._conn.total_changes == changes
    columns = {
        row["name"]
        for row in store._conn.execute("PRAGMA table_info(platform_autonomous_windows)")
    }
    assert {"max_token_units", "enforcement_class", "unknown_observation_count"} <= columns
    receipt_columns = {
        row["name"]
        for row in store._conn.execute("PRAGMA table_info(platform_operation_receipts)")
    }
    claim_columns = {
        row["name"]
        for row in store._conn.execute("PRAGMA table_info(platform_coordinator_claims)")
    }
    reservation_columns = {
        row["name"]
        for row in store._conn.execute("PRAGMA table_info(platform_budget_reservations)")
    }
    assert "identity_json" in receipt_columns
    assert {"execution_authority_sha", "planning_sha"} <= claim_columns
    assert {"execution_authority_sha", "planning_sha"} <= reservation_columns
