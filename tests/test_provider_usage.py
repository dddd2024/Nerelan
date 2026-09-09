from decimal import Decimal

import pytest

from reverse_agent.model_access.provider_usage import (
    CredentialCapability,
    MetricObservation,
    ObservationState,
    Provenance,
    ProviderUsageSnapshot,
    UnavailableReason,
    parse_deepseek_balance,
    parse_openai_organization_usage,
    parse_openai_rate_limit_headers,
    parse_sensenova_stream_usage,
    parse_sensenova_usage,
    resolve_provider_dispatch,
    state_from_http_status,
    unsupported_provider_snapshot,
)


NOW = "2026-09-09T01:30:00Z"


def metric(snapshot, metric_id):
    return next(item for item in snapshot.observations if item.metric_id == metric_id)


def test_closed_normalized_enums():
    assert {item.value for item in Provenance} == {
        "OFFICIAL_BALANCE",
        "OFFICIAL_USAGE",
        "RATE_LIMIT_HEADER",
        "LOCAL_METERING",
        "ESTIMATED",
        "UNAVAILABLE",
    }
    assert {item.value for item in ObservationState} == {
        "FRESH",
        "STALE",
        "UNAVAILABLE",
        "AUTH_FAILED",
        "RATE_LIMITED",
        "TRANSIENT_ERROR",
    }
    assert {item.value for item in CredentialCapability} == {
        "NONE",
        "INFERENCE",
        "MANAGEMENT_USAGE",
        "MANAGEMENT_BILLING",
        "SESSION_OBSERVATION",
    }


def test_unknown_is_distinct_from_zero_and_mixed_provenance_survives():
    snapshot = ProviderUsageSnapshot(
        provider_id="openai",
        fetched_at=NOW,
        observations=(
            MetricObservation(
                "usage.input_tokens",
                "usage",
                "tokens",
                Provenance.OFFICIAL_USAGE,
                used=Decimal("0"),
                fetched_at=NOW,
            ),
            MetricObservation(
                "rate_limit.tokens",
                "rate_limit",
                "tokens",
                Provenance.RATE_LIMIT_HEADER,
                limit=Decimal("100"),
                remaining=None,
                fetched_at=NOW,
            ),
            MetricObservation(
                "local.tokens",
                "usage",
                "tokens",
                Provenance.LOCAL_METERING,
                used=Decimal("5"),
                fetched_at=NOW,
            ),
        ),
    )
    assert metric(snapshot, "usage.input_tokens").used == Decimal("0")
    assert metric(snapshot, "rate_limit.tokens").remaining is None
    assert {item.provenance for item in snapshot.observations} == {
        Provenance.OFFICIAL_USAGE,
        Provenance.RATE_LIMIT_HEADER,
        Provenance.LOCAL_METERING,
    }


def test_confidence_is_derived_from_and_consistent_with_provenance():
    official = MetricObservation(
        "official.tokens",
        "usage",
        "tokens",
        Provenance.OFFICIAL_USAGE,
        used=Decimal("1"),
        fetched_at=NOW,
    )
    local = MetricObservation(
        "local.tokens",
        "usage",
        "tokens",
        Provenance.LOCAL_METERING,
        used=Decimal("1"),
        fetched_at=NOW,
    )
    estimated = MetricObservation(
        "estimated.tokens",
        "usage",
        "tokens",
        Provenance.ESTIMATED,
        used=Decimal("1"),
        fetched_at=NOW,
    )
    assert official.confidence == "authoritative"
    assert local.confidence == "observed"
    assert estimated.confidence == "estimated"

    with pytest.raises(ValueError, match="contradicts provenance"):
        MetricObservation(
            "bad-estimate.tokens",
            "usage",
            "tokens",
            Provenance.ESTIMATED,
            used=Decimal("1"),
            fetched_at=NOW,
            confidence="authoritative",
        )


def test_observations_and_snapshots_require_freshness_metadata():
    with pytest.raises(ValueError, match="fetched_at"):
        MetricObservation(
            "usage.tokens",
            "usage",
            "tokens",
            Provenance.OFFICIAL_USAGE,
            used=Decimal("1"),
        )
    with pytest.raises(ValueError, match="fetched_at"):
        ProviderUsageSnapshot(provider_id="openai", fetched_at="")


def test_deepseek_balance_is_official_and_preserves_currency():
    snapshot = parse_deepseek_balance(
        {
            "is_available": True,
            "balance_infos": [
                {
                    "currency": "CNY",
                    "total_balance": "12.50",
                    "granted_balance": "2.50",
                    "topped_up_balance": "10.00",
                }
            ],
        },
        fetched_at=NOW,
    )
    assert snapshot.state is ObservationState.FRESH
    assert metric(snapshot, "account.available").value is True
    total = metric(snapshot, "balance.total")
    assert total.value == Decimal("12.50")
    assert total.unit == "CNY"
    assert total.provenance is Provenance.OFFICIAL_BALANCE
    assert total.confidence == "authoritative"


