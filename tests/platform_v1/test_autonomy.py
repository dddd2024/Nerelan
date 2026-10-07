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


def _canonical_checker_policy():
    now = datetime.now(timezone.utc)
    caps = {name: 0 for name in ("maxPrsOpened", "maxMergesToMain", "maxReleasesCreated", "maxDeploysToEnvironment")}
    return {
        "mode": "CONTROLLER_REVIEW", "repository": "dddd2024/Nerelan",
        "resourceAccess": {
            "filesystem": {"allowedPaths": ["input.txt"], "writablePaths": []},
            "network": {"allowedDomains": [], "allowWrite": False},
            "shell": {"allowedCommands": ["git_diff_check"], "deniedCommands": []},
            "secrets": {"access": "none", "allowedKeys": []},
            "workerApproval": {"required": False, "approvers": []},
        },
        "githubCapabilities": [], "publicationCapabilities": [],
        "publicationPolicy": {"allowedArtifactOrPackage": [], "allowedRegistry": [],
                              "allowedRepository": [], "allowedEnvironment": []},
        "mergePolicy": {"allowedRepositories": [], "allowedBaseBranches": [],
                        "requiredChecks": [], "allowedMergeMethods": [], "requireExactHead": True},
        "autonomousWindow": {"enabled": True, "startsAt": (now - timedelta(seconds=2)).isoformat(),
                             "expiresAt": (now + timedelta(hours=1)).isoformat(), **caps,
                             "stopConditions": [{"type": "window_expired", "scope": "window"}]},
        "budgets": dict(caps),
    }


def test_canonical_checker_policy_preserves_every_field_and_digest():
    from reverse_agent.platform_v1.autonomy import validate_canonical_policy, policy_digest
    policy = _canonical_checker_policy()
    parsed = validate_canonical_policy(policy)
    assert parsed == policy
    assert parsed is not policy
    assert policy_digest(parsed) == policy_digest(dict(reversed(list(policy.items()))))


@pytest.mark.parametrize("path", [(), ("resourceAccess",), ("resourceAccess", "shell"),
                                 ("autonomousWindow",), ("budgets",), ("mergePolicy",)])
def test_canonical_policy_rejects_unknown_nested_fields(path):
    from reverse_agent.platform_v1.autonomy import validate_canonical_policy
    policy = _canonical_checker_policy()
    node = policy
    for key in path:
        node = node[key]
    node["verified"] = True
    with pytest.raises(TaskStoreError, match="fields_invalid"):
        validate_canonical_policy(policy)


@pytest.mark.parametrize("path,value", [
    (("budgets", "maxPrsOpened"), True),
    (("budgets", "maxPrsOpened"), "0"),
    (("resourceAccess", "network", "allowWrite"), "false"),
    (("resourceAccess", "filesystem", "allowedPaths"), ["../outside.txt"]),
    (("resourceAccess", "filesystem", "allowedPaths"), ["src/**"]),
    (("resourceAccess", "filesystem", "writablePaths"), ["input.txt"]),
    (("resourceAccess", "shell", "allowedCommands"), ["git_diff_check; echo bad"]),
    (("resourceAccess", "secrets", "access"), "masked"),
    (("githubCapabilities",), ["merge_pr"]),
    (("publicationCapabilities",), ["deploy_production"]),
    (("autonomousWindow", "expiresAt"), "2020-01-01T00:00:00Z"),
    (("autonomousWindow", "startsAt"), "2026-10-07T10:00:00"),
])
def test_canonical_policy_rejects_widening_and_unavailable_adapters(path, value):
    from reverse_agent.platform_v1.autonomy import validate_canonical_policy
    policy = _canonical_checker_policy()
    node = policy
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    with pytest.raises(TaskStoreError):
        validate_canonical_policy(policy)


def test_production_policy_activation_rejects_legacy_renderer_owner():
    service = AutonomyService(control_store=PlatformControlStore(TaskStore(":memory:")),
                              capabilities=CapabilityRegistry())
    with pytest.raises(TaskStoreError, match="fields_invalid"):
        service.activate_policy(_payload())
    with pytest.raises(TaskStoreError, match="authority_unavailable"):
        service.activate_policy({"policy_id": "policy-1", "policy_revision": 1,
                                 "policy": _canonical_checker_policy()})


