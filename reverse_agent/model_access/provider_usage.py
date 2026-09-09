"""Provider-neutral usage/quota contracts and provider-free parsers.

No function in this module performs network I/O or resolves credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
import math
from typing import Any, Iterable, Mapping, Sequence


class Provenance(str, Enum):
    OFFICIAL_BALANCE = "OFFICIAL_BALANCE"
    OFFICIAL_USAGE = "OFFICIAL_USAGE"
    RATE_LIMIT_HEADER = "RATE_LIMIT_HEADER"
    LOCAL_METERING = "LOCAL_METERING"
    ESTIMATED = "ESTIMATED"
    UNAVAILABLE = "UNAVAILABLE"


class ObservationState(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    AUTH_FAILED = "AUTH_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    TRANSIENT_ERROR = "TRANSIENT_ERROR"


class CredentialCapability(str, Enum):
    NONE = "NONE"
    INFERENCE = "INFERENCE"
    MANAGEMENT_USAGE = "MANAGEMENT_USAGE"
    MANAGEMENT_BILLING = "MANAGEMENT_BILLING"
    SESSION_OBSERVATION = "SESSION_OBSERVATION"


class UnavailableReason(str, Enum):
    UNSUPPORTED_PROVIDER = "UNSUPPORTED_PROVIDER"
    PROVIDER_REPORTED_UNAVAILABLE = "PROVIDER_REPORTED_UNAVAILABLE"


Scalar = Decimal | bool | str


def _public_scalar(value: Scalar | None) -> str | bool | None:
    return format(value, "f") if isinstance(value, Decimal) else value


@dataclass(frozen=True, slots=True)
class MetricObservation:
    metric_id: str
    kind: str
    unit: str
    provenance: Provenance
    state: ObservationState = ObservationState.FRESH
    value: Scalar | None = None
    used: Decimal | None = None
    limit: Decimal | None = None
    remaining: Decimal | None = None
    period_start: str | None = None
    period_end: str | None = None
    resets_at: str | None = None
    reset_after: str | None = None
    scope: str | None = None
    fetched_at: str | None = None
    confidence: str = "authoritative"

    def __post_init__(self) -> None:
        if not self.metric_id.strip() or not self.kind.strip() or not self.unit.strip():
            raise ValueError("metric_id, kind and unit are required")
        numeric_values = (self.used, self.limit, self.remaining)
        if any(
            value is not None and (not value.is_finite() or value < 0)
            for value in numeric_values
        ):
            raise ValueError("numeric observations must be finite and non-negative")
        if isinstance(self.value, Decimal) and (
            not self.value.is_finite() or self.value < 0
        ):
            raise ValueError("value must be finite and non-negative")

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "kind": self.kind,
            "unit": self.unit,
            "value": _public_scalar(self.value),
            "used": _public_scalar(self.used),
            "limit": _public_scalar(self.limit),
            "remaining": _public_scalar(self.remaining),
            "period_start": self.period_start,
            "period_end": self.period_end,
            "resets_at": self.resets_at,
            "reset_after": self.reset_after,
            "scope": self.scope,
            "provenance": self.provenance.value,
            "state": self.state.value,
            "fetched_at": self.fetched_at,
            "confidence": self.confidence,
        }


@dataclass(frozen=True, slots=True)
class ProviderUsageSnapshot:
    provider_id: str
    fetched_at: str
    observations: tuple[MetricObservation, ...] = ()
    state: ObservationState = ObservationState.FRESH
    connection_ref: str | None = None
    account_ref: str | None = None
    unavailable_reason: UnavailableReason | None = None

    def __post_init__(self) -> None:
        if not self.provider_id.strip():
            raise ValueError("provider_id is required")
        if self.state is ObservationState.UNAVAILABLE and self.unavailable_reason is None:
            raise ValueError("unavailable snapshots require an unavailable_reason")

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "connection_ref": self.connection_ref,
            "account_ref": self.account_ref,
            "fetched_at": self.fetched_at,
            "state": self.state.value,
            "unavailable_reason": (
                self.unavailable_reason.value if self.unavailable_reason else None
            ),
            "observations": [item.to_public_dict() for item in self.observations],
        }


@dataclass(frozen=True, slots=True)
class ProviderDispatch:
    provider_id: str
    protocol_family: str
    parser_ids: tuple[str, ...]
    allowed_credential_capabilities: tuple[CredentialCapability, ...]
    supported: bool
    unavailable_reason: UnavailableReason | None = None


_PROVIDER_REGISTRY = {
    ("sensetime", "openai"): ProviderDispatch(
        "sensetime",
        "openai",
        ("sensenova_usage",),
        (CredentialCapability.INFERENCE,),
        True,
    ),
    ("deepseek", "openai"): ProviderDispatch(
        "deepseek",
        "openai",
        ("deepseek_balance",),
        (CredentialCapability.INFERENCE,),
        True,
    ),
    ("openai", "openai"): ProviderDispatch(
        "openai",
        "openai",
        ("openai_rate_limits", "openai_organization_usage"),
        (
            CredentialCapability.INFERENCE,
            CredentialCapability.MANAGEMENT_USAGE,
            CredentialCapability.MANAGEMENT_BILLING,
        ),
        True,
    ),
    ("openrouter", "openai"): ProviderDispatch(
        "openrouter",
        "openai",
        (),
        (CredentialCapability.NONE,),
        False,
        UnavailableReason.UNSUPPORTED_PROVIDER,
    ),
}


def _identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip().lower()


def _protocol(value: str) -> str:
    normalized = _identifier(value, "protocol_family")
    return "openai" if normalized == "openai-compatible" else normalized


def resolve_provider_dispatch(provider_id: str, protocol_family: str) -> ProviderDispatch:
    provider = _identifier(provider_id, "provider_id")
    protocol = _protocol(protocol_family)
    return _PROVIDER_REGISTRY.get(
        (provider, protocol),
        ProviderDispatch(
            provider,
            protocol,
            (),
            (CredentialCapability.NONE,),
            False,
            UnavailableReason.UNSUPPORTED_PROVIDER,
        ),
    )


def unsupported_provider_snapshot(
    provider_id: str, *, fetched_at: str
) -> ProviderUsageSnapshot:
    return ProviderUsageSnapshot(
        provider_id=_identifier(provider_id, "provider_id"),
        fetched_at=fetched_at,
        state=ObservationState.UNAVAILABLE,
        unavailable_reason=UnavailableReason.UNSUPPORTED_PROVIDER,
    )


def _decimal(value: Any, field: str) -> Decimal:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field} must be a finite non-negative number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{field} must be finite and non-negative")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite non-negative number") from exc
    if not number.is_finite() or number < 0:
        raise ValueError(f"{field} must be finite and non-negative")
    return number


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return value


def _sequence(value: Any, field: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be an array")
    return value


def parse_deepseek_balance(
    payload: Mapping[str, Any], *, fetched_at: str
) -> ProviderUsageSnapshot:
    data = _mapping(payload, "payload")
    available = data.get("is_available")
    if not isinstance(available, bool):
        raise ValueError("is_available must be a boolean")
    infos = _sequence(data.get("balance_infos"), "balance_infos")

    observations: list[MetricObservation] = [
        MetricObservation(
            "account.available",
            "availability",
            "boolean",
            Provenance.OFFICIAL_BALANCE,
            value=available,
            fetched_at=fetched_at,
        )
    ]
    for index, raw in enumerate(infos):
        info = _mapping(raw, f"balance_infos[{index}]")
        currency = info.get("currency")
        if not isinstance(currency, str) or not currency.strip():
            raise ValueError(f"balance_infos[{index}].currency is required")
        currency = currency.strip().upper()
        for source, metric_id in (
            ("total_balance", "balance.total"),
            ("granted_balance", "balance.granted"),
            ("topped_up_balance", "balance.topped_up"),
        ):
            observations.append(
                MetricObservation(
                    metric_id,
                    "balance",
                    currency,
                    Provenance.OFFICIAL_BALANCE,
                    value=_decimal(info.get(source), f"balance_infos[{index}].{source}"),
                    scope=currency,
                    fetched_at=fetched_at,
                )
            )

    return ProviderUsageSnapshot(
        provider_id="deepseek",
        fetched_at=fetched_at,
        observations=tuple(observations),
        state=ObservationState.FRESH if available else ObservationState.UNAVAILABLE,
        unavailable_reason=(
            None if available else UnavailableReason.PROVIDER_REPORTED_UNAVAILABLE
        ),
    )


def parse_openai_rate_limit_headers(
    headers: Mapping[str, Any], *, fetched_at: str
) -> ProviderUsageSnapshot:
    values = {str(key).lower(): value for key, value in headers.items()}

    def observation(
        metric_id: str,
        unit: str,
        limit_key: str,
        remaining_key: str,
        reset_key: str,
    ) -> MetricObservation | None:
        if all(values.get(key) is None for key in (limit_key, remaining_key, reset_key)):
            return None
        if values.get(limit_key) is None or values.get(remaining_key) is None:
            raise ValueError(f"{metric_id} requires limit and remaining headers")
        reset = values.get(reset_key)
        return MetricObservation(
            metric_id,
            "rate_limit",
            unit,
            Provenance.RATE_LIMIT_HEADER,
            limit=_decimal(values[limit_key], limit_key),
            remaining=_decimal(values[remaining_key], remaining_key),
            reset_after=None if reset is None else str(reset),
            fetched_at=fetched_at,
        )

    observations = tuple(
        item
        for item in (
            observation(
                "rate_limit.requests",
                "requests",
                "x-ratelimit-limit-requests",
                "x-ratelimit-remaining-requests",
                "x-ratelimit-reset-requests",
            ),
            observation(
                "rate_limit.tokens",
                "tokens",
                "x-ratelimit-limit-tokens",
                "x-ratelimit-remaining-tokens",
                "x-ratelimit-reset-tokens",
            ),
        )
        if item is not None
    )
    return ProviderUsageSnapshot("openai", fetched_at, observations)


_OPENAI_USAGE_FIELDS = {
    "input_tokens": ("usage.input_tokens", "tokens"),
    "output_tokens": ("usage.output_tokens", "tokens"),
    "input_cached_tokens": ("usage.input_cached_tokens", "tokens"),
    "num_model_requests": ("usage.requests", "requests"),
}


def parse_openai_organization_usage(
    payload: Mapping[str, Any], *, fetched_at: str
) -> ProviderUsageSnapshot:
    buckets = _sequence(_mapping(payload, "payload").get("data"), "data")
    totals = {field: Decimal(0) for field in _OPENAI_USAGE_FIELDS}
    seen: set[str] = set()
    period_start: str | None = None
    period_end: str | None = None

    for bucket_index, raw_bucket in enumerate(buckets):
        bucket = _mapping(raw_bucket, f"data[{bucket_index}]")
        if period_start is None and bucket.get("start_time") is not None:
            period_start = str(bucket["start_time"])
        if bucket.get("end_time") is not None:
            period_end = str(bucket["end_time"])
        results = _sequence(bucket.get("results", ()), f"data[{bucket_index}].results")
        for result_index, raw_result in enumerate(results):
            result = _mapping(
                raw_result, f"data[{bucket_index}].results[{result_index}]"
            )
            for field in _OPENAI_USAGE_FIELDS:
                if field in result and result[field] is not None:
                    totals[field] += _decimal(
                        result[field],
                        f"data[{bucket_index}].results[{result_index}].{field}",
                    )
                    seen.add(field)

    observations = tuple(
        MetricObservation(
            metric_id,
            "usage",
            unit,
            Provenance.OFFICIAL_USAGE,
            used=totals[field],
            period_start=period_start,
            period_end=period_end,
            fetched_at=fetched_at,
        )
        for field, (metric_id, unit) in _OPENAI_USAGE_FIELDS.items()
        if field in seen
    )
    return ProviderUsageSnapshot("openai", fetched_at, observations)


_SENSENOVA_FIELDS = {
    "prompt_tokens": "usage.prompt_tokens",
    "knowledge_tokens": "usage.knowledge_tokens",
    "completion_tokens": "usage.completion_tokens",
    "total_tokens": "usage.total_tokens",
}


def _sensenova_observations(
    usage: Mapping[str, Any], *, fetched_at: str
) -> tuple[MetricObservation, ...]:
    result = tuple(
        MetricObservation(
            metric_id,
            "usage",
            "tokens",
            Provenance.LOCAL_METERING,
            used=_decimal(usage[field], field),
            fetched_at=fetched_at,
            confidence="observed",
        )
        for field, metric_id in _SENSENOVA_FIELDS.items()
        if field in usage and usage[field] is not None
    )
    if not result:
        raise ValueError("SenseNova usage contains no supported token fields")
    return result


def parse_sensenova_usage(
    payload: Mapping[str, Any], *, fetched_at: str
) -> ProviderUsageSnapshot:
    usage = _mapping(_mapping(payload, "payload").get("usage"), "usage")
    return ProviderUsageSnapshot(
        "sensetime",
        fetched_at,
        _sensenova_observations(usage, fetched_at=fetched_at),
    )


def parse_sensenova_stream_usage(
    chunks: Iterable[Mapping[str, Any]],
    *,
    fetched_at: str,
    response_id: str | None = None,
) -> ProviderUsageSnapshot:
    latest: Mapping[str, Any] | None = None
    stream_id = response_id
    previous: dict[str, Decimal] = {}

    for index, raw_chunk in enumerate(chunks):
        chunk = _mapping(raw_chunk, f"chunks[{index}]")
        chunk_id = chunk.get("id") or chunk.get("response_id")
        if chunk_id is not None:
            chunk_id = str(chunk_id)
            if stream_id is None:
                stream_id = chunk_id
            elif chunk_id != stream_id:
                raise ValueError("stream chunks must belong to one response identity")

        if chunk.get("usage") is None:
            continue
        usage = _mapping(chunk["usage"], f"chunks[{index}].usage")
        for field in _SENSENOVA_FIELDS:
            if field not in usage or usage[field] is None:
                continue
            current = _decimal(usage[field], f"chunks[{index}].usage.{field}")
            if field in previous and current < previous[field]:
                raise ValueError(f"cumulative usage decreased for {field}")
            previous[field] = current
        latest = usage

    if latest is None:
        raise ValueError("stream contains no usage observation")
    return ProviderUsageSnapshot(
        "sensetime",
        fetched_at,
        _sensenova_observations(latest, fetched_at=fetched_at),
    )


def state_from_http_status(status_code: int) -> ObservationState:
    if status_code in (401, 403):
        return ObservationState.AUTH_FAILED
    if status_code == 429:
        return ObservationState.RATE_LIMITED
    if 500 <= status_code <= 599:
        return ObservationState.TRANSIENT_ERROR
    if 200 <= status_code <= 299:
        return ObservationState.FRESH
    return ObservationState.UNAVAILABLE
