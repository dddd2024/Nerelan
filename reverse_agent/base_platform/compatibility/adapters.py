"""Read-only, versioned, fail-closed, non-authoritative compatibility."""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from ..contracts import SCHEMA_VERSION, VersionedContract
from ..errors import fail
from ..serialization import canonical_json_bytes


ADAPTER_VERSION = "0.1"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, kw_only=True)
class CompatibilitySnapshot(VersionedContract):
    CONTRACT_TYPE = "CompatibilitySnapshot"
    adapter_version: str
    source_type: str
    source_identity: str
    payload: Mapping[str, Any]
    authoritative: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.adapter_version or not self.source_type or not self.source_identity:
            fail("INVALID_COMPATIBILITY_SOURCE", "Compatibility source metadata is incomplete.")
        if self.authoritative:
            fail(
                "COMPATIBILITY_CANNOT_AUTHORIZE",
                "Compatibility snapshots are always non-authoritative.",
            )
        frozen_copy = _freeze(json.loads(canonical_json_bytes(self.payload)))
        object.__setattr__(self, "payload", frozen_copy)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CompatibilitySnapshot":
        values = cls._base_values(payload)
        source_payload = payload.get("payload")
        if not isinstance(source_payload, Mapping):
            fail("INVALID_FIELD", "Compatibility payload must be a mapping.", field="payload")
        authoritative = payload.get("authoritative", False)
        if not isinstance(authoritative, bool):
            fail("INVALID_FIELD", "Authoritative must be a boolean.", field="authoritative")
        return cls(
            **values,
            adapter_version=str(payload.get("adapter_version", "")),
            source_type=str(payload.get("source_type", "")),
            source_identity=str(payload.get("source_identity", "")),
            payload=source_payload,
            authoritative=authoritative,
        )


@dataclass(frozen=True)
class ReadOnlyCompatibilityAdapter:
    """Copy selected legacy mappings without granting execution authority."""

    adapter_version: str = ADAPTER_VERSION
    supported_source_schema_versions: frozenset[int | str] = frozenset({1, SCHEMA_VERSION})

    def adapt(
        self,
        source: Mapping[str, Any],
        *,
        source_type: str,
        source_identity: str,
    ) -> CompatibilitySnapshot:
        if not isinstance(source, Mapping):
            fail("INVALID_COMPATIBILITY_SOURCE", "Compatibility input must be a mapping.")
        source_schema = source.get("schema_version")
        if source_schema not in self.supported_source_schema_versions:
            fail(
                "UNSUPPORTED_COMPATIBILITY_VERSION",
                "Compatibility source schema is not supported.",
                schema_version=source_schema,
            )
        return CompatibilitySnapshot(
            identity=f"compat:{self.adapter_version}:{source_type}:{source_identity}",
            adapter_version=self.adapter_version,
            source_type=source_type,
            source_identity=source_identity,
            payload=source,
            authoritative=False,
        )