def test_deepseek_provider_unavailable_is_not_zero_balance():
    snapshot = parse_deepseek_balance(
        {
            "is_available": False,
            "balance_infos": [
                {
                    "currency": "USD",
                    "total_balance": "3.25",
                    "granted_balance": "0",
                    "topped_up_balance": "3.25",
                }
            ],
        },
        fetched_at=NOW,
    )
    assert snapshot.state is ObservationState.UNAVAILABLE
    assert snapshot.unavailable_reason is UnavailableReason.PROVIDER_REPORTED_UNAVAILABLE
    assert metric(snapshot, "account.available").value is False
    assert metric(snapshot, "balance.total").value == Decimal("3.25")


@pytest.mark.parametrize("bad", ["-1", "NaN", "Infinity", float("nan"), float("inf")])
def test_deepseek_rejects_negative_and_nonfinite_numbers(bad):
    with pytest.raises(ValueError):
        parse_deepseek_balance(
            {
                "is_available": True,
                "balance_infos": [
                    {
                        "currency": "CNY",
                        "total_balance": bad,
                        "granted_balance": "0",
                        "topped_up_balance": "0",
                    }
                ],
            },
            fetched_at=NOW,
        )


def test_openai_rate_limit_headers_are_not_account_balance():
    snapshot = parse_openai_rate_limit_headers(
        {
            "X-RateLimit-Limit-Requests": "500",
            "x-ratelimit-remaining-requests": "499",
            "x-ratelimit-reset-requests": "120ms",
            "x-ratelimit-limit-tokens": "30000",
            "x-ratelimit-remaining-tokens": "29900",
            "x-ratelimit-reset-tokens": "1s",
        },
        fetched_at=NOW,
    )
    requests = metric(snapshot, "rate_limit.requests")
    tokens = metric(snapshot, "rate_limit.tokens")
    assert requests.limit == Decimal("500")
    assert requests.remaining == Decimal("499")
    assert requests.reset_after == "120ms"
    assert tokens.limit == Decimal("30000")
    assert tokens.remaining == Decimal("29900")
    assert all(item.kind == "rate_limit" for item in snapshot.observations)
    assert all(
        item.provenance is Provenance.RATE_LIMIT_HEADER
        for item in snapshot.observations
    )
    assert not any(item.kind == "balance" for item in snapshot.observations)


def test_openai_organization_usage_is_official_usage():
    snapshot = parse_openai_organization_usage(
        {
            "data": [
                {
                    "start_time": "100",
                    "end_time": "200",
                    "results": [
                        {
                            "input_tokens": 10,
                            "output_tokens": 4,
                            "input_cached_tokens": 2,
                            "num_model_requests": 1,
                        },
                        {
                            "input_tokens": 5,
                            "output_tokens": 3,
                            "num_model_requests": 2,
                        },
                    ],
                }
            ],
            "has_more": False,
            "next_page": None,
        },
        fetched_at=NOW,
    )
    assert metric(snapshot, "usage.input_tokens").used == Decimal("15")
    assert metric(snapshot, "usage.output_tokens").used == Decimal("7")
    assert metric(snapshot, "usage.input_cached_tokens").used == Decimal("2")
    assert metric(snapshot, "usage.requests").used == Decimal("3")
    assert all(
        item.provenance is Provenance.OFFICIAL_USAGE for item in snapshot.observations
    )


def test_openai_organization_usage_rejects_incomplete_pagination():
    with pytest.raises(ValueError, match="incomplete"):
        parse_openai_organization_usage(
            {
                "data": [
                    {
                        "start_time": "100",
                        "end_time": "200",
                        "results": [{"input_tokens": 10}],
                    }
                ],
                "has_more": True,
                "next_page": "page-2",
            },
            fetched_at=NOW,
        )


def test_sensenova_non_stream_usage_components_are_local_metering():
    snapshot = parse_sensenova_usage(
        {
            "usage": {
                "prompt_tokens": 7,
                "knowledge_tokens": 2,
                "completion_tokens": 4,
                "total_tokens": 13,
            }
        },
        fetched_at=NOW,
    )
    assert metric(snapshot, "usage.prompt_tokens").used == Decimal("7")
    assert metric(snapshot, "usage.knowledge_tokens").used == Decimal("2")
    assert metric(snapshot, "usage.completion_tokens").used == Decimal("4")
    assert metric(snapshot, "usage.total_tokens").used == Decimal("13")
    assert all(
        item.provenance is Provenance.LOCAL_METERING
        for item in snapshot.observations
    )
    assert all(item.confidence == "observed" for item in snapshot.observations)


