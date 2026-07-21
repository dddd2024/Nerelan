"""Fail-closed command authorization for transition rounds."""

from __future__ import annotations

from typing import Iterable

from .legacy_adapter import canonical_command
from .models import ExecutionEnvelope, TransitionCommand, TransitionCommandPlan


VALID_EXECUTION_SURFACES = frozenset({"local", "ci_only", "remote_observation"})


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
        if not entry.phase:
            errors.append(f"missing_phase:{identity[0]}")
        if not entry.operations and not entry.bootstrap_exception:
            # Bootstrap exception commands are permitted to omit operations
            # because they predate the structured command contract.
            errors.append(f"missing_operations:{identity[0]}")
        if identity in seen:
            errors.append(f"duplicate_command:{identity[1]}:{identity[0]}")
        seen.add(identity)
    return tuple(errors)


def _find_matching_command(
    plan: TransitionCommandPlan,
    envelope: ExecutionEnvelope,
) -> TransitionCommand | None:
    requested = canonical_command(envelope.command)
    for entry in plan.commands:
        if canonical_command(entry.command) == requested and entry.execution_surface == envelope.execution_surface:
            return entry
    return None


def authorize_command(
    plan: TransitionCommandPlan,
    envelope: ExecutionEnvelope,
) -> tuple[str, ...]:
    """Deny undeclared commands and cross-surface execution by default."""

    requested = canonical_command(envelope.command)
    exact = _find_matching_command(plan, envelope)
    if exact:
        return _validate_command_execution(exact, envelope)
    other_surface = [
        entry.execution_surface
        for entry in plan.commands
        if canonical_command(entry.command) == requested
    ]
    if other_surface:
        return (f"execution_surface_mismatch:{requested}",)
    return (f"undeclared_command:{requested}",)


def _validate_command_execution(
    command: TransitionCommand,
    envelope: ExecutionEnvelope,
) -> tuple[str, ...]:
    """Validate execution-surface-specific constraints for an authorized command."""

    errors: list[str] = []
    if command.network_access and not envelope.operations:
        # Commands that declare network access must also declare operations so
        # capability reconciliation has something to map.
        errors.append(f"missing_network_operations:{canonical_command(command.command)}")
    if envelope.exit_code is not None and command.expected_exit_codes:
        if envelope.exit_code not in command.expected_exit_codes:
            errors.append(
                f"exit_code_mismatch:{canonical_command(command.command)}:{envelope.exit_code}"
            )
    return tuple(errors)


def reconcile_command(
    plan: TransitionCommandPlan,
    envelope: ExecutionEnvelope,
) -> tuple[str, ...]:
    """Reconcile a real execution record against the plan.

    This is the post-execution analog of :func:`authorize_command`. It uses
    the same matching rule but additionally requires the envelope to carry an
    exit code and surface that match the plan entry exactly. Bootstrap
    exception commands are matched but flagged so callers can distinguish them
    from normal plan-authorized commands.
    """

    requested = canonical_command(envelope.command)
    command = _find_matching_command(plan, envelope)
    if command is None:
        other_surfaces = [
            entry.execution_surface
            for entry in plan.commands
            if canonical_command(entry.command) == requested
        ]
        if other_surfaces:
            return (f"execution_surface_mismatch:{requested}",)
        return (f"undeclared_command:{requested}",)
    errors: list[str] = []
    # ``exit_code is None`` marks a pre-execution authorization envelope
    # (e.g. the trust authorization port asking whether a command may run).
    # Only validate the exit code when execution has actually been observed.
    if envelope.exit_code is not None and command.expected_exit_codes:
        if envelope.exit_code not in command.expected_exit_codes:
            errors.append(
                f"exit_code_mismatch:{requested}:{envelope.exit_code}"
            )
    # Phase C/F2: plan-driven operation coverage. When the plan declares
    # operations, the envelope must cover them all. An empty envelope
    # operations tuple cannot bypass the operation check by claiming
    # nothing happened. Bootstrap exception commands are exempt because
    # they predate the structured operation contract.
    if command.operations and not command.bootstrap_exception:
        missing = tuple(
            operation for operation in command.operations
            if operation not in envelope.operations
        )
        if missing:
            errors.append(f"operations_under_reported:{requested}:{list(missing)}")
    return tuple(errors)
