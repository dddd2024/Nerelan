"""Independent authority kernel for control-plane transition rounds."""

from .command_authority import authorize_command, canonical_command, validate_command_plan
from .models import (
    ExecutionEnvelope,
    TransitionAuthority,
    TransitionCommand,
    TransitionCommandPlan,
    TransitionDecision,
    TransitionPreflightResult,
)
from .transition import validate_transition

__all__ = [
    "ExecutionEnvelope",
    "TransitionAuthority",
    "TransitionCommand",
    "TransitionCommandPlan",
    "TransitionDecision",
    "TransitionPreflightResult",
    "authorize_command",
    "canonical_command",
    "validate_command_plan",
    "validate_transition",
]