def _strict_checker_service(tmp_path):
    """Explicit provider-free fixture authority; not a live Owner observation."""
    from reverse_agent.platform_v1.autonomy import policy_digest
    from reverse_agent.platform_v1.authority_adapter import PolicyAuthority
    policy = _canonical_checker_policy()
    (tmp_path / "input.txt").write_text("original\n", encoding="utf-8")
    database = tmp_path / "tasks.sqlite3"
    control = PlatformControlStore(TaskStore(str(database)))
    binding = {
        "schema_version": 1, "confirmation_mode": "DELEGATED_CONTROLLER", "personally_human": False,
        "controller_identity": "fixture-controller", "upper_proposal_sha256": "a" * 64,
        "upper_expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "phase_ordinal": 6, "policy_id": "fixture-policy", "policy_revision": 1,
        "policy": policy, "policy_digest_sha256": policy_digest(policy),
        "window_id": "fixture-window", "delegation_slot_id": "fixture-slot", "slot_ordinal": 1,
        "max_real_window_activations": 1, "host_instance_id": "fixture-host", "runtime_instance_kind": "acceptance",
        "database_path": str(database), "workspace_path": str(tmp_path),
        "allowed_operations": ["validate_task"], "validation_command_ids": ["git_diff_check"],
        "validation_paths": ["input.txt"], "max_tasks": 1, "max_retries": 0, "max_concurrent_tasks": 1,
        "model_call_limit": 0, "provider_call_limit": 0, "github_write_limit": 0,
        "goal_idempotency_key": "fixture-goal", "plan_task_id": "CHECK001",
    }
    authority = PolicyAuthority("decision_fixture", "round_fixture", "b" * 64, "a" * 40,
                                "c" * 64, "dddd2024/Nerelan", "codex/fixture", "b" * 40, "c" * 40, binding)
    scope = {"capability": "validate_task", "validation_command_id": "git_diff_check",
             "allowed_paths": ["input.txt"], "workspace_path": str(tmp_path), "base_sha": "c" * 40,
             "goal_idempotency_key": "fixture-goal", "plan_task_id": "CHECK001"}
    service = AutonomyService(control_store=control, capabilities=CapabilityRegistry(),
                              authority_loader=lambda: authority, task_scope_resolver=lambda _id: scope)
    return service, authority, scope


def test_strict_policy_template_records_delegated_actor_without_human_claim(tmp_path):
    service, authority, _ = _strict_checker_service(tmp_path)
    result = service.policy_template()
    assert result["policy"] == authority.binding["policy"]
    assert result["confirmation_provenance"]["personally_human"] is False
    assert result["confirmation_provenance"]["controller_identity"] == "fixture-controller"
    assert result["supported_operations"] == ["validate_task"]
    assert result["task_budget"]["model_call_limit"] == 0


def test_strict_policy_confirmation_binds_exact_policy_and_rejects_revision_edits(tmp_path):
    import copy
    service, authority, _ = _strict_checker_service(tmp_path)
    policy = copy.deepcopy(authority.binding["policy"])
    policy["resourceAccess"]["filesystem"]["allowedPaths"] = ["different.txt"]
    with pytest.raises(TaskStoreError, match="exact_confirmation_mismatch"):
        service.activate_policy({"policy_id": "fixture-policy", "policy_revision": 1, "policy": policy})
    assert service.control_store.list_windows() == ()


def test_strict_task_scope_uses_server_resolver_and_rejects_command_and_workspace_drift(tmp_path):
    service, _, scope = _strict_checker_service(tmp_path)
    assert service.check_task_scope("task-1", "validate_task")["validation_command_id"] == "git_diff_check"
    scope["validation_command_id"] = "unapproved"
    with pytest.raises(TaskStoreError, match="scope_mismatch"):
        service.check_task_scope("task-1", "validate_task")
    scope["validation_command_id"] = "git_diff_check"
    scope["workspace_path"] = str(tmp_path.parent)
    with pytest.raises(TaskStoreError, match="workspace_mismatch"):
        service.check_task_scope("task-1", "validate_task")


