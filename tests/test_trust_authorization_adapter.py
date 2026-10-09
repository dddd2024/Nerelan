from __future__ import annotations

from dataclasses import replace

from reverse_agent.architecture.contracts import AuthorizationRequest, ExecutionEnvelope, WorkflowIdentity
from reverse_agent.architecture.risk import AuthorizationStatus, RiskTier
from reverse_agent.control_plane.models import TransitionAuthority, TransitionCommand, TransitionCommandPlan, TransitionDecision
from reverse_agent.trust.authorization import TransitionKernelAuthorizationAdapter


def test_policy_loader_rejects_caller_verified_without_host_pins(tmp_path, monkeypatch):
    import pytest
    from reverse_agent.platform_v1 import authority_adapter
    monkeypatch.setattr(authority_adapter.subprocess, "run", lambda *_a, **_k: (_ for _ in ()).throw(
        AssertionError("invalid pins must not reach Git or a runtime")))
    with pytest.raises(authority_adapter.AuthorityBundleError, match="invalid_policy_host_pins"):
        authority_adapter.load_policy_authority(repo_dir=str(tmp_path), pins={"verified": True},
                                               database_path=str(tmp_path / "tasks.sqlite3"), host_instance_id="host")


def test_policy_loader_detects_material_edit_before_git_or_preflight(tmp_path, monkeypatch):
    import json
    import pytest
    from reverse_agent.platform_v1 import authority_adapter
    state = tmp_path / "project_state"
    state.mkdir()
    meta = {"schema_version": 1, "status": "APPROVED", "mainline": "engineering_branch",
            "decision_id": "decision_fixture", "round_id": "round_fixture"}
    (state / "decision_packet.md").write_text(
        "```json decision_meta\n" + json.dumps(meta) + "\n```\n"
        "```json decision_contract\n{}\n```\n", encoding="utf-8")
    pins = {"decision_commit_sha": "a" * 40, "decision_content_sha256": "a" * 64,
            "expected_head_sha": "b" * 40, "command_plan_sha256": "b" * 64,
            "upper_proposal_sha256": "c" * 64, "upper_expires_at": "2099-01-01T00:00:00Z",
            "delegation_slot_id": "fixture-slot", "database_path": str(tmp_path / "tasks.sqlite3"),
            "workspace_path": str(tmp_path), "host_instance_id": "fixture-host"}
    monkeypatch.setattr(authority_adapter.subprocess, "run", lambda *_a, **_k: (_ for _ in ()).throw(
        AssertionError("material edit must fail before Git")))
    with pytest.raises(authority_adapter.AuthorityBundleError, match="policy_decision_digest_mismatch"):
        authority_adapter.load_policy_authority(repo_dir=str(tmp_path), pins=pins,
                                               database_path=pins["database_path"], host_instance_id="fixture-host")


