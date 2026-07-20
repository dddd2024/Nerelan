"""Fail-closed command authorization for transition rounds."""

from __future__ import annotations

from .models import ExecutionEnvelope, TransitionCommandPlan


VALID_EXECUTION_SURFACES = frozenset({"local", "ci_only"})


def canonical_command(command: str) -> str:
    """Return a stable command identity without interpreting shell syntax."""

    return " ".join(str(command).split())


def validate_command_plan(plan: TransitionCommandPlan) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    if not plan.decision_id:
        errors.append("missing_decision_id")
    if not plan.round_id:
        errors.append("missing_round_id")
    for entry in plan.commands:
        identity = (canonical_command(entry.command), entry.execution_surface)
        if not identity[0]:
            errors.append("empty_command")
        if entry.execution_surface not in VALID_EXECUTION_SURFACES:
            errors.append(f"invalid_execution_surface:{entry.execution_surface}")
        if not entry.expected_exit_codes:
            errors.append(f"missing_expected_exit_codes:{identity[0]}")
        if identity in seen:
            errors.append(f"duplicate_command:{identity[1]}:{identity[0]}")
        seen.add(identity)
    return tuple(errors)


def authorize_command(
    plan: TransitionCommandPlan,
    envelope: ExecutionEnvelope,
) -> tuple[str, ...]:
    """Deny undeclared commands and cross-surface execution by default."""

    requested = canonical_command(envelope.command)
    exact = [
        entry
        for entry in plan.commands
        if canonical_command(entry.command) == requested
        and entry.execution_surface == envelope.execution_surface
    ]
    if exact:
        return ()
    other_surface = [
        entry.execution_surface
        for entry in plan.commands
        if canonical_command(entry.command) == requested
    ]
    if other_surface:
        return (f"execution_surface_mismatch:{requested}",)
    return (f"undeclared_command:{requested}",)
