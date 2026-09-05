"""Fail-closed command authorization for transition rounds."""

from __future__ import annotations

from fnmatch import fnmatch

from .legacy_adapter import canonical_command
from .models import ExecutionEnvelope, ExecutionRecord, TransitionCommand, TransitionCommandPlan


VALID_EXECUTION_SURFACES = frozenset({
    "github_control_plane",
    "trusted_worker",
    "ci_only",
    "remote_observation",
    "user_local",
    "local",
})

# Legacy compatibility token kept for historical Decisions and the migration
# round; ``local`` must never be the authoring default for new Decisions.
LEGACY_LOCAL_SURFACE = "local"

# Surfaces that represent shell/checked-out repository execution that a
# TrustedCommandRunner subprocess may execute. GitHub-native, CI, and
# read-only observation surfaces must never be subprocess-executed.
SUBPROCESS_EXECUTABLE_SURFACES = frozenset({
    "trusted_worker",
    "user_local",
    LEGACY_LOCAL_SURFACE,
})

# Explicit machine-specific capability declaration required for user_local.
MACHINE_SPECIFIC_EXECUTION_OPERATION = "machine_specific_execution"

# ---------------------------------------------------------------------------
# Canonical operation -> admissible execution-surface compatibility.
#
# #636 proved that a surface token being enum-valid is not enough: a fresh
# Decision can pair ``execution_surface`` with operations that surface cannot
# actually perform. This single canonical table is consumed by BOTH structured
# plan compilation and pre-execution plan validation so State Gate and
# Decision Preflight share identical semantics. ``local`` intentionally has
# no admissible operations here: it is a legacy compatibility token that is
# only readable through ``load_legacy_command_plan``.
# ---------------------------------------------------------------------------

_SUBPROCESS_MUTATION_SURFACES = frozenset({"trusted_worker", "user_local"})
_SUBPROCESS_VALIDATION_SURFACES = frozenset({"trusted_worker", "user_local", "ci_only"})
_READ_OBSERVATION_SURFACES = frozenset({"trusted_worker", "user_local", "ci_only", "remote_observation"})
_GITHUB_NATIVE_SURFACES = frozenset({"github_control_plane"})
_NETWORK_SURFACES = frozenset({"trusted_worker", "user_local", "ci_only", "github_control_plane"})

# Checkout/source-edits and checkout-local mutations require executor
# provenance (trusted_worker / explicit machine-specific user_local). They
# are NEVER satisfiable by the GitHub control plane, repository CI, or
# read-only observation even though those surface tokens are valid.
OPERATION_SURFACE_ADMISSIBILITY: dict[str, frozenset[str]] = {
    "source_edit": _SUBPROCESS_MUTATION_SURFACES,
    "commit": _SUBPROCESS_MUTATION_SURFACES,
    "build": _SUBPROCESS_MUTATION_SURFACES,
    "command_plan_generation": _SUBPROCESS_MUTATION_SURFACES,
    # Repository-owned validation executes in a checkout or in CI workflows.
    "unit_test": _SUBPROCESS_VALIDATION_SURFACES,
    "local_static_check": _SUBPROCESS_VALIDATION_SURFACES,
    "diff_validation": _SUBPROCESS_VALIDATION_SURFACES,
    "integration_test": _SUBPROCESS_VALIDATION_SURFACES,
    # Read-only observation.
    "repository_observation": _READ_OBSERVATION_SURFACES,
    "code_read": _READ_OBSERVATION_SURFACES,
    "read_only_audit": frozenset({"trusted_worker", "user_local", "remote_observation"}),
    "remote_observation": frozenset({"trusted_worker", "user_local", "ci_only", "remote_observation"}),
    # GitHub-native control-plane mutations/publication.
    "push": _GITHUB_NATIVE_SURFACES,
    "draft_pr": _GITHUB_NATIVE_SURFACES,
    "pr_create": _GITHUB_NATIVE_SURFACES,
    "pull_request_comment": _GITHUB_NATIVE_SURFACES,
    "issue_comment": _GITHUB_NATIVE_SURFACES,
    "mark_ready": _GITHUB_NATIVE_SURFACES,
    "merge": _GITHUB_NATIVE_SURFACES,
    "ready": _GITHUB_NATIVE_SURFACES,
    # Network/install modifiers.
    "network_access": _NETWORK_SURFACES,
    "network": _NETWORK_SURFACES,
    "package_install": _SUBPROCESS_VALIDATION_SURFACES,
    "dependency_install": _SUBPROCESS_VALIDATION_SURFACES,
    # Machine-specific declaration is user_local-only.
    "machine_specific_execution": frozenset({"user_local"}),
}

# Surfaces that current/new structured authoring may select. The legacy
# ``local`` token is deliberately excluded.
CURRENT_AUTHORING_SURFACES = frozenset({
    "github_control_plane",
    "trusted_worker",
    "ci_only",
    "remote_observation",
    "user_local",
})


def _admissible_surfaces(operation: str) -> frozenset[str] | None:
    return OPERATION_SURFACE_ADMISSIBILITY.get(operation)


