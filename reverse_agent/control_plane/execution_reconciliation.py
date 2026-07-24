"""Post-execution reconciliation between observed transcripts and the plan.

This module closes the gap between ``PRE_EXECUTION_AUTHORIZED`` and
``POST_EXECUTION_RECONCILED``. The transition preflight must not claim
command authority passed when no real execution envelopes are supplied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .command_authority import canonical_command, reconcile_command
from .models import ExecutionEnvelope, TransitionCommandPlan


@dataclass(frozen=True)
class ReconciliationOutcome:
    status: str
    matched: tuple[dict[str, Any], ...]
    undeclared: tuple[str, ...]
    surface_mismatches: tuple[str, ...]
    bootstrap_exceptions: tuple[str, ...]
    missing_evidence: bool
    blocking_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "matched": [dict(item) for item in self.matched],
            "undeclared": list(self.undeclared),
            "surface_mismatches": list(self.surface_mismatches),
            "bootstrap_exceptions": list(self.bootstrap_exceptions),
            "missing_evidence": self.missing_evidence,
            "blocking_reasons": list(self.blocking_reasons),
        }


def reconcile_executions(
    plan: TransitionCommandPlan,
    envelopes: tuple[ExecutionEnvelope, ...],
) -> ReconciliationOutcome:
    """Match each envelope against one exact plan entry.

    Returns a structured outcome. ``status`` is one of:
    - ``PRE_EXECUTION_AUTHORIZED``: no envelopes were supplied; the plan is
      validated but no execution has been observed yet.
    - ``POST_EXECUTION_RECONCILED``: every envelope matched a plan entry,
      surface and exit code exactly.
    - ``BLOCKED``: at least one envelope failed reconciliation.
    """

    if not envelopes:
        return ReconciliationOutcome(
            status="PRE_EXECUTION_AUTHORIZED",
            matched=(),
            undeclared=(),
            surface_mismatches=(),
            bootstrap_exceptions=(),
            missing_evidence=True,
            blocking_reasons=("missing_execution_evidence",),
        )

    matched: list[dict[str, Any]] = []
    undeclared: list[str] = []
    surface_mismatches: list[str] = []
    bootstrap_exceptions: list[str] = []
    blocking_reasons: list[str] = []

    for envelope in envelopes:
        requested = canonical_command(envelope.command)
        errors = reconcile_command(plan, envelope)
        if not errors:
            is_bootstrap = _is_bootstrap_exception(plan, envelope)
            if is_bootstrap:
                bootstrap_exceptions.append(requested)
            matched.append({
                "command": requested,
                "execution_surface": envelope.execution_surface,
                "exit_code": envelope.exit_code,
                "bootstrap_exception": is_bootstrap,
            })
            continue
        for error in errors:
            if error.startswith("undeclared_command:"):
                undeclared.append(requested)
            elif error.startswith("execution_surface_mismatch:"):
                surface_mismatches.append(requested)
            blocking_reasons.append(error)

    status = "POST_EXECUTION_RECONCILED" if not blocking_reasons else "BLOCKED"
    return ReconciliationOutcome(
        status=status,
        matched=tuple(matched),
        undeclared=tuple(dict.fromkeys(undeclared)),
        surface_mismatches=tuple(dict.fromkeys(surface_mismatches)),
        bootstrap_exceptions=tuple(dict.fromkeys(bootstrap_exceptions)),
        missing_evidence=False,
        blocking_reasons=tuple(dict.fromkeys(blocking_reasons)),
    )


def _is_bootstrap_exception(plan: TransitionCommandPlan, envelope: ExecutionEnvelope) -> bool:
    if envelope.bootstrap_exception:
        return True
    requested = canonical_command(envelope.command)
    for entry in plan.commands:
        if canonical_command(entry.command) == requested and entry.execution_surface == envelope.execution_surface:
            return entry.bootstrap_exception
    return False
