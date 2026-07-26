"""Versioned SpecPackage and deterministic Policy Resolver core."""

from .compatibility import ADAPTER_VERSION, CompatibilitySnapshot, ReadOnlyCompatibilityAdapter
from .contracts import (
    PUBLICATION_BRANCH_AND_DRAFT_PR,
    PUBLICATION_DENIED,
    SCHEMA_VERSION,
    AcceptanceResult,
    AgentTask,
    CapabilityManifest,
    ExecutionEnvelope,
    FailureEnvelope,
    GoalContract,
    NaturalLanguageRequest,
    ResolvedExecutionPolicy,
    RetryPolicy,
    SpecPackage,
    TaskSubmission,
    VersionedContract,
)
from .errors import BasePlatformError
from .policy import RESOLVER_VERSION, PolicyResolver, resolve_policy
from .serialization import canonical_data, canonical_digest, canonical_json, canonical_json_bytes

__all__ = [
    "ADAPTER_VERSION",
    "PUBLICATION_BRANCH_AND_DRAFT_PR",
    "PUBLICATION_DENIED",
    "RESOLVER_VERSION",
    "SCHEMA_VERSION",
    "AcceptanceResult",
    "AgentTask",
    "BasePlatformError",
    "CapabilityManifest",
    "CompatibilitySnapshot",
    "ExecutionEnvelope",
    "FailureEnvelope",
    "GoalContract",
    "NaturalLanguageRequest",
    "PolicyResolver",
    "ReadOnlyCompatibilityAdapter",
    "ResolvedExecutionPolicy",
    "RetryPolicy",
    "SpecPackage",
    "TaskSubmission",
    "VersionedContract",
    "canonical_data",
    "canonical_digest",
    "canonical_json",
    "canonical_json_bytes",
    "resolve_policy",
]
