"""Phase A: execution evidence schema and bootstrap state tests.

Covers the new stable command_id, required_evidence_source, authority_origin
fields, the strict execution record schema, and the BOOTSTRAP_OPEN /
BOOTSTRAP_EXPIRED lifecycle.
"""

from __future__ import annotations

import pytest

from reverse_agent.control_plane.legacy_adapter import (
    build_transition_command_plan,
    load_bootstrap_state,
    persist_bootstrap_state,
)
from reverse_agent.control_plane.models import (
    ExecutionEnvelope,
    ExecutionRecord,
    TransitionCommand,
    TransitionDecision,
)


def _decision() -> TransitionDecision:
    return TransitionDecision(
        decision_id="decision_evidence",
        round_id="round_evidence",
        status="APPROVED",
        mainline="engineering_branch",
        skill_profiles=("reverse-agent-iteration@v2",),
    )


def _structured_contract(*, allowed_commands: list) -> dict:
    return {
        "transition_kernel_required": True,
        "required_branch": "codex/example-v1",
        "activation_base_sha": "a" * 40,
        "bootstrap_exception_files": ["reverse_agent/project_gate.py"],
        "bootstrap_exception_commands": [],
        "allowed_commands": allowed_commands,
        "allowed_mutated_paths": ["reverse_agent/example/**"],
        "forbidden_mutated_paths": ["frontend/**"],
        "capability_policy": {
            "network_access_default_allowed": False,
            "local_network_exceptions": [],
            "ci_network_exceptions": [],
        },
        "path_risk_floor": [],
    }


def _structured_command(
    command_id: str = "status.git_status",
    command: str = "git status --short",
    *,
    required_evidence_source: str = "local_provenance",
    authority_origin: str = "normal_plan",
    network_access: bool = False,
    operations: tuple[str, ...] = ("repository_observation",),
) -> dict:
    return {
        "command_id": command_id,
        "command": command,
        "phase": "status",
        "required": True,
        "required_evidence_source": required_evidence_source,
        "expected_exit_codes": [0],
        "execution_surface": "local",
        "operations": list(operations),
        "network_access": network_access,
        "authority_origin": authority_origin,
    }


# --- Phase A.1: stable command_id + authority origin --------------------


def test_structured_command_plan_carries_command_id() -> None:
    """Structured commands must preserve command_id through the plan."""

    decision = _decision()
    contract = _structured_contract(
        allowed_commands=[_structured_command("status.git_status")],
    )
    plan = build_transition_command_plan(decision, contract)
    assert plan.commands[0].command_id == "status.git_status"
    assert plan.commands[0].authority_origin == "normal_plan"


def test_command_id_and_surface_must_match_record() -> None:
    """An execution record must match the plan entry by command_id + surface."""

    decision = _decision()
    contract = _structured_contract(
        allowed_commands=[_structured_command("status.git_status")],
    )
    plan = build_transition_command_plan(decision, contract)
    matching = plan.find_command("status.git_status", "local")
    assert matching is not None
    assert matching.command == "git status --short"


def test_bootstrap_command_gets_bootstrap_authority_origin() -> None:
    """Bootstrap exception commands carry authority_origin=bootstrap_exception."""

    decision = _decision()
    contract = _structured_contract(
        allowed_commands=[_structured_command("status.git_status")],
    )
    contract["bootstrap_exception_commands"] = ["git rev-parse HEAD"]
    plan = build_transition_command_plan(decision, contract)
    bootstrap_cmd = next(cmd for cmd in plan.commands if cmd.bootstrap_exception)
    assert bootstrap_cmd.authority_origin == "bootstrap_exception"


# --- Phase A.2: strict execution record schema --------------------------


def test_execution_record_rejects_missing_required_fields() -> None:
    """Strict execution record must reject missing required fields."""

    with pytest.raises(ValueError, match="missing_field:command_id"):
        ExecutionRecord(
            command_id="",
            command="git status --short",
            execution_surface="local",
            operations=("repository_observation",),
            mutated_paths=(),
            exit_code=0,
            started_at="2026-07-21T00:00:00Z",
            observed_at="2026-07-21T00:00:01Z",
            head_before="a" * 40,
            head_after="b" * 40,
            stdout_digest="sha256:abc",
            stderr_digest="sha256:def",
            authority_origin="normal_plan",
        )


