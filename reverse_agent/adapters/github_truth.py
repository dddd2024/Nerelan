"""Provenanced GitHub observations that never replace GitHub truth."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


def _required(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing_or_invalid:{name}")
    return value.strip()


@dataclass(frozen=True)
class GitHubTruthObservation:
    repository: str
    observation_kind: str
    subject_ref: str
    head_sha: str
    source: str
    observed_at: str
    schema_version: int = 1

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "GitHubTruthObservation":
        if payload.get("schema_version") != 1:
            raise ValueError("unsupported_schema_version")
        observed_at = _required(payload.get("observed_at"), "observed_at")
        parsed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("observed_at_must_include_timezone")
        head_sha = _required(payload.get("head_sha"), "head_sha").lower()
        if len(head_sha) != 40 or any(char not in "0123456789abcdef" for char in head_sha):
            raise ValueError("missing_or_invalid:head_sha")
        return cls(
            repository=_required(payload.get("repository"), "repository"),
            observation_kind=_required(payload.get("observation_kind"), "observation_kind"),
            subject_ref=_required(payload.get("subject_ref"), "subject_ref"),
            head_sha=head_sha,
            source=_required(payload.get("source"), "source"),
            observed_at=observed_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository": self.repository,
            "observation_kind": self.observation_kind,
            "subject_ref": self.subject_ref,
            "head_sha": self.head_sha,
            "source": self.source,
            "observed_at": self.observed_at,
            "authority": "CACHE_OBSERVATION",
            "authoritative": False,
        }
