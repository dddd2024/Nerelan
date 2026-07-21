"""Phase E: command-bound mutation grants tests.

Replaces the global generated-artifact exemption with command-specific
grants. A path in ``generated_artifact_paths`` may only be mutated by the
command whose ``produced_artifacts`` entry covers that path (F7).
"""

from __future__ import annotations

import pytest

from reverse_agent.control_plane.command_authority import validate_mutation_grants
from reverse_agent.control_plane.models import (
    ExecutionRecord,
    TransitionCommand,
    TransitionCommandPlan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _command(
    *,
    command_id: str = "gate.command_plan",
    command: str = "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    produced_artifacts: tuple[str, ...] = (),
) -> TransitionCommand:
    return TransitionCommand(
        command_id=command_id,
        command=command,
        phase="gate",
        required=True,
        expected_exit_codes=(0,),
        execution_surface="local",
        operations=("command_plan_generation",),
        authority_origin="normal_plan",
        produced_artifacts=produced_artifacts,
    )


def _record(
    *,
    command_id: str = "gate.command_plan",
    command: str = "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    mutated_paths: tuple[str, ...] = (),
) -> ExecutionRecord:
    return ExecutionRecord(
        command_id=command_id,
        command=command,
        execution_surface="local",
        operations=("command_plan_generation",),
        mutated_paths=mutated_paths,
        exit_code=0,
        started_at="2026-07-21T10:00:00Z",
        observed_at="2026-07-21T10:00:01Z",
        head_before="a" * 40,
        head_after="a" * 40,
        stdout_digest="sha256:" + "0" * 64,
        stderr_digest="sha256:" + "0" * 64,
        authority_origin="normal_plan",
    )


def _plan(*commands: TransitionCommand) -> TransitionCommandPlan:
    return TransitionCommandPlan(
        decision_id="decision_grants",
        round_id="round_grants",
        commands=commands,
    )


# ---------------------------------------------------------------------------
# Command-bound mutation grants
# ---------------------------------------------------------------------------


def test_command_with_produced_artifacts_can_mutate_them() -> None:
    """A command may mutate paths listed in its produced_artifacts."""

    cmd = _command(
        produced_artifacts=(
            "project_state/gates/command_plan.json",
            "project_state/gates/transition_command_plan_preview.json",
        ),
    )
    plan = _plan(cmd)
    record = _record(
        mutated_paths=(
            "project_state/gates/command_plan.json",
            "project_state/gates/transition_command_plan_preview.json",
        ),
    )
    violations = validate_mutation_grants(
        plan,
        (record,),
        generated_artifact_paths=(
            "project_state/gates/command_plan.json",
            "project_state/gates/transition_command_plan_preview.json",
        ),
    )
    assert violations == [], violations


def test_command_without_grant_cannot_mutate_generated_artifact() -> None:
    """A command without produced_artifacts cannot mutate generated artifacts."""

    cmd = _command(produced_artifacts=())  # no grants
    plan = _plan(cmd)
    record = _record(
        mutated_paths=("project_state/gates/command_plan.json",),
    )
    violations = validate_mutation_grants(
        plan,
        (record,),
        generated_artifact_paths=("project_state/gates/command_plan.json",),
    )
    assert any("missing_mutation_grant" in v for v in violations), violations


def test_command_can_only_mutate_its_own_artifacts() -> None:
    """A command cannot mutate another command's produced artifacts."""

    cmd_a = _command(
        command_id="gate.command_plan",
        produced_artifacts=("project_state/gates/command_plan.json",),
    )
    cmd_b = _command(
        command_id="report.generate_local",
        command="python -m reverse_agent.project_gate transition-report --state-dir project_state",
        produced_artifacts=("project_state/execution_report.md",),
    )
    plan = _plan(cmd_a, cmd_b)
    # cmd_b tries to mutate cmd_a's artifact.
    record = _record(
        command_id="report.generate_local",
        command="python -m reverse_agent.project_gate transition-report --state-dir project_state",
        mutated_paths=("project_state/gates/command_plan.json",),
    )
    violations = validate_mutation_grants(
        plan,
        (record,),
        generated_artifact_paths=(
            "project_state/gates/command_plan.json",
            "project_state/execution_report.md",
        ),
    )
    assert any("missing_mutation_grant" in v for v in violations), violations


def test_command_can_mutate_non_artifact_paths_freely() -> None:
    """Non-artifact paths are not subject to produced_artifacts binding."""

    cmd = _command(produced_artifacts=())
    plan = _plan(cmd)
    record = _record(
        mutated_paths=("reverse_agent/example.py",),  # not a generated artifact
    )
    violations = validate_mutation_grants(
        plan,
        (record,),
        generated_artifact_paths=("project_state/gates/command_plan.json",),
    )
    assert violations == [], violations


def test_unknown_command_id_cannot_mutate_artifacts() -> None:
    """Records with unknown command_id cannot mutate generated artifacts."""

    cmd = _command(produced_artifacts=("project_state/gates/command_plan.json",))
    plan = _plan(cmd)
    record = _record(
        command_id="unknown.command",
        command="some-command",
        mutated_paths=("project_state/gates/command_plan.json",),
    )
    violations = validate_mutation_grants(
        plan,
        (record,),
        generated_artifact_paths=("project_state/gates/command_plan.json",),
    )
    assert any("unknown_command_id" in v for v in violations), violations


def test_pattern_based_produced_artifacts_match() -> None:
    """produced_artifacts may use glob patterns to cover multiple files."""

    cmd = _command(
        produced_artifacts=("project_state/gates/*.json",),
    )
    plan = _plan(cmd)
    record = _record(
        mutated_paths=(
            "project_state/gates/command_plan.json",
            "project_state/gates/execution_log.json",
        ),
    )
    violations = validate_mutation_grants(
        plan,
        (record,),
        generated_artifact_paths=(
            "project_state/gates/command_plan.json",
            "project_state/gates/execution_log.json",
        ),
    )
    assert violations == [], violations