def test_execution_record_rejects_missing_head_binding() -> None:
    with pytest.raises(ValueError, match="missing_field:head_before"):
        ExecutionRecord(
            command_id="status.git_status",
            command="git status --short",
            execution_surface="local",
            operations=("repository_observation",),
            mutated_paths=(),
            exit_code=0,
            started_at="2026-07-21T00:00:00Z",
            observed_at="2026-07-21T00:00:01Z",
            head_before="",
            head_after="b" * 40,
            stdout_digest="sha256:abc",
            stderr_digest="sha256:def",
            authority_origin="normal_plan",
        )


def test_execution_record_rejects_missing_digest() -> None:
    with pytest.raises(ValueError, match="missing_field:stdout_digest"):
        ExecutionRecord(
            command_id="status.git_status",
            command="git status --short",
            execution_surface="local",
            operations=("repository_observation",),
            mutated_paths=(),
            exit_code=0,
            started_at="2026-07-21T00:00:00Z",
            observed_at="2026-07-21T00:00:01Z",
            head_before="a" * 40,
            head_after="b" * 40,
            stdout_digest="",
            stderr_digest="sha256:def",
            authority_origin="normal_plan",
        )


def test_execution_record_rejects_invalid_authority_origin() -> None:
    with pytest.raises(ValueError, match="invalid_authority_origin"):
        ExecutionRecord(
            command_id="status.git_status",
            command="git status --short",
            execution_surface="local",
            operations=("repository_observation",),
            mutated_paths=(),
            exit_code=0,
            started_at="2026-07-21T00:00:00Z",
            observed_at="2026-07-21T00:00:01Z",
            head_before="a" * 40,
            head_after="b" * 40,
            stdout_digest="sha256:abc",
            stderr_digest="sha256:def",
            authority_origin="caller_supplied",
        )


# --- Phase A.3: bootstrap lifecycle -------------------------------------


def test_bootstrap_state_defaults_to_open(tmp_path) -> None:
    """Without a persisted state file, bootstrap is BOOTSTRAP_OPEN."""

    state = load_bootstrap_state(tmp_path / "missing.json")
    assert state.status == "BOOTSTRAP_OPEN"
    assert state.is_open is True
    assert state.is_expired is False


def test_bootstrap_state_can_be_expired(tmp_path) -> None:
    state_path = tmp_path / "bootstrap_state.json"
    persist_bootstrap_state(state_path, status="BOOTSTRAP_EXPIRED")
    loaded = load_bootstrap_state(state_path)
    assert loaded.status == "BOOTSTRAP_EXPIRED"
    assert loaded.is_expired is True


def test_bootstrap_state_rejects_invalid_status(tmp_path) -> None:
    state_path = tmp_path / "bootstrap_state.json"
    with pytest.raises(ValueError, match="invalid_bootstrap_status"):
        persist_bootstrap_state(state_path, status="BOOTSTRAP_UNKNOWN")


def test_expired_bootstrap_rejects_new_bootstrap_records(tmp_path) -> None:
    """Once BOOTSTRAP_EXPIRED, new bootstrap records must be rejected."""

    state_path = tmp_path / "bootstrap_state.json"
    persist_bootstrap_state(state_path, status="BOOTSTRAP_EXPIRED")
    state = load_bootstrap_state(state_path)
    assert state.is_expired is True
    # A record claiming bootstrap_exception after expiry must be flagged.
    record = ExecutionRecord(
        command_id="bootstrap.cmd",
        command="git rev-parse HEAD",
        execution_surface="local",
        operations=(),
        mutated_paths=(),
        exit_code=0,
        started_at="2026-07-21T00:00:00Z",
        observed_at="2026-07-21T00:00:01Z",
        head_before="a" * 40,
        head_after="b" * 40,
        stdout_digest="sha256:abc",
        stderr_digest="sha256:def",
        authority_origin="bootstrap_exception",
    )
    assert state.rejects_expired_bootstrap_record(record) is True


def test_open_bootstrap_accepts_new_bootstrap_records(tmp_path) -> None:
    state_path = tmp_path / "bootstrap_state.json"
    persist_bootstrap_state(state_path, status="BOOTSTRAP_OPEN")
    state = load_bootstrap_state(state_path)
    record = ExecutionRecord(
        command_id="bootstrap.cmd",
        command="git rev-parse HEAD",
        execution_surface="local",
        operations=(),
        mutated_paths=(),
        exit_code=0,
        started_at="2026-07-21T00:00:00Z",
        observed_at="2026-07-21T00:00:01Z",
        head_before="a" * 40,
        head_after="b" * 40,
        stdout_digest="sha256:abc",
        stderr_digest="sha256:def",
        authority_origin="bootstrap_exception",
    )
    assert state.rejects_expired_bootstrap_record(record) is False