def test_sensenova_cumulative_stream_uses_final_not_sum():
    snapshot = parse_sensenova_stream_usage(
        [
            {
                "id": "resp-1",
                "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
            },
            {
                "id": "resp-1",
                "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
            },
            {
                "id": "resp-1",
                "usage": {"prompt_tokens": 5, "completion_tokens": 4, "total_tokens": 9},
            },
            {
                "id": "resp-1",
                "usage": {
                    "prompt_tokens": 7,
                    "knowledge_tokens": 2,
                    "completion_tokens": 4,
                    "total_tokens": 13,
                },
            },
        ],
        fetched_at=NOW,
    )
    assert metric(snapshot, "usage.total_tokens").used == Decimal("13")
    assert metric(snapshot, "usage.prompt_tokens").used == Decimal("7")
    assert metric(snapshot, "usage.knowledge_tokens").used == Decimal("2")
    assert metric(snapshot, "usage.completion_tokens").used == Decimal("4")


def test_sensenova_cumulative_stream_rejects_identity_mix_or_decrease():
    with pytest.raises(ValueError, match="one response identity"):
        parse_sensenova_stream_usage(
            [
                {"id": "a", "usage": {"total_tokens": 7}},
                {"id": "b", "usage": {"total_tokens": 8}},
            ],
            fetched_at=NOW,
        )
    with pytest.raises(ValueError, match="decreased"):
        parse_sensenova_stream_usage(
            [
                {"id": "a", "usage": {"total_tokens": 8}},
                {"id": "a", "usage": {"total_tokens": 7}},
            ],
            fetched_at=NOW,
        )


def test_provider_identity_is_distinct_from_protocol_family():
    sense = resolve_provider_dispatch("sensetime", "openai")
    deepseek = resolve_provider_dispatch("deepseek", "openai-compatible")
    openai = resolve_provider_dispatch("openai", "openai")
    assert sense.parser_ids == ("sensenova_usage",)
    assert sense.provider_id == "sensetime"
    assert deepseek.parser_ids == ("deepseek_balance",)
    assert set(openai.parser_ids) == {
        "openai_rate_limits",
        "openai_organization_usage",
    }
    assert set(openai.allowed_credential_capabilities) == {
        CredentialCapability.INFERENCE,
        CredentialCapability.MANAGEMENT_USAGE,
        CredentialCapability.MANAGEMENT_BILLING,
    }


def test_custom_openai_compatible_does_not_dispatch_openai_billing():
    custom = resolve_provider_dispatch("custom", "openai-compatible")
    assert custom.supported is False
    assert custom.parser_ids == ()
    assert custom.unavailable_reason is UnavailableReason.UNSUPPORTED_PROVIDER

    openrouter = resolve_provider_dispatch("openrouter", "openai")
    assert openrouter.provider_id == "openrouter"
    assert openrouter.supported is False
    assert openrouter.parser_ids == ()


def test_unsupported_provider_snapshot_is_explicit_unavailable():
    snapshot = unsupported_provider_snapshot("custom", fetched_at=NOW)
    assert snapshot.state is ObservationState.UNAVAILABLE
    assert snapshot.unavailable_reason is UnavailableReason.UNSUPPORTED_PROVIDER
    assert snapshot.observations == ()


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (200, ObservationState.FRESH),
        (401, ObservationState.AUTH_FAILED),
        (403, ObservationState.AUTH_FAILED),
        (429, ObservationState.RATE_LIMITED),
        (500, ObservationState.TRANSIENT_ERROR),
        (503, ObservationState.TRANSIENT_ERROR),
        (404, ObservationState.UNAVAILABLE),
    ],
)
def test_http_status_normalization_is_bounded(status, expected):
    assert state_from_http_status(status) is expected


def test_429_does_not_claim_quota_exhaustion():
    state = state_from_http_status(429)
    assert state is ObservationState.RATE_LIMITED
    assert "QUOTA" not in state.value
    assert "WEEKLY" not in state.value


def test_public_serialization_has_closed_sanitized_shape():
    secret_payload = {
        "is_available": True,
        "balance_infos": [
            {
                "currency": "USD",
                "total_balance": "1",
                "granted_balance": "0",
                "topped_up_balance": "1",
            }
        ],
        "Authorization": "Bearer should-not-survive",
        "api_key": "should-not-survive",
        "raw_response": {"cookie": "should-not-survive"},
    }
    public = parse_deepseek_balance(secret_payload, fetched_at=NOW).to_public_dict()
    rendered = repr(public)
    for forbidden in (
        "should-not-survive",
        "Authorization",
        "api_key",
        "raw_response",
        "cookie",
    ):
        assert forbidden not in rendered
    assert set(public) == {
        "provider_id",
        "connection_ref",
        "account_ref",
        "fetched_at",
        "state",
        "unavailable_reason",
        "observations",
    }


def test_module_contract_has_no_network_or_credential_runtime_requirements():
    snapshot = parse_sensenova_usage(
        {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}},
        fetched_at=NOW,
    )
    assert metric(snapshot, "usage.total_tokens").used == Decimal("2")
