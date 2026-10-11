"""Real Git/SQLite/checker composition; authority loader is an explicit double."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import copy
import subprocess

import pytest

from reverse_agent.platform_v1.authority_adapter import PolicyAuthority
from reverse_agent.platform_v1.autonomy import AutonomyService, policy_digest
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorRouter, load_host_validation_contract
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator


def system(tmp_path, monkeypatch, *, count=2, reopen=False):
    root = tmp_path / "repository"
    database = tmp_path / "tasks.sqlite3"
    if not reopen:
        root.mkdir()
        subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
        for key, value in [("core.autocrlf", "false"), ("user.name", "Fixture"),
                           ("user.email", "fixture@example.invalid"),
                           ("remote.origin.url", "https://github.com/dddd2024/Nerelan.git")]:
            subprocess.run(["git", "-C", str(root), "config", key, value], check=True)
        (root / "input.txt").write_bytes(b"baseline\n")
        subprocess.run(["git", "-C", str(root), "add", "input.txt"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-m", "fixture"], check=True, capture_output=True)
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(root))
    store = TaskStore(str(database)); control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)
    if reopen:
        saved = control.window_policy_binding("admission-window")
        binding = saved["authority"]
        # The real loader reconstitutes exactly its binding, not runtime metadata.
        for key in ["decision_id", "round_id", "decision_content_sha256", "decision_commit_sha",
                    "command_plan_sha256", "head_sha", "base_sha", "branch"]:
            binding.pop(key)
    else:
        snapshots = []
        for index in range(count):
            goal = goals.create({"objective": "Check exact hygiene", "repository": "dddd2024/Nerelan",
                "idempotency_key": f"admission-goal-{index}", "executor_kind": "opencode", "orchestration_mode": "single"})
            goal = goals.plan(goal.id, expected_revision=goal.revision, tasks=[{
                "id": "CHECK001", "title": "Hygiene", "instruction": "Only fixed checker",
                "capability": "validate_task", "validation_command_id": "git_diff_check"}]).goal
            snapshots.append({"goal_id": goal.id, "revision": goal.revision,
                              "artifact_digest": goal.artifact_digest, "idempotency_key": goal.idempotency_key})
        now = datetime.now(timezone.utc)
        quotas = {key: 0 for key in ["maxPrsOpened", "maxMergesToMain", "maxReleasesCreated", "maxDeploysToEnvironment"]}
        policy = {"mode": "CONTROLLER_REVIEW", "repository": "dddd2024/Nerelan",
            "resourceAccess": {"filesystem": {"allowedPaths": ["input.txt"], "writablePaths": []},
                "network": {"allowedDomains": [], "allowWrite": False},
                "shell": {"allowedCommands": ["git_diff_check"], "deniedCommands": []},
                "secrets": {"access": "none", "allowedKeys": []}, "workerApproval": {"required": False, "approvers": []}},
            "githubCapabilities": [], "publicationCapabilities": [],
            "publicationPolicy": {"allowedArtifactOrPackage": [], "allowedRegistry": [], "allowedRepository": [], "allowedEnvironment": []},
            "mergePolicy": {"allowedRepositories": [], "allowedBaseBranches": [], "requiredChecks": [],
                            "allowedMergeMethods": [], "requireExactHead": True},
            "autonomousWindow": {"enabled": True, "startsAt": (now - timedelta(seconds=2)).isoformat(),
                "expiresAt": (now + timedelta(hours=1)).isoformat(), **quotas,
                "stopConditions": [{"type": "window_expired", "scope": "window"}]}, "budgets": quotas}
        binding = {"schema_version": 1, "confirmation_mode": "DELEGATED_CONTROLLER", "personally_human": False,
            "controller_identity": "fixture-controller", "upper_proposal_sha256": "a" * 64,
            "upper_expires_at": (now + timedelta(hours=2)).isoformat(), "phase_ordinal": 6,
            "policy_id": "admission-policy", "policy_revision": 1, "policy": policy, "policy_digest_sha256": policy_digest(policy),
            "window_id": "admission-window", "delegation_slot_id": "admission-slot", "slot_ordinal": 1,
            "max_real_window_activations": 1, "host_instance_id": "fixture-host", "runtime_instance_kind": "acceptance",
            "database_path": str(database), "workspace_path": str(root), "allowed_operations": ["approve_goal", "validate_task"],
            "validation_command_ids": ["git_diff_check"], "validation_paths": ["input.txt"], "max_tasks": count,
            "max_concurrent_tasks": 1, "max_retries": 0, "model_call_limit": 0, "provider_call_limit": 0, "github_write_limit": 0,
            "goal_idempotency_key": snapshots[0]["idempotency_key"], "plan_task_id": "CHECK001", "goal_admissions": snapshots}
    authority = PolicyAuthority("decision_fixture", "round_fixture", "b" * 64, head,
        "c" * 64, "dddd2024/Nerelan", "codex/fixture", head, head, binding)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry(),
        authority_loader=lambda: authority, task_scope_resolver=lambda task_id: load_host_validation_contract(store.get_task(task_id)))
    if not reopen:
        autonomy.activate_policy({"policy_id": binding["policy_id"], "policy_revision": 1, "policy": binding["policy"]})
    router = ExecutorRouter()
    def forbidden(**kwargs):
        pytest.fail("Model/provider backend reached by fixed-checker admission")
    monkeypatch.setattr(router, "create_executor", forbidden)
    monkeypatch.setattr(router, "dispatch_execute", forbidden)
    coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy,
        router=router, workspace_root=tmp_path / "workspaces", execution_authority_sha=head, planning_sha=head)
    return store, control, goals, autonomy, authority, coordinator


def admissions(control):
    return [r for r in control.list_receipts(window_id="admission-window") if r.operation_type == "goal_admission"]


def test_coordinator_admits_two_planned_goals_without_manual_approval_or_model(tmp_path, monkeypatch):
    store, control, goals, autonomy, authority, coordinator = system(tmp_path, monkeypatch)
    ids = [s["goal_id"] for s in authority.binding["goal_admissions"]]
    assert all(control.get_goal(i).status == "PLANNED" for i in ids)
    assert coordinator.tick() == 1
    assert coordinator.tick() == 1
    assert coordinator.tick() == 0
    assert len(admissions(control)) == 2
    assert all(r.actor == "fixture-controller" and r.confirmation_mode == "DELEGATED_CONTROLLER" for r in admissions(control))
    for identity in ids:
        links = control.list_goal_tasks(identity)
        assert len(links) == 1
        task = store.get_task(links[0]["task_id"])
        assert task.status == "READY_FOR_REVIEW" and task.validation_exit_code == 0
        assert task.validation_command_id == "git_diff_check"
    window = control.get_window("admission-window")
    assert (window.tasks_started, window.tasks_completed, window.retries_used) == (2, 2, 0)
    assert (window.observed_token_units, window.observed_cost_micro_units, window.unknown_observation_count) == (0, 0, 0)
    store._conn.close()


def test_restart_after_atomic_admission_resumes_existing_queued_tasks(tmp_path, monkeypatch):
    store, control, goals, autonomy, authority, _ = system(tmp_path, monkeypatch)
    assert all(r["admitted"] for r in autonomy.admit_goals(goals, window_id="admission-window"))
    original = {s["goal_id"]: control.list_goal_tasks(s["goal_id"])[0]["task_id"] for s in authority.binding["goal_admissions"]}
    store._conn.close()
    store, control, goals, autonomy, authority, coordinator = system(tmp_path, monkeypatch, reopen=True)
    assert all(r["replayed"] for r in autonomy.admit_goals(goals, window_id="admission-window"))
    assert coordinator.tick() == 1 and coordinator.tick() == 1
    assert len(admissions(control)) == 2
    assert original == {i: control.list_goal_tasks(i)[0]["task_id"] for i in original}
    assert control.get_window("admission-window").tasks_started == 2
    store._conn.close()


def test_concurrent_connections_admit_once(tmp_path, monkeypatch):
    one = system(tmp_path, monkeypatch)
    two = system(tmp_path, monkeypatch, reopen=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(s[3].admit_goals, s[2], window_id="admission-window") for s in [one, two]]
        assert all(all(o["admitted"] for o in r.result(timeout=60)) for r in results)
    assert len(admissions(one[1])) == 2
    assert all(len(one[1].list_goal_tasks(s["goal_id"])) == 1 for s in one[4].binding["goal_admissions"])
    one[0]._conn.close(); two[0]._conn.close()


def test_isolated_revision_drift_does_not_stall_other_goal_or_repeat_denial(tmp_path, monkeypatch):
    store, control, goals, autonomy, authority, coordinator = system(tmp_path, monkeypatch)
    first, second = authority.binding["goal_admissions"]
    goals.amend(first["goal_id"], expected_revision=first["revision"], objective="Different obligation")
    assert coordinator.tick() == 1
    assert coordinator.tick() == 0
    assert control.list_goal_tasks(first["goal_id"]) == ()
    assert len(control.list_goal_tasks(second["goal_id"])) == 1
    assert len([r for r in admissions(control) if r.decision == "denied"]) == 1
    assert control.get_goal(first["goal_id"]).status == "DRAFT"
    store._conn.close()


@pytest.mark.parametrize("field,value", [("artifact_digest", "f" * 64), ("repository", "other/project")])
def test_corrupt_persisted_goal_cannot_broaden_approved_snapshot(tmp_path, monkeypatch, field, value):
    store, control, goals, autonomy, authority, coordinator = system(tmp_path, monkeypatch, count=1)
    # Ordinary test database fault injection, not an external production write path.
    identity = authority.binding["goal_admissions"][0]["goal_id"]
    control._conn.execute(f"UPDATE platform_goals SET {field} = ? WHERE id = ?", (value, identity))
    assert coordinator.tick() == 0
    assert control.list_goal_tasks(identity) == ()
    assert admissions(control)[0].decision == "denied"
    store._conn.close()


def test_receipt_failure_rolls_back_goal_tasks_and_preserves_window_hard_stop(tmp_path, monkeypatch):
    store, control, goals, autonomy, authority, _ = system(tmp_path, monkeypatch, count=1)
    identity = authority.binding["goal_admissions"][0]["goal_id"]
    control._conn.execute("CREATE TRIGGER receipt_failure BEFORE INSERT ON platform_operation_receipts "
        "WHEN NEW.operation_type = 'goal_admission' BEGIN SELECT RAISE(FAIL, 'fixture'); END")
    with pytest.raises(TaskStoreError, match="receipt_persistence_failed"):
        autonomy.admit_goals(goals, window_id="admission-window")
    assert control.get_goal(identity).status == "PLANNED"
    assert control.list_goal_tasks(identity) == ()
    assert control._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
    assert control.get_window("admission-window").status == "BLOCKED"
    store._conn.close()
    store = TaskStore(str(tmp_path / "tasks.sqlite3"));control = PlatformControlStore(store)
    assert control.get_window("admission-window").status == "BLOCKED"
    assert control.get_window("admission-window").tasks_started == 0
    store._conn.close()


def test_launch_fault_cannot_leave_approved_goal_without_receipt(tmp_path, monkeypatch):
    store, control, goals, autonomy, authority, _ = system(tmp_path, monkeypatch, count=1)
    def fail(*args, **kwargs):raise RuntimeError("injected materialization failure")
    monkeypatch.setattr(goals, "_launch", fail)
    with pytest.raises(RuntimeError, match="materialization"):
        autonomy.admit_goals(goals, window_id="admission-window")
    assert control.get_goal(authority.binding["goal_admissions"][0]["goal_id"]).status == "PLANNED"
    assert admissions(control) == []
    store._conn.close()


@pytest.mark.parametrize("stop", ["stop", "expiry"])
def test_revoked_or_expired_window_cannot_admit(tmp_path, monkeypatch, stop):
    store, control, goals, autonomy, authority, _ = system(tmp_path, monkeypatch, count=1)
    if stop == "stop":control.stop_window("admission-window", reason="owner_revoked")
    else:control._conn.execute("UPDATE platform_autonomous_windows SET expires_at = '2000-01-01T00:00:00Z' WHERE id = 'admission-window'")
    assert not autonomy.admit_goals(goals, window_id="admission-window")[0]["admitted"]
    assert control.list_goal_tasks(authority.binding["goal_admissions"][0]["goal_id"]) == ()
    store._conn.close()


@pytest.mark.parametrize("mutation", ["bool_revision", "duplicate", "unknown_field", "budget", "operations", "actor"])
def test_invalid_or_changed_binding_cannot_admit(tmp_path, monkeypatch, mutation):
    store, control, goals, autonomy, authority, _ = system(tmp_path, monkeypatch, count=1)
    binding = authority.binding
    if mutation == "bool_revision":binding["goal_admissions"][0]["revision"] = True
    elif mutation == "duplicate":binding["goal_admissions"].append(copy.deepcopy(binding["goal_admissions"][0]))
    elif mutation == "unknown_field":binding["goal_admissions"][0]["arbitrary_command"] = "not executed"
    elif mutation == "budget":binding["max_tasks"] = 100
    elif mutation == "operations":binding["allowed_operations"] = ["approve_goal", "execute_task"]
    else:binding["controller_identity"] = "different-controller"
    if mutation == "actor":
        assert not autonomy.admit_goals(goals, window_id="admission-window")[0]["admitted"]
    else:
        with pytest.raises(TaskStoreError):autonomy.admit_goals(goals, window_id="admission-window")
    assert control.list_goal_tasks(binding["goal_admissions"][0]["goal_id"]) == ()
    store._conn.close()


def test_capability_metadata_does_not_grant_legacy_goal_approval(tmp_path, monkeypatch):
    store, control, goals, autonomy, authority, _ = system(tmp_path, monkeypatch, count=1)
    legacy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    assert not legacy.authorize(window_id="admission-window", operation="approve_goal",
        repository="dddd2024/Nerelan", subject_id=authority.binding["goal_admissions"][0]["goal_id"], input_payload={})
    assert admissions(control) == []
    store._conn.close()