def operation_surface_errors(
    operations: tuple[str, ...],
    surface: str,
    *,
    command_identity: str = "",
) -> tuple[str, ...]:
    """Return canonical operation↔surface incompatibility errors.

    Unknown operations fail closed: a current typed Decision must only declare
    operations whose admissible-surface class is known and whose surface is in
    that class. ``local`` carries no admissible operations for current New
    authoring; this function never authorizes it.
    """

    errors: list[str] = []
    for operation in operations:
        admissible = _admissible_surfaces(operation)
        if admissible is None:
            errors.append(f"unknown_operation:{operation}:{surface}:{command_identity}")
        elif surface not in admissible:
            errors.append(
                f"operation_surface_incompatible:{operation}:{surface}:{command_identity}"
            )
    return tuple(errors)


def validate_command_plan(plan: TransitionCommandPlan) -> tuple[str, ...]:
    errors: list[str] = []
    seen_commands: set[tuple[str, str]] = set()
    seen_command_ids: set[str] = set()
    if not plan.decision_id:
        errors.append("missing_decision_id")
    if not plan.round_id:
        errors.append("missing_round_id")
    for entry in plan.commands:
        identity = (canonical_command(entry.command), entry.execution_surface)
        if not identity[0]:
            errors.append("empty_command")
        if not entry.command_id:
            errors.append(f"missing_command_id:{identity[0]}")
        elif entry.command_id in seen_command_ids:
            errors.append(f"duplicate_command_id:{entry.command_id}")
        else:
            seen_command_ids.add(entry.command_id)
        if entry.execution_surface not in VALID_EXECUTION_SURFACES:
            errors.append(f"invalid_execution_surface:{entry.execution_surface}")
        if entry.execution_surface == "user_local" and MACHINE_SPECIFIC_EXECUTION_OPERATION not in entry.operations:
            errors.append(f"user_local_requires_machine_specific_execution:{identity[0]}")
        if not entry.expected_exit_codes:
            errors.append(f"missing_expected_exit_codes:{identity[0]}")
        if not entry.phase:
            errors.append(f"missing_phase:{identity[0]}")
        if not entry.operations and not entry.bootstrap_exception:
            # Bootstrap exception commands are permitted to omit operations
            # because they predate the structured command contract.
            errors.append(f"missing_operations:{identity[0]}")
        if identity in seen_commands:
            errors.append(f"duplicate_command:{identity[1]}:{identity[0]}")
        seen_commands.add(identity)
        # G2-compatibility / #636: current/new structured authoring must not
        # select the legacy ``local`` surface. Bootstrap-exception commands
        # are the narrow historical/migration seam and keep their exemption.
        if entry.execution_surface == LEGACY_LOCAL_SURFACE and not entry.bootstrap_exception:
            errors.append(
                f"legacy_local_surface_forbidden_in_current_authoring:{identity[0]}"
            )
        # Canonical operation↔surface admissibility. Historical tracked
        # artifacts stay readable through load_legacy_command_plan; this
        # validation is for current/new typed plans.
        compatibility = operation_surface_errors(
            entry.operations,
            entry.execution_surface,
            command_identity=identity[0],
        )
        errors.extend(compatibility)
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


def _path_matches_pattern(path: str, pattern: str) -> bool:
    """Match a path against a glob pattern, normalizing separators."""

    normalized = path.replace("\\", "/")
    candidate = pattern.replace("\\", "/")
    return fnmatch(normalized, candidate)


def _path_in_produced(path: str, produced_artifacts: tuple[str, ...]) -> bool:
    """Return True if path is covered by any produced_artifacts pattern."""

    normalized = path.replace("\\", "/")
    for pattern in produced_artifacts:
        candidate = pattern.replace("\\", "/")
        if fnmatch(normalized, candidate):
            return True
    return False


def validate_mutation_grants(
    plan: TransitionCommandPlan,
    records: tuple[ExecutionRecord, ...],
    *,
    generated_artifact_paths: tuple[str, ...] = (),
) -> list[str]:
    """Enforce command-bound mutation grants for every observed path.

    Every observed mutated path must belong to the exact plan entry selected by
    ``record.command_id``. ``generated_artifact_paths`` is inventory only and
    never grants write permission. Command-string fallback is deliberately
    forbidden: missing, unknown, or duplicated command IDs must fail closed.
    """

    violations: list[str] = []
    plan_by_id: dict[str, TransitionCommand] = {}
    duplicate_ids: set[str] = set()
    for entry in plan.commands:
        if not entry.command_id:
            continue
        if entry.command_id in plan_by_id:
            duplicate_ids.add(entry.command_id)
            continue
        plan_by_id[entry.command_id] = entry

    for record in records:
        record_command_id = record.command_id
        if record_command_id in duplicate_ids:
            for mutated_path in record.mutated_paths:
                violations.append(
                    f"ambiguous_command_id:{record_command_id}:{mutated_path}"
                )
            continue

        plan_entry = plan_by_id.get(record_command_id)
        for mutated_path in record.mutated_paths:
            if plan_entry is None:
                violations.append(
                    f"unknown_command_id:{record_command_id}:{mutated_path}"
                )
                continue
            in_produced = _path_in_produced(
                mutated_path,
                plan_entry.produced_artifacts,
            )
            in_allowed = _path_in_produced(
                mutated_path,
                plan_entry.allowed_mutated_paths,
            )
            if not in_produced and not in_allowed:
                violations.append(
                    f"missing_mutation_grant:{record_command_id}:{mutated_path}"
                )
    return violations
