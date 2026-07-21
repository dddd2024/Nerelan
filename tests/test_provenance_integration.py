"""Integration coverage for strict provenance and command authority.

This file is intentionally narrow. It covers the bootstrap-safe portion that can
be completed without running the production trusted executor: globally unique
command IDs and fail-closed mutation attribution. The execution Agent must
extend this file when TrustedExecutionContext and the atomic evidence journal
are implemented.
"""

from __future__ import annotations

from reverse_agent.control_plane.command_authority import (
    validate_command_plan,
    validate_mutation_grants,
)
from reverse_agent.control_plane.models import (
    ExecutionRecord,
    TransitionCommand,
    TransitionCommandPlan,
)


def _command(
    *,
    command_id: str,
    command: str = "python -m pytest -q",
    allowed_mutated_paths: tuple[str, ...] = (),
    produced_artifacts: tuple[str, ...] = (),
) -> TransitionCommand:
    return TransitionCommand(
        command=command,
        phase="test",
        required=True,
        expected_exit_codes=(0,),
        execution_surface="local",
        operations=("integration_test",),
        command_id=command_id,
        authority_origin="normal_plan",
        allowed_mutated_paths=allowed_mutated_paths,
        produced_artifacts=produced_artifacts,
    )


def _plan(*commands: TransitionCommand) -> TransitionCommandPlan:
    return TransitionCommandPlan(
        decision_id="decision_provenance_integration",
        round_id="round_provenance_integration",
        commands=tuple(commands),
    )


def _record(
    *,
    command_id: str,
    command: str,
    mutated_paths: tuple[str, ...],
) -> ExecutionRecord:
    empty_digest = "sha256:" + ("0" * 64)
    return ExecutionRecord(
        command_id=command_id,
        command=command,
        execution_surface="local",
        operations=("integration_test",),
        mutated_paths=mutated_paths,
        exit_code=0,
        started_at="2026-07-21T00:00:00Z",
        observed_at="2026-07-21T00:00:01Z",
        head_before="a" * 40,
        head_after="a" * 40,
        stdout_digest=empty_digest,
        stderr_digest=empty_digest,
        authority_origin="normal_plan",
    )


def test_command_plan_rejects_missing_command_id() -> None:
    plan = _plan(_command(command_id=""))

    errors = validate_command_plan(plan)

    assert "missing_command_id:python -m pytest -q" in errors


def test_command_plan_rejects_duplicate_command_ids_globally() -> None:
    plan = _plan(
        _command(command_id="test.shared", command="python -m pytest tests/a.py -q"),
        _command(command_id="test.shared", command="python -m pytest tests/b.py -q"),
    )

    errors = validate_command_plan(plan)

    assert "duplicate_command_id:test.shared" in errors


def test_mutation_grant_requires_exact_command_id() -> None:
    command = _command(
        command_id="report.generate",
        command="python -m reverse_agent.project_gate transition-report",
        produced_artifacts=("project_state/execution_report.md",),
    )
    plan = _plan(command)
    record = _record(
        command_id="legacy.unknown",
        command=command.command,
        mutated_paths=("project_state/execution_report.md",),
    )

    violations = validate_mutation_grants(plan, (record,))

    assert violations == [
        "unknown_command_id:legacy.unknown:project_state/execution_report.md"
    ]


def test_mutation_grant_accepts_exact_allowed_path() -> None:
    command = _command(
        command_id="gate.command_plan",
        allowed_mutated_paths=("project_state/gates/command_plan.json",),
    )
    plan = _plan(command)
    record = _record(
        command_id=command.command_id,
        command=command.command,
        mutated_paths=("project_state/gates/command_plan.json",),
    )

    assert validate_mutation_grants(plan, (record,)) == []


def test_mutation_grant_rejects_ambiguous_duplicate_command_id() -> None:
    first = _command(
        command_id="gate.shared",
        command="python -m tool first",
        allowed_mutated_paths=("project_state/gates/first.json",),
    )
    second = _command(
        command_id="gate.shared",
        command="python -m tool second",
        allowed_mutated_paths=("project_state/gates/second.json",),
    )
    plan = _plan(first, second)
    record = _record(
        command_id="gate.shared",
        command=first.command,
        mutated_paths=("project_state/gates/first.json",),
    )

    violations = validate_mutation_grants(plan, (record,))

    assert violations == [
        "ambiguous_command_id:gate.shared:project_state/gates/first.json"
    ]