def test_delegated_activation_persists_exact_policy_and_replay_preserves_spending(tmp_path):
    service, authority, _ = _strict_checker_service(tmp_path)
    payload = {"policy_id": "fixture-policy", "policy_revision": 1, "policy": authority.binding["policy"]}
    first = service.activate_policy(payload)
    binding = service.control_store.window_policy_binding(first.id)
    assert binding["canonical_policy"] == payload["policy"]
    assert first.canonical_policy_digest == authority.binding["policy_digest_sha256"]
    assert first.confirmation_mode == "DELEGATED_CONTROLLER"
    service.control_store._conn.execute("UPDATE platform_autonomous_windows SET tasks_started = 1 WHERE id = ?", (first.id,))
    replay = service.activate_policy(payload)
    assert replay.id == first.id and replay.tasks_started == 1
    reopened = PlatformControlStore(TaskStore(str(tmp_path / "tasks.sqlite3")))
    assert reopened.get_window(first.id).tasks_started == 1
    assert reopened.window_policy_binding(first.id) == binding


def test_receipt_summary_totals_full_window_and_snapshot_pages_more_than_1000(tmp_path):
    service, authority, _ = _strict_checker_service(tmp_path)
    window = service.activate_policy({"policy_id": "fixture-policy", "policy_revision": 1,
                                      "policy": authority.binding["policy"]})
    control = service.control_store
    for index in range(1101):
        control.append_receipt(window_id=window.id, operation_type="policy_evaluation", capability="validate_task",
                               repository="dddd2024/Nerelan", subject_id=str(index),
                               decision="allowed" if index % 2 else "denied", reason="fixture",
                               input_payload={"index": index})
    summary = service.summary(window.id)
    assert summary["operations"] == {"allowed": 550, "denied": 551, "total": 1101}
    assert len(summary["receipts"]) == 100
    first = control.list_receipts_page(window_id=window.id, limit=73)
    observed = [item.id for item in first["items"]]
    # A concurrent append does not shift the already frozen history snapshot.
    later = control.append_receipt(window_id=window.id, operation_type="policy_evaluation", capability="validate_task",
                                   repository="dddd2024/Nerelan", subject_id="later", decision="allowed",
                                   reason="fixture", input_payload={"index": 1102})
    cursor = first["next_cursor"]
    while cursor is not None:
        page = control.list_receipts_page(window_id=window.id, limit=73, cursor=cursor)
        observed.extend(item.id for item in page["items"])
        assert page["snapshot_seq"] == first["snapshot_seq"]
        cursor = page["next_cursor"]
    assert len(observed) == len(set(observed)) == 1101
    assert later.id not in observed
    reopened = PlatformControlStore(TaskStore(str(tmp_path / "tasks.sqlite3")))
    assert reopened.receipt_totals(window_id=window.id)["total"] == 1102
    with pytest.raises(TaskStoreError, match="cursor"):
        reopened.list_receipts_page(window_id="different-window", cursor=first["next_cursor"])


def test_receipt_insert_failure_blocks_window_without_resetting_allowance(tmp_path):
    service, authority, _ = _strict_checker_service(tmp_path)
    window = service.activate_policy({"policy_id": "fixture-policy", "policy_revision": 1,
                                      "policy": authority.binding["policy"]})
    control = service.control_store
    control._conn.execute("UPDATE platform_autonomous_windows SET tasks_started = 1 WHERE id = ?", (window.id,))
    control._conn.execute("CREATE TRIGGER fixture_receipt_failure BEFORE INSERT ON platform_operation_receipts "
                          "BEGIN SELECT RAISE(FAIL, 'fixture receipt insert failure'); END")
    with pytest.raises(TaskStoreError, match="receipt_persistence_failed"):
        control.append_receipt(window_id=window.id, operation_type="task_execution", capability="validate_task",
                               repository="dddd2024/Nerelan", subject_id="fixture-task", decision="allowed",
                               reason="fixture", input_payload={})
    assert control.get_window(window.id).status == "BLOCKED"
    assert control.get_window(window.id).tasks_started == 1


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
