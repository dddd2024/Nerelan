"""Provider-free normalization and conservative classification of PR feedback.

Feedback is external observation, never execution authority.  This module
intentionally contains no GitHub transport, persistence, model calls, or side
effects; adapters may normalize observations here before later reconciliation.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

MAX_FEEDBACK_INPUT_CHARS = 100_000
MAX_FEEDBACK_EXCERPT_CHARS = 2_000
MAX_SOURCE_IDENTITY_CHARS = 256
MAX_PATH_CHARS = 1_024

_REPOSITORY_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9_.-]{1,100}$"
)
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ACTION_RE = re.compile(
    r"\b(?:fix|change|update|replace|remove|add|rename|adjust|refactor|correct|"
    r"rewrite|handle|guard|assert|test)\b",
    re.IGNORECASE,
)
_TEST_TEXT_RE = re.compile(
    r"\b(?:test|tests|testing|spec|specs|fixture|fixtures|assertion|assertions|"
    r"pytest|playwright)\b",
    re.IGNORECASE,
)
_QUESTION_RE = re.compile(
    r"(?:\?\s*$)|"
    r"(?:^\s*(?:why|what|when|where|who|how|is|are|do|does|did|can|could|"
    r"would|should)\b)|"
    r"(?:\b(?:please\s+clarify|need\s+clarification|can\s+you\s+clarify|"
    r"could\s+you\s+clarify)\b)",
    re.IGNORECASE,
)

_FAILED_CHECK_CONCLUSIONS = frozenset(
    {
        "FAILURE",
        "TIMED_OUT",
        "CANCELLED",
        "ACTION_REQUIRED",
        "STARTUP_FAILURE",
        "STALE",
    }
)
_SUCCESS_CHECK_CONCLUSIONS = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
_ACKNOWLEDGEMENTS = frozenset(
    {
        "ack",
        "acknowledged",
        "approved",
        "done",
        "fixed",
        "good",
        "looks good",
        "lgtm",
        "no change needed",
        "no changes needed",
        "no fix needed",
        "resolved",
        "thanks",
        "thank you",
        "works for me",
    }
)


class FeedbackValidationError(ValueError):
    """A malformed feedback observation that cannot be bound safely."""


class FeedbackSource(StrEnum):
    REVIEW_THREAD = "REVIEW_THREAD"
    PR_COMMENT = "PR_COMMENT"
    CI_CHECK = "CI_CHECK"
    SECURITY_CHECK = "SECURITY_CHECK"
    OWNER_REQUEST = "OWNER_REQUEST"


class FeedbackTrustClass(StrEnum):
    UNTRUSTED_EXTERNAL = "UNTRUSTED_EXTERNAL"
    OWNER_INPUT = "OWNER_INPUT"


class FeedbackResolutionState(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ADDRESSING = "ADDRESSING"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    STALE = "STALE"


class FeedbackCategory(StrEnum):
    ACTIONABLE_CODE_CHANGE = "ACTIONABLE_CODE_CHANGE"
    ACTIONABLE_TEST_CHANGE = "ACTIONABLE_TEST_CHANGE"
    QUESTION_OR_CLARIFICATION = "QUESTION_OR_CLARIFICATION"
    NON_ACTIONABLE = "NON_ACTIONABLE"
    STALE_CONTEXT = "STALE_CONTEXT"


@dataclass(frozen=True, slots=True)
class FeedbackItem:
    feedback_id: str
    repository: str
    pr_number: int
    observed_head_sha: str
    source: FeedbackSource
    source_identity: str
    content_digest_sha256: str
    content_excerpt: str
    trust_class: FeedbackTrustClass
    path: str | None = None
    line: int | None = None
    check_name: str | None = None
    check_conclusion: str | None = None
    severity: str | None = None
    resolution_state: FeedbackResolutionState = FeedbackResolutionState.OPEN

    @classmethod
    def from_observation(
        cls,
        *,
        repository: str,
        pr_number: int,
        observed_head_sha: str,
        source: FeedbackSource | str,
        source_identity: str,
        content: str = "",
        path: str | None = None,
        line: int | None = None,
        check_name: str | None = None,
        check_conclusion: str | None = None,
        severity: str | None = None,
        resolution_state: FeedbackResolutionState | str = FeedbackResolutionState.OPEN,
    ) -> "FeedbackItem":
        repository = _validate_repository(repository)
        pr_number = _validate_pr_number(pr_number)
        observed_head_sha = _validate_sha(observed_head_sha)
        source = _coerce_enum(FeedbackSource, source, "source")
        source_identity = _bounded_printable(source_identity, MAX_SOURCE_IDENTITY_CHARS, "source_identity")
        normalized_content = _normalize_content(content)
        content_digest = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
        content_excerpt = _sanitize_excerpt(normalized_content)
        path = _normalize_path(path)
        line = _normalize_line(line)
        check_name = _optional_printable(check_name, 256, "check_name")
        check_conclusion = _optional_token(check_conclusion, 64, "check_conclusion")
        severity = _optional_token(severity, 64, "severity")
        resolution_state = _coerce_enum(
            FeedbackResolutionState, resolution_state, "resolution_state"
        )
        trust_class = (
            FeedbackTrustClass.OWNER_INPUT
            if source is FeedbackSource.OWNER_REQUEST
            else FeedbackTrustClass.UNTRUSTED_EXTERNAL
        )
        identity_payload: dict[str, Any] = {
            "v": 1,
            "repository": repository.casefold(),
            "pr_number": pr_number,
            "observed_head_sha": observed_head_sha,
            "source": source.value,
            "source_identity": source_identity,
            "content_digest_sha256": content_digest,
            "path": path,
            "line": line,
            "check_name": check_name,
            "check_conclusion": check_conclusion,
            "severity": severity,
        }
        feedback_id = hashlib.sha256(
            json.dumps(
                identity_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        return cls(
            feedback_id=feedback_id,
            repository=repository,
            pr_number=pr_number,
            observed_head_sha=observed_head_sha,
            source=source,
            source_identity=source_identity,
            content_digest_sha256=content_digest,
            content_excerpt=content_excerpt,
            trust_class=trust_class,
            path=path,
            line=line,
            check_name=check_name,
            check_conclusion=check_conclusion,
            severity=severity,
            resolution_state=resolution_state,
        )


@dataclass(frozen=True, slots=True)
class FeedbackClassification:
    category: FeedbackCategory
    reason: str
    grants_authority: bool = field(default=False, init=False)


def classify_feedback(
    item: FeedbackItem,
    *,
    current_head_sha: str,
) -> FeedbackClassification:
    """Classify one observation without granting or inferring authority."""

    if not isinstance(item, FeedbackItem):
        raise FeedbackValidationError("invalid_feedback_item")
    current_head_sha = _validate_sha(current_head_sha)

    if current_head_sha != item.observed_head_sha:
        return FeedbackClassification(
            FeedbackCategory.STALE_CONTEXT,
            "observed_head_is_stale",
        )

    if item.source in (FeedbackSource.CI_CHECK, FeedbackSource.SECURITY_CHECK):
        if item.check_conclusion in _FAILED_CHECK_CONCLUSIONS:
            return FeedbackClassification(
                FeedbackCategory.ACTIONABLE_CODE_CHANGE,
                "failed_check_requires_correction",
            )
        if item.check_conclusion in _SUCCESS_CHECK_CONCLUSIONS:
            return FeedbackClassification(
                FeedbackCategory.NON_ACTIONABLE,
                "check_did_not_fail",
            )

    text = item.content_excerpt.strip()
    if not text:
        return FeedbackClassification(
            FeedbackCategory.NON_ACTIONABLE,
            "empty_feedback",
        )

    if _is_acknowledgement(text):
        return FeedbackClassification(
            FeedbackCategory.NON_ACTIONABLE,
            "acknowledgement_only",
        )

    if _ACTION_RE.search(text):
        if _is_test_path(item.path) or _TEST_TEXT_RE.search(text):
            return FeedbackClassification(
                FeedbackCategory.ACTIONABLE_TEST_CHANGE,
                "explicit_test_change_request",
            )
        return FeedbackClassification(
            FeedbackCategory.ACTIONABLE_CODE_CHANGE,
            "explicit_code_change_request",
        )

    if _QUESTION_RE.search(text):
        return FeedbackClassification(
            FeedbackCategory.QUESTION_OR_CLARIFICATION,
            "clarification_requested",
        )

    return FeedbackClassification(
        FeedbackCategory.NON_ACTIONABLE,
        "ambiguous_feedback",
    )


def _validate_repository(value: str) -> str:
    if not isinstance(value, str):
        raise FeedbackValidationError("invalid_repository")
    value = value.strip()
    if not _REPOSITORY_RE.fullmatch(value):
        raise FeedbackValidationError("invalid_repository")
    owner, name = value.split("/", 1)
    if owner in {".", ".."} or name in {".", ".."}:
        raise FeedbackValidationError("invalid_repository")
    return value


def _validate_pr_number(value: int) -> int:
    if type(value) is not int or value <= 0:
        raise FeedbackValidationError("invalid_pr_number")
    return value


def _validate_sha(value: str) -> str:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise FeedbackValidationError("invalid_head_sha")
    return value


def _coerce_enum(enum_type: type[StrEnum], value: StrEnum | str, field_name: str) -> Any:
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise FeedbackValidationError(f"invalid_{field_name}") from exc


def _bounded_printable(value: str, maximum: int, field_name: str) -> str:
    if not isinstance(value, str):
        raise FeedbackValidationError(f"invalid_{field_name}")
    value = unicodedata.normalize("NFC", value.strip())
    if not 1 <= len(value) <= maximum:
        raise FeedbackValidationError(f"invalid_{field_name}")
    if any(unicodedata.category(char).startswith("C") for char in value):
        raise FeedbackValidationError(f"invalid_{field_name}")
    return value


def _optional_printable(value: str | None, maximum: int, field_name: str) -> str | None:
    if value is None:
        return None
    return _bounded_printable(value, maximum, field_name)


def _optional_token(value: str | None, maximum: int, field_name: str) -> str | None:
    if value is None:
        return None
    normalized = _bounded_printable(value, maximum, field_name)
    return re.sub(r"[\s-]+", "_", normalized).upper()


def _normalize_content(value: str) -> str:
    if not isinstance(value, str) or len(value) > MAX_FEEDBACK_INPUT_CHARS:
        raise FeedbackValidationError("invalid_content")
    return unicodedata.normalize(
        "NFC",
        value.replace("\r\n", "\n").replace("\r", "\n"),
    )


def _sanitize_excerpt(value: str) -> str:
    safe = "".join(
        char
        for char in value
        if char in {"\n", "\t"} or not unicodedata.category(char).startswith("C")
    )
    return safe[:MAX_FEEDBACK_EXCERPT_CHARS]


def _normalize_path(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise FeedbackValidationError("invalid_path")
    value = unicodedata.normalize("NFC", value.strip())
    if not 1 <= len(value) <= MAX_PATH_CHARS:
        raise FeedbackValidationError("invalid_path")
    if value.startswith("/") or "\\" in value or "//" in value:
        raise FeedbackValidationError("invalid_path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise FeedbackValidationError("invalid_path")
    if any(unicodedata.category(char).startswith("C") for char in value):
        raise FeedbackValidationError("invalid_path")
    return value


def _normalize_line(value: int | None) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value <= 0:
        raise FeedbackValidationError("invalid_line")
    return value


def _is_acknowledgement(text: str) -> bool:
    normalized = re.sub(r"[.!]+$", "", text.strip().casefold())
    return normalized in _ACKNOWLEDGEMENTS


def _is_test_path(path: str | None) -> bool:
    if path is None:
        return False
    lowered = path.casefold()
    name = lowered.rsplit("/", 1)[-1]
    return (
        lowered.startswith("tests/")
        or "/tests/" in lowered
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".spec.ts")
        or name.endswith(".spec.tsx")
        or name.endswith(".test.ts")
        or name.endswith(".test.tsx")
    )
