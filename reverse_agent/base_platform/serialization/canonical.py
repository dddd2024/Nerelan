"""Deterministic canonical JSON serialization and SHA-256 digests."""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from collections.abc import Mapping, Sequence, Set
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from ..errors import fail


@runtime_checkable
class CanonicalDataProvider(Protocol):
    def to_canonical_data(self) -> Any: ...


def _normalized_text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def canonical_data(value: Any) -> Any:
    """Convert supported values to a deterministic JSON-compatible form."""

    if isinstance(value, CanonicalDataProvider):
        return canonical_data(value.to_canonical_data())
    if isinstance(value, Enum):
        return canonical_data(value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return canonical_data({field.name: getattr(value, field.name) for field in fields(value)})
    if isinstance(value, Mapping):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                fail("NON_STRING_MAPPING_KEY", "Canonical mappings require string keys.")
            normalized_key = _normalized_text(key)
            if normalized_key in converted:
                fail("DUPLICATE_NORMALIZED_KEY", "Mapping keys collide after Unicode normalization.", key=key)
            converted[normalized_key] = canonical_data(item)
        return {key: converted[key] for key in sorted(converted)}
    if isinstance(value, Set) and not isinstance(value, (str, bytes, bytearray)):
        converted_items = [canonical_data(item) for item in value]
        return sorted(converted_items, key=_canonical_sort_key)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [canonical_data(item) for item in value]
    if isinstance(value, str):
        return _normalized_text(value)
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            fail("NON_FINITE_NUMBER", "Canonical JSON rejects NaN and infinity.")
        return value
    fail("UNSUPPORTED_CANONICAL_TYPE", "Value cannot be represented as canonical JSON.", type=type(value).__name__)


def _canonical_sort_key(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        canonical_data(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