def test_policy_loader_accepts_real_immutable_git_decision_and_canonical_preflight(tmp_path):
    """Exercise the actual Gate; this synthetic grant is not live Owner evidence."""
    import hashlib
    import json
    import subprocess
    from datetime import datetime, timedelta, timezone
    from reverse_agent import project_gate
    from reverse_agent.platform_v1.authority_adapter import load_policy_authority
    from reverse_agent.platform_v1.autonomy import policy_digest

    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        return subprocess.run(["git", *args], cwd=repo, check=True,
                              capture_output=True, text=True).stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.email", "tests@example.invalid")
    git("config", "user.name", "policy-fixture")
    git("config", "core.autocrlf", "false")
    git("remote", "add", "origin", "https://github.com/dddd2024/Nerelan.git")
    (repo / "input.txt").write_text("original\n", encoding="utf-8")
    git("add", "input.txt")
    git("commit", "-qm", "base")
    base = git("rev-parse", "HEAD")
    branch = "codex/policy-authority-fixture"
    git("checkout", "-qb", branch)
    now = datetime.now(timezone.utc)
    caps = {key: 0 for key in ("maxPrsOpened", "maxMergesToMain", "maxReleasesCreated", "maxDeploysToEnvironment")}
    policy = {
        "mode": "CONTROLLER_REVIEW", "repository": "dddd2024/Nerelan",
        "resourceAccess": {
            "filesystem": {"allowedPaths": ["input.txt"], "writablePaths": []},
            "network": {"allowedDomains": [], "allowWrite": False},
            "shell": {"allowedCommands": ["git_diff_check"], "deniedCommands": []},
            "secrets": {"access": "none", "allowedKeys": []},
            "workerApproval": {"required": False, "approvers": []}},
        "githubCapabilities": [], "publicationCapabilities": [],
        "publicationPolicy": {"allowedArtifactOrPackage": [], "allowedRegistry": [],
                              "allowedRepository": [], "allowedEnvironment": []},
        "mergePolicy": {"allowedRepositories": [], "allowedBaseBranches": [], "requiredChecks": [],
                        "allowedMergeMethods": [], "requireExactHead": True},
        "autonomousWindow": {"enabled": True, "startsAt": (now - timedelta(seconds=2)).isoformat(),
                             "expiresAt": (now + timedelta(hours=1)).isoformat(), **caps,
                             "stopConditions": [{"type": "window_expired", "scope": "window"}]},
        "budgets": dict(caps)}
    binding = {
        "schema_version": 1, "confirmation_mode": "DELEGATED_CONTROLLER", "personally_human": False,
        "controller_identity": "fixture-controller", "upper_proposal_sha256": "a" * 64,
        "upper_expires_at": (now + timedelta(hours=2)).isoformat(), "phase_ordinal": 6,
        "policy_id": "fixture-policy", "policy_revision": 1, "policy": policy,
        "policy_digest_sha256": policy_digest(policy), "window_id": "fixture-window",
        "delegation_slot_id": "fixture-slot", "slot_ordinal": 1, "max_real_window_activations": 1,
        "host_instance_id": "fixture-host", "runtime_instance_kind": "acceptance",
        "database_path": str(tmp_path / "tasks.sqlite3"), "workspace_path": str(repo),
        "allowed_operations": ["validate_task"], "validation_command_ids": ["git_diff_check"],
        "validation_paths": ["input.txt"], "max_tasks": 1, "max_retries": 0, "max_concurrent_tasks": 1,
        "model_call_limit": 0, "provider_call_limit": 0, "github_write_limit": 0,
        "goal_idempotency_key": "fixture-goal", "plan_task_id": "CHECK001"}
    meta = {"schema_version": 1, "decision_id": "decision_policy_fixture", "round_id": "round_policy_fixture",
            "status": "APPROVED", "mainline": "engineering_branch", "skill_profiles": ["reverse-agent-iteration@v2"]}
    contract = {
        "repository": "dddd2024/Nerelan", "transition_kernel_required": True,
        "required_branch": branch, "activation_base_sha": base, "starting_head": base,
        "decision_content_immutable_after_activation": True, "decision_immutability_required": True,
        "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
        "bootstrap_exception_commands": ["git diff --check"], "allowed_source_paths": ["input.txt"],
        "forbidden_mutated_paths": ["frontend/**"], "direct_push_to_main_allowed": False,
        "merge_allowed": False, "force_push_allowed": False, "rebase_during_execution_allowed": False,
        "destructive_operations_allowed": False, "unknown_binary_execution_allowed": False,
        "model_api_invocation_allowed": False, "external_reverse_tool_invocation_allowed": False,
        "live_model_call_limit": 0, "live_provider_access_allowed": False, "autonomy_policy_authority": binding}
    state = repo / "project_state"
    state.mkdir()
    decision = state / "decision_packet.md"
    decision.write_text("```json decision_meta\n" + json.dumps(meta) + "\n```\n\n```json decision_contract\n"
                        + json.dumps(contract) + "\n```\n", encoding="utf-8")
    git("add", "project_state/decision_packet.md")
    git("commit", "-qm", "immutable Decision activation")
    activation = git("rev-parse", "HEAD")
    registry = repo / ".codex-skills" / "registry.json"
    registry.parent.mkdir()
    registry.write_text(json.dumps({"schema_version": 1, "skills": {
        "reverse-agent-iteration": {"status": "active", "version": 2}}}), encoding="utf-8")
    generated = project_gate.transition_command_plan(state_dir=state)
    assert generated["plan_status"] == "PASSED"
    preflight = project_gate.transition_preflight(state_dir=state, repo_root=repo)
    assert preflight["gate_status"] == "PRE_EXECUTION_AUTHORIZED", preflight
    pins = {"decision_commit_sha": activation, "expected_head_sha": activation,
            "decision_content_sha256": hashlib.sha256(decision.read_bytes()).hexdigest(),
            "command_plan_sha256": hashlib.sha256((state / "gates" / "command_plan.json").read_bytes()).hexdigest(),
            **{key: binding[key] for key in ("upper_proposal_sha256", "upper_expires_at", "delegation_slot_id",
                                            "database_path", "workspace_path", "host_instance_id")}}
    authority = load_policy_authority(repo_dir=str(repo), pins=pins,
                                     database_path=binding["database_path"], host_instance_id="fixture-host")
    assert authority.decision_commit_sha == activation
    assert authority.head_sha == activation
    assert authority.base_sha == base
    assert authority.binding == binding
    assert authority.command_plan_sha256 == pins["command_plan_sha256"]