# --- Phase C: plan-driven operation/capability anti-omission ------------


def _envelope(
    command: str = "git status --short",
    *,
    execution_surface: str = "local",
    operations: tuple[str, ...] = ("repository_observation",),
    exit_code: int | None = 0,
    mutated_paths: tuple[str, ...] = (),
) -> ExecutionEnvelope:
    return ExecutionEnvelope(
        command=command,
        execution_surface=execution_surface,
        operations=operations,
        exit_code=exit_code,
        mutated_paths=mutated_paths,
    )


def test_plan_operations_must_be_covered_by_envelope() -> None:
    """Phase C/F2: envelope omitting plan-declared operations must block.

    Plan declares ``repository_observation``; envelope with empty operations
    cannot bypass the operation check by claiming nothing happened.
    """

    from reverse_agent.control_plane.command_authority import reconcile_command
    from reverse_agent.control_plane.legacy_adapter import build_transition_command_plan

    decision = _decision()
    contract = _structured_contract(
        allowed_commands=[_structured_command("status.git_status", operations=("repository_observation",))],
    )
    plan = build_transition_command_plan(decision, contract)
    envelope = _envelope(operations=())
    errors = reconcile_command(plan, envelope)
    assert any("operations_under_reported" in err for err in errors)


def test_plan_network_access_enforces_policy_without_envelope_operations() -> None:
    """Phase C/F2: plan network_access=true triggers network policy check.

    Even when envelope omits operations, plan-declared network_access must
    still be subject to capability_policy enforcement.
    """

    from reverse_agent.control_plane.transition import _plan_network_policy_violations
    from reverse_agent.control_plane.legacy_adapter import build_transition_command_plan
    from reverse_agent.control_plane.models import CapabilityPolicy

    decision = _decision()
    contract = _structured_contract(
        allowed_commands=[_structured_command(
            "ci.install",
            command="python -m pip install -e .[test]",
            network_access=True,
            operations=("dependency_install",),
            required_evidence_source="exact_head_ci",
        )],
    )
    plan = build_transition_command_plan(decision, contract)
    # Envelope with no operations — must still trigger plan-driven network check.
    envelope = _envelope(
        command="python -m pip install -e .[test]",
        execution_surface="ci_only",
        operations=(),
    )
    policy = CapabilityPolicy(
        network_access_default_allowed=False,
        ci_network_exceptions=(),  # deny
    )
    violations = _plan_network_policy_violations(plan, (envelope,), policy)
    assert violations, "plan network_access=true must trigger network policy even without envelope operations"


def test_plan_network_false_envelope_network_operation_blocks() -> None:
    """Phase C/F2: envelope claiming network when plan denies must block."""

    from reverse_agent.control_plane.transition import _envelope_network_violations
    from reverse_agent.control_plane.models import CapabilityPolicy

    envelope = _envelope(operations=("network_access",))
    policy = CapabilityPolicy(
        network_access_default_allowed=False,
        local_network_exceptions=(),
    )
    violations = _envelope_network_violations((envelope,), policy)
    assert violations, "envelope network operation must be blocked when policy denies"


def test_unknown_envelope_operation_fails_closed() -> None:
    """Phase C: unknown operations must fail closed."""

    from reverse_agent.control_plane.transition import _unknown_operation_violations
    from reverse_agent.control_plane.legacy_adapter import build_transition_command_plan

    decision = _decision()
    contract = _structured_contract(
        allowed_commands=[_structured_command("status.git_status", operations=("repository_observation",))],
    )
    plan = build_transition_command_plan(decision, contract)
    # Envelope claims an operation not declared by the plan.
    envelope = _envelope(operations=("repository_observation", "data_exfiltration"))
    violations = _unknown_operation_violations(plan, (envelope,))
    assert violations, "unknown operation must fail closed"


# --- Phase E: path contract separation (4-group) -------------------------


