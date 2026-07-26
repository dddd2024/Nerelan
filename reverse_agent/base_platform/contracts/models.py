"""Versioned typed contracts for the executable base-platform boundary."""

from __future__ import annotations

from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, Self

from ..errors import fail


SCHEMA_VERSION = "0.1"
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})
PUBLICATION_DENIED = "denied"
PUBLICATION_BRANCH_AND_DRAFT_PR = "branch_and_draft_pr"
PUBLICATION_MERGE = "merge"
SUPPORTED_PUBLICATION_PERMISSIONS = frozenset(
    {PUBLICATION_DENIED, PUBLICATION_BRANCH_AND_DRAFT_PR}
)


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail("INVALID_FIELD", "Expected a non-empty string.", field=field_name)
    return value.strip()


def _bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        fail("INVALID_FIELD", "Expected a boolean.", field=field_name)
    return value


def _integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        fail("INVALID_FIELD", "Expected an integer within bounds.", field=field_name, minimum=minimum)
    return value


def _strings(
    value: object,
    field_name: str,
    *,
    ordered: bool = False,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        fail("INVALID_FIELD", "Expected a collection of strings.", field=field_name)
    items = tuple(_text(item, field_name) for item in value)
    if not allow_empty and not items:
        fail("INVALID_FIELD", "Collection cannot be empty.", field=field_name)
    return items if ordered else tuple(sorted(set(items)))


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    fail("INVALID_FIELD", "Mapping contains a non-JSON-compatible value.", type=type(value).__name__)


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        fail("INVALID_FIELD", "Expected a mapping.", field=field_name)
    if any(not isinstance(key, str) for key in value):
        fail("INVALID_FIELD", "Mapping keys must be strings.", field=field_name)
    return _freeze_json(value)


def _expect_schema(payload: Mapping[str, Any]) -> None:
    version = payload.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        fail(
            "UNSUPPORTED_SCHEMA_VERSION",
            "The protocol schema version is not supported.",
            schema_version=version,
        )


def _contract(payload: object, field_name: str, contract_type: type["VersionedContract"]) -> Any:
    if isinstance(payload, contract_type):
        return payload
    if not isinstance(payload, Mapping):
        fail("INVALID_FIELD", "Expected a versioned contract mapping.", field=field_name)
    return contract_type.from_mapping(payload)


@dataclass(frozen=True, kw_only=True)
class VersionedContract:
    """Base for all externally stored or transferred M1 protocol objects."""

    identity: str
    schema_version: str = SCHEMA_VERSION
    CONTRACT_TYPE: ClassVar[str] = "VersionedContract"

    def __post_init__(self) -> None:
        object.__setattr__(self, "identity", _text(self.identity, "identity"))
        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            fail(
                "UNSUPPORTED_SCHEMA_VERSION",
                "The protocol schema version is not supported.",
                schema_version=self.schema_version,
            )

    def to_canonical_data(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "contract_type": self.CONTRACT_TYPE,
            "schema_version": self.schema_version,
        }
        for field in fields(self):
            if field.name != "schema_version":
                result[field.name] = getattr(self, field.name)
        return result

    def to_dict(self) -> dict[str, Any]:
        from ..serialization import canonical_data

        return canonical_data(self.to_canonical_data())

    def canonical_bytes(self) -> bytes:
        from ..serialization import canonical_json_bytes

        return canonical_json_bytes(self)

    def digest(self) -> str:
        from ..serialization import canonical_digest

        return canonical_digest(self)

    @classmethod
    def _base_values(cls, payload: Mapping[str, Any]) -> dict[str, Any]:
        _expect_schema(payload)
        contract_type = payload.get("contract_type")
        if contract_type not in (None, cls.CONTRACT_TYPE):
            fail(
                "CONTRACT_TYPE_MISMATCH",
                "The serialized contract type does not match the requested type.",
                expected=cls.CONTRACT_TYPE,
                actual=contract_type,
            )
        return {
            "identity": _text(payload.get("identity"), "identity"),
            "schema_version": str(payload["schema_version"]),
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(**cls._base_values(payload))


@dataclass(frozen=True, kw_only=True)
class NaturalLanguageRequest(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "NaturalLanguageRequest"
    text: str
    requested_operations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "text", _text(self.text, "text"))
        object.__setattr__(
            self,
            "requested_operations",
            _strings(self.requested_operations, "requested_operations"),
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(
            **cls._base_values(payload),
            text=_text(payload.get("text"), "text"),
            requested_operations=_strings(payload.get("requested_operations", ()), "requested_operations"),
        )


@dataclass(frozen=True, kw_only=True)
class GoalContract(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "GoalContract"
    objective: str
    acceptance_criteria: tuple[str, ...]
    required_checks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "objective", _text(self.objective, "objective"))
        object.__setattr__(
            self,
            "acceptance_criteria",
            _strings(self.acceptance_criteria, "acceptance_criteria", ordered=True, allow_empty=False),
        )
        object.__setattr__(self, "required_checks", _strings(self.required_checks, "required_checks"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(
            **cls._base_values(payload),
            objective=_text(payload.get("objective"), "objective"),
            acceptance_criteria=_strings(
                payload.get("acceptance_criteria"),
                "acceptance_criteria",
                ordered=True,
                allow_empty=False,
            ),
            required_checks=_strings(payload.get("required_checks", ()), "required_checks"),
        )


@dataclass(frozen=True, kw_only=True)
class RetryPolicy(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "RetryPolicy"
    max_attempts: int = 1
    retryable_error_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "max_attempts", _integer(self.max_attempts, "max_attempts", minimum=1))
        object.__setattr__(
            self,
            "retryable_error_codes",
            _strings(self.retryable_error_codes, "retryable_error_codes"),
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(
            **cls._base_values(payload),
            max_attempts=_integer(payload.get("max_attempts", 1), "max_attempts", minimum=1),
            retryable_error_codes=_strings(
                payload.get("retryable_error_codes", ()),
                "retryable_error_codes",
            ),
        )


@dataclass(frozen=True, kw_only=True)
class SpecPackage(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "SpecPackage"
    request: NaturalLanguageRequest
    goal: GoalContract
    approved: bool
    approval_identity: str
    requested_risk_tier: str
    allowed_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...] = ()
    required_operations: tuple[str, ...] = ()
    required_approval: str = "approved_spec"
    required_checks: tuple[str, ...] = ()
    requested_retry_policy: RetryPolicy | None = None
    requested_publication_permission: str = PUBLICATION_DENIED

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "request", _contract(self.request, "request", NaturalLanguageRequest))
        object.__setattr__(self, "goal", _contract(self.goal, "goal", GoalContract))
        object.__setattr__(self, "approved", _bool(self.approved, "approved"))
        object.__setattr__(self, "approval_identity", _text(self.approval_identity, "approval_identity"))
        object.__setattr__(self, "requested_risk_tier", _text(self.requested_risk_tier, "requested_risk_tier").upper())
        object.__setattr__(self, "allowed_operations", _strings(self.allowed_operations, "allowed_operations"))
        object.__setattr__(
            self,
            "forbidden_operations",
            _strings(self.forbidden_operations, "forbidden_operations"),
        )
        object.__setattr__(
            self,
            "required_operations",
            _strings(self.required_operations, "required_operations"),
        )
        object.__setattr__(self, "required_approval", _text(self.required_approval, "required_approval"))
        object.__setattr__(self, "required_checks", _strings(self.required_checks, "required_checks"))
        retry_policy = self.requested_retry_policy or RetryPolicy(identity=f"{self.identity}:retry")
        object.__setattr__(
            self,
            "requested_retry_policy",
            _contract(retry_policy, "requested_retry_policy", RetryPolicy),
        )
        permission = _text(
            self.requested_publication_permission,
            "requested_publication_permission",
        )
        if permission == PUBLICATION_MERGE or permission not in SUPPORTED_PUBLICATION_PERMISSIONS:
            fail(
                "UNSUPPORTED_PUBLICATION_PERMISSION",
                "The requested publication permission is not supported.",
                permission=permission,
            )
        object.__setattr__(self, "requested_publication_permission", permission)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        values = cls._base_values(payload)
        retry_payload = payload.get("requested_retry_policy")
        return cls(
            **values,
            request=_contract(payload.get("request"), "request", NaturalLanguageRequest),
            goal=_contract(payload.get("goal"), "goal", GoalContract),
            approved=_bool(payload.get("approved"), "approved"),
            approval_identity=_text(payload.get("approval_identity"), "approval_identity"),
            requested_risk_tier=_text(payload.get("requested_risk_tier"), "requested_risk_tier"),
            allowed_operations=_strings(payload.get("allowed_operations", ()), "allowed_operations"),
            forbidden_operations=_strings(payload.get("forbidden_operations", ()), "forbidden_operations"),
            required_operations=_strings(payload.get("required_operations", ()), "required_operations"),
            required_approval=_text(payload.get("required_approval", "approved_spec"), "required_approval"),
            required_checks=_strings(payload.get("required_checks", ()), "required_checks"),
            requested_retry_policy=(
                _contract(retry_payload, "requested_retry_policy", RetryPolicy)
                if retry_payload is not None
                else None
            ),
            requested_publication_permission=_text(
                payload.get("requested_publication_permission", PUBLICATION_DENIED),
                "requested_publication_permission",
            ),
        )


@dataclass(frozen=True, kw_only=True)
class CapabilityManifest(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "CapabilityManifest"
    supported_operations: tuple[str, ...]
    supported_risk_tiers: tuple[str, ...]
    required_checks: tuple[str, ...] = ()
    publication_permissions: tuple[str, ...] = (PUBLICATION_DENIED,)
    max_retry_attempts: int = 1

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(
            self,
            "supported_operations",
            _strings(self.supported_operations, "supported_operations"),
        )
        tiers = tuple(
            sorted(
                set(
                    item.upper()
                    for item in _strings(self.supported_risk_tiers, "supported_risk_tiers")
                )
            )
        )
        if any(tier not in {"R0", "R1", "R2", "R3"} for tier in tiers):
            fail("INVALID_RISK_TIER", "Capability manifest contains an invalid risk tier.")
        object.__setattr__(self, "supported_risk_tiers", tiers)
        object.__setattr__(self, "required_checks", _strings(self.required_checks, "required_checks"))
        permissions = _strings(self.publication_permissions, "publication_permissions")
        if any(permission not in SUPPORTED_PUBLICATION_PERMISSIONS for permission in permissions):
            fail(
                "UNSUPPORTED_PUBLICATION_PERMISSION",
                "Capability manifest contains an unsupported publication permission.",
            )
        object.__setattr__(self, "publication_permissions", permissions)
        object.__setattr__(
            self,
            "max_retry_attempts",
            _integer(self.max_retry_attempts, "max_retry_attempts", minimum=1),
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(
            **cls._base_values(payload),
            supported_operations=_strings(payload.get("supported_operations", ()), "supported_operations"),
            supported_risk_tiers=_strings(payload.get("supported_risk_tiers", ()), "supported_risk_tiers"),
            required_checks=_strings(payload.get("required_checks", ()), "required_checks"),
            publication_permissions=_strings(
                payload.get("publication_permissions", (PUBLICATION_DENIED,)),
                "publication_permissions",
            ),
            max_retry_attempts=_integer(
                payload.get("max_retry_attempts", 1),
                "max_retry_attempts",
                minimum=1,
            ),
        )


@dataclass(frozen=True, kw_only=True)
class ResolvedExecutionPolicy(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "ResolvedExecutionPolicy"
    risk_tier: str
    allowed_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    required_approval: str
    required_checks: tuple[str, ...]
    retry_policy: RetryPolicy
    publication_permission: str
    source_spec_identity: str
    capability_manifest_identity: str
    resolver_version: str
    canonical_input_digest: str

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "risk_tier", _text(self.risk_tier, "risk_tier").upper())
        object.__setattr__(self, "allowed_operations", _strings(self.allowed_operations, "allowed_operations"))
        object.__setattr__(
            self,
            "forbidden_operations",
            _strings(self.forbidden_operations, "forbidden_operations"),
        )
        object.__setattr__(self, "required_approval", _text(self.required_approval, "required_approval"))
        object.__setattr__(self, "required_checks", _strings(self.required_checks, "required_checks"))
        object.__setattr__(self, "retry_policy", _contract(self.retry_policy, "retry_policy", RetryPolicy))
        if self.publication_permission not in SUPPORTED_PUBLICATION_PERMISSIONS:
            fail(
                "UNSUPPORTED_PUBLICATION_PERMISSION",
                "Resolved policy contains an unsupported publication permission.",
            )
        for field_name in (
            "source_spec_identity",
            "capability_manifest_identity",
            "resolver_version",
            "canonical_input_digest",
        ):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(
            **cls._base_values(payload),
            risk_tier=_text(payload.get("risk_tier"), "risk_tier"),
            allowed_operations=_strings(payload.get("allowed_operations", ()), "allowed_operations"),
            forbidden_operations=_strings(payload.get("forbidden_operations", ()), "forbidden_operations"),
            required_approval=_text(payload.get("required_approval"), "required_approval"),
            required_checks=_strings(payload.get("required_checks", ()), "required_checks"),
            retry_policy=_contract(payload.get("retry_policy"), "retry_policy", RetryPolicy),
            publication_permission=_text(payload.get("publication_permission"), "publication_permission"),
            source_spec_identity=_text(payload.get("source_spec_identity"), "source_spec_identity"),
            capability_manifest_identity=_text(
                payload.get("capability_manifest_identity"),
                "capability_manifest_identity",
            ),
            resolver_version=_text(payload.get("resolver_version"), "resolver_version"),
            canonical_input_digest=_text(
                payload.get("canonical_input_digest"),
                "canonical_input_digest",
            ),
        )


@dataclass(frozen=True, kw_only=True)
class ExecutionEnvelope(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "ExecutionEnvelope"
    policy: ResolvedExecutionPolicy
    task_identity: str
    attempt: int = 1

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "policy", _contract(self.policy, "policy", ResolvedExecutionPolicy))
        object.__setattr__(self, "task_identity", _text(self.task_identity, "task_identity"))
        object.__setattr__(self, "attempt", _integer(self.attempt, "attempt", minimum=1))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(
            **cls._base_values(payload),
            policy=_contract(payload.get("policy"), "policy", ResolvedExecutionPolicy),
            task_identity=_text(payload.get("task_identity"), "task_identity"),
            attempt=_integer(payload.get("attempt", 1), "attempt", minimum=1),
        )


@dataclass(frozen=True, kw_only=True)
class AgentTask(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "AgentTask"
    operation: str
    parameters: Mapping[str, Any]

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "operation", _text(self.operation, "operation"))
        object.__setattr__(self, "parameters", _mapping(self.parameters, "parameters"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(
            **cls._base_values(payload),
            operation=_text(payload.get("operation"), "operation"),
            parameters=_mapping(payload.get("parameters", {}), "parameters"),
        )


@dataclass(frozen=True, kw_only=True)
class TaskSubmission(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "TaskSubmission"
    task: AgentTask
    envelope: ExecutionEnvelope

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "task", _contract(self.task, "task", AgentTask))
        object.__setattr__(self, "envelope", _contract(self.envelope, "envelope", ExecutionEnvelope))
        if self.task.identity != self.envelope.task_identity:
            fail(
                "TASK_IDENTITY_MISMATCH",
                "Submission task identity does not match its execution envelope.",
            )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(
            **cls._base_values(payload),
            task=_contract(payload.get("task"), "task", AgentTask),
            envelope=_contract(payload.get("envelope"), "envelope", ExecutionEnvelope),
        )


@dataclass(frozen=True, kw_only=True)
class FailureEnvelope(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "FailureEnvelope"
    error_code: str
    message: str
    retryable: bool = False
    details: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "error_code", _text(self.error_code, "error_code"))
        object.__setattr__(self, "message", _text(self.message, "message"))
        object.__setattr__(self, "retryable", _bool(self.retryable, "retryable"))
        object.__setattr__(self, "details", _mapping(self.details or {}, "details"))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(
            **cls._base_values(payload),
            error_code=_text(payload.get("error_code"), "error_code"),
            message=_text(payload.get("message"), "message"),
            retryable=_bool(payload.get("retryable", False), "retryable"),
            details=_mapping(payload.get("details", {}), "details"),
        )


@dataclass(frozen=True, kw_only=True)
class AcceptanceResult(VersionedContract):
    CONTRACT_TYPE: ClassVar[str] = "AcceptanceResult"
    accepted: bool
    check_results: Mapping[str, bool]
    failure_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "accepted", _bool(self.accepted, "accepted"))
        results = _mapping(self.check_results, "check_results")
        if any(not isinstance(value, bool) for value in results.values()):
            fail("INVALID_FIELD", "Check results must be booleans.", field="check_results")
        object.__setattr__(self, "check_results", results)
        object.__setattr__(self, "failure_codes", _strings(self.failure_codes, "failure_codes"))
        if self.accepted != (all(results.values()) and not self.failure_codes):
            fail(
                "ACCEPTANCE_RESULT_INCONSISTENT",
                "Acceptance flag must match check results and failure codes.",
            )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Self:
        return cls(
            **cls._base_values(payload),
            accepted=_bool(payload.get("accepted"), "accepted"),
            check_results=_mapping(payload.get("check_results", {}), "check_results"),
            failure_codes=_strings(payload.get("failure_codes", ()), "failure_codes"),
        )