def _authority() -> TransitionAuthority:
    decision = TransitionDecision("decision_x", "round_x", "APPROVED", "engineering_branch", ("reverse-agent-iteration@v2",))
    command = "python -m pytest tests/test_architecture_contracts.py -q"
    plan = TransitionCommandPlan(
        "decision_x",
        "round_x",
        (TransitionCommand(
            command,
            "test",
            True,
            (0,),
            "trusted_worker",
            ("unit_test",),
            command_id="test.unit",
            allowed_mutated_paths=("tests/test_architecture_contracts.py",),
        ),),
    )
    return TransitionAuthority(
        decision=decision,
        command_plan=plan,
        expected_decision_id="decision_x",
        expected_round_id="round_x",
        active_skills=("reverse-agent-iteration@v2",),
        legal_mainlines=("engineering_branch",),
        expected_branch="codex/architecture-spine-v1",
        actual_branch="codex/architecture-spine-v1",
        base_sha="a" * 40,
        merge_base_sha="a" * 40,
        decision_commit_sha="b" * 40,
        decision_is_ancestor=True,
        observed_paths=(),
        allowed_paths=("tests/test_architecture_contracts.py",),
        forbidden_paths=("frontend/**",),
        forbidden_operations=("force_push",),
    )


def _request(*, decision_id: str = "decision_x", tier: RiskTier = RiskTier.R2) -> AuthorizationRequest:
    return AuthorizationRequest(
        workflow_identity=WorkflowIdentity("workflow-x", "owner/repo#1@node"),
        risk_tier=tier,
        envelope=ExecutionEnvelope(("unit_test",), ("tests/test_architecture_contracts.py",)),
        decision_id=decision_id,
        round_id="round_x",
        command="python -m pytest tests/test_architecture_contracts.py -q",
    )


def test_transition_adapter_authorizes_matching_high_risk_request() -> None:
    result = TransitionKernelAuthorizationAdapter(_authority()).authorize(_request())
    assert result.status is AuthorizationStatus.AUTHORIZED


def test_transition_adapter_fails_closed_on_identity_or_kernel_failure() -> None:
    adapter = TransitionKernelAuthorizationAdapter(_authority())
    assert adapter.authorize(_request(decision_id="wrong")).status is AuthorizationStatus.BLOCKED
    broken = replace(_authority(), decision_is_ancestor=False)
    assert TransitionKernelAuthorizationAdapter(broken).authorize(_request()).status is AuthorizationStatus.BLOCKED


def test_transition_adapter_does_not_accept_low_risk_requests() -> None:
    result = TransitionKernelAuthorizationAdapter(_authority()).authorize(_request(tier=RiskTier.R1))
    assert result.status is AuthorizationStatus.BLOCKED