def _contract_with_path_contract(
    *,
    reference_paths: list[str] | None = None,
    generated_artifact_paths: list[str] | None = None,
    allowed_mutated_paths: list[str] | None = None,
    forbidden_mutated_paths: list[str] | None = None,
    path_risk_floor: list | None = None,
) -> dict:
    base = _structured_contract(
        allowed_commands=[_structured_command("status.git_status")],
    )
    if reference_paths is not None:
        base["reference_paths"] = reference_paths
    if generated_artifact_paths is not None:
        base["generated_artifact_paths"] = generated_artifact_paths
    if allowed_mutated_paths is not None:
        base["allowed_mutated_paths"] = allowed_mutated_paths
    if forbidden_mutated_paths is not None:
        base["forbidden_mutated_paths"] = forbidden_mutated_paths
    if path_risk_floor is not None:
        base["path_risk_floor"] = path_risk_floor
    return base


def test_load_transition_scope_returns_generated_artifact_paths() -> None:
    """Phase E: generated_artifact_paths must be loaded as a separate group."""

    from reverse_agent.control_plane.legacy_adapter import load_transition_scope

    decision = _decision()
    contract = _contract_with_path_contract(
        reference_paths=["docs/roadmap/example.md"],
        generated_artifact_paths=[
            "project_state/gates/command_plan.json",
            "project_state/gates/transition_preflight_result.json",
        ],
        allowed_mutated_paths=["reverse_agent/example/**"],
        forbidden_mutated_paths=["frontend/**"],
    )
    scope = load_transition_scope(decision, contract)
    assert scope["generated_artifact_paths"] == (
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_preflight_result.json",
    )
    # Reference paths must remain separate from generated artifact paths.
    assert scope["reference_paths"] == ("docs/roadmap/example.md",)


def test_load_transition_scope_rejects_reference_generated_overlap() -> None:
    """Phase E: reference_paths and generated_artifact_paths must not overlap."""

    from reverse_agent.control_plane.legacy_adapter import load_transition_scope

    decision = _decision()
    contract = _contract_with_path_contract(
        reference_paths=["docs/roadmap/example.md"],
        generated_artifact_paths=["docs/roadmap/example.md"],
    )
    with pytest.raises(ValueError, match="reference_generated_path_conflict"):
        load_transition_scope(decision, contract)


def test_load_transition_scope_rejects_generated_forbidden_overlap() -> None:
    """Phase E: generated_artifact_paths and forbidden_mutated_paths must not overlap."""

    from reverse_agent.control_plane.legacy_adapter import load_transition_scope

    decision = _decision()
    contract = _contract_with_path_contract(
        generated_artifact_paths=["project_state/gates/command_plan.json"],
        forbidden_mutated_paths=["project_state/gates/command_plan.json"],
    )
    with pytest.raises(ValueError, match="generated_forbidden_path_conflict"):
        load_transition_scope(decision, contract)


def test_load_transition_scope_allows_generated_allowed_overlap() -> None:
    """Phase E v2: generated_artifact_paths may overlap with allowed_mutated_paths.

    The attestation policy seal round replaces the global generated-artifact
    exemption with command-bound mutation grants. A path may be both an
    authorized mutable path AND a generated artifact bound to a specific
    generator command via ``produced_artifacts``. The scope loader must accept
    this overlap; binding enforcement happens at execution-record validation.
    """

    from reverse_agent.control_plane.legacy_adapter import load_transition_scope

    decision = _decision()
    contract = _contract_with_path_contract(
        generated_artifact_paths=["project_state/gates/command_plan.json"],
        allowed_mutated_paths=["project_state/gates/command_plan.json"],
    )
    scope = load_transition_scope(decision, contract)
    assert "project_state/gates/command_plan.json" in scope["generated_artifact_paths"]
    assert "project_state/gates/command_plan.json" in scope["allowed_paths"]


def test_path_risk_applies_to_all_observed_paths_including_allowed() -> None:
    """Phase E/F5: path risk floor must apply to ALL observed paths, not just outside_scope.

    Modifying an allowed path that is also in the risk floor (e.g. workflow file)
    must still be flagged so the runtime can route to Trust Authorization.
    """

    from reverse_agent.control_plane.transition import _path_risk_floor_violations
    from reverse_agent.control_plane.models import PathRiskFloor

    floor = PathRiskFloor(
        entries=(
            (".github/workflows/**", "R2"),
            ("pyproject.toml", "R2"),
        )
    )
    observed = (
        "reverse_agent/example.py",  # not in floor
        ".github/workflows/ci.yml",  # R2 sensitive
        "pyproject.toml",            # R2 sensitive
    )
    violations = _path_risk_floor_violations(observed, floor, minimum="R2")
    assert ".github/workflows/ci.yml:R2" in violations
    assert "pyproject.toml:R2" in violations
