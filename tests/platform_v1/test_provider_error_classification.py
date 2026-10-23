"""Parametrized tests for real provider error classification.

Only events with type=error/session.error or a direct error mapping are
scanned. Success text output, tool results and other non-error events must
never mis-classify as an auth failure or quota exhaustion.
"""

import pytest

from reverse_agent.platform_v1.opencode_executor import (
    OpenCodeExecutor,
    _extract_error_payloads,
    _pick_error_status,
    _pick_error_str,
)


def _dummy_executor() -> OpenCodeExecutor:
    return OpenCodeExecutor(model_id="provider/model")


@pytest.mark.parametrize(
    ("events", "expected"),
    [
        (
            [{"type": "error", "error": {"name": "APIError", "data": {
                "statusCode": 429, "message": "Your quota has been exhausted",
            }}}],
            "quota_exhausted",
        ),
        (
            [{"type": "error", "error": {"name": "APIError", "data": {
                "statusCode": 429, "message": "Too many requests",
            }}}],
            "api_error_429",
        ),
        (
            [{"type": "error", "error": {"name": "APIError", "data": {
                "status_code": 529, "message": "Service provider overload",
            }}}],
            "provider_overloaded",
        ),
        (
            [{"type": "error", "error": {"name": "APIError", "data": {
                "statusCode": 401, "message": "Invalid API key",
            }}}],
            "auth_provider_route_failure",
        ),
        (
            [{"type": "error", "error": {"name": "APIError", "data": {
                "statusCode": 403, "message": "Forbidden",
            }}}],
            "auth_provider_route_failure",
        ),
        (
            [{"type": "error", "error": {"name": "APIError", "data": {
                "statusCode": 503, "message": "Service unavailable",
            }}}],
            "provider_overloaded",
        ),
        (
            [{"type": "error", "error": {"name": "APIError", "data": {
                "statusCode": 429, "message": "Request rate limited, quota status unknown",
            }}}],
            "api_error_429",
        ),
        (
            [{"type": "error", "error": {"name": "APIError", "data": {
                "statusCode": 429, "message": "Quota exceeded but reset unknown",
            }}}],
            "api_error_429",
        ),
        (
            [{"type": "error", "error": {"name": "APIError", "data": {
                "statusCode": 500, "message": "Internal server error",
            }}}],
            "executor_nonzero",
        ),
        (
            [{"type": "error", "error": {"name": "APIError", "data": {
                "statusCode": 500, "message": "auth check failed",
            }}}],
            "executor_nonzero",
        ),
    ],
)
def test_classify_real_error_events(events, expected):
    ex = _dummy_executor()
    assert ex._classify_exit(1, events) == expected


@pytest.mark.parametrize(
    ("events", "expected"),
    [
        (
            [{"type": "text", "data": "Here is the invalid_api_key I found in auth docs"}],
            "executor_nonzero",
        ),
        (
            [{"type": "text", "data": "The model_not_supported message appears above"}],
            "executor_nonzero",
        ),
        (
            [{"type": "tool", "name": "bash", "output": "unauthorized request log"}],
            "executor_nonzero",
        ),
        (
            [{"type": "text", "data": "quota status reset unknown"}],
            "executor_nonzero",
        ),
    ],
)
def test_non_error_events_stay_unknown(events, expected):
    ex = _dummy_executor()
    assert ex._classify_exit(1, events) == expected


@pytest.mark.parametrize(
    ("exit_code", "expected"),
    [
        (127, "cli_unavailable"),
        (126, "cli_unavailable"),
        (124, "timeout"),
        (137, "timeout"),
        (143, "timeout"),
    ],
)
def test_exit_code_priority_above_events(exit_code, expected):
    ex = _dummy_executor()
    poison = [{"type": "error", "error": {"data": {
        "statusCode": 401, "message": "invalid api key",
    }}}]
    assert ex._classify_exit(exit_code, poison) == expected


def test_direct_error_dict_no_data():
    ex = _dummy_executor()
    ev = [{"type": "error", "error": {"statusCode": 429, "message": "Too many requests"}}]
    assert ex._classify_exit(1, ev) == "api_error_429"


def test_empty_error_stays_unknown():
    ex = _dummy_executor()
    ev = [{"type": "error", "error": {}}]
    assert ex._classify_exit(1, ev) == "executor_nonzero"


def test_simple_529_without_status_code():
    ex = _dummy_executor()
    ev = [{"type": "error", "error": {"message": "Service at capacity"}}]
    assert ex._classify_exit(1, ev) == "provider_overloaded"


def test_session_error_type_recognized():
    ex = _dummy_executor()
    ev = [{"type": "session.error", "error": {"data": {
        "statusCode": 401, "message": "authentication failed",
    }}}]
    assert ex._classify_exit(1, ev) == "auth_provider_route_failure"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"data": {"statusCode": 429}}, 429),
        ({"status_code": 401}, 401),
        ({"data": {"status": 503}}, 503),
        ({"data": {"body": {"status": 429}}}, None),
        ({"data": {"statusCode": "429"}}, None),
    ],
)
def test_pick_error_status(payload, expected):
    assert _pick_error_status(payload) == expected


@pytest.mark.parametrize(
    ("payload", "expected_substr"),
    [
        ({"data": {"message": "Too many requests"}}, "too many requests"),
        ({"code": "invalid_api_key"}, "invalid_api_key"),
        ({"name": "QuotaExceeded"}, "quotaexceeded"),
        ({"data": {"body": {"message": "ignored"}}}, ""),
    ],
)
def test_pick_error_str(payload, expected_substr):
    result = _pick_error_str(payload)
    if expected_substr == "":
        assert result == ""
    else:
        assert expected_substr in result


def test_extract_error_payloads_skips_non_errors():
    events = [
        {"type": "text", "data": "hello auth"},
        {"type": "error", "error": {"message": "boom"}},
        {"type": "tool", "name": "bash", "output": "unrelated"},
        {"type": "session.error", "error": {"data": {"statusCode": 429}}},
    ]
    payloads = _extract_error_payloads(events)
    assert len(payloads) == 2


def test_outer_error_code_used_when_data_is_present():
    ex = _dummy_executor()
    ev = [{"type": "error", "error": {
        "code": "insufficient_quota",
        "data": {"statusCode": 429, "message": "Request failed"},
    }}]
    assert ex._classify_exit(1, ev) == "quota_exhausted"


def test_middle_field_code_not_swallowed_by_first_message():
    ex = _dummy_executor()
    ev = [{"type": "error", "error": {
        "message": "Request failed",
        "code": "insufficient_quota",
        "statusCode": 429,
    }}]
    assert ex._classify_exit(1, ev) == "quota_exhausted"


def test_outer_data_fields_both_contribute_to_str():
    payload = {"code": "insufficient_quota", "data": {"statusCode": 429, "message": "Request failed"}}
    text = _pick_error_str(payload)
    assert "insufficient_quota" in text
    assert "request failed" in text


def test_body_field_does_not_pollute_str():
    payload = {"data": {"statusCode": 429, "body": {"message": "your quota has been exhausted"}}}
    assert _pick_error_str(payload) == ""


def test_secret_and_headers_not_used_for_classification():
    ex = _dummy_executor()
    ev = [{"type": "error", "error": {
        "data": {
            "statusCode": 429,
            "body": {"message": "your quota has been exhausted"},
            "headers": {"x-rate-limit": "0"},
            "prompt": "use the secret: sk-live-1234",
        },
    }}]
    assert ex._classify_exit(1, ev) == "api_error_429"


def test_not_exhausted_is_not_quota_exhausted():
    ex = _dummy_executor()
    ev = [{"type": "error", "error": {"data": {
        "statusCode": 429,
        "message": "Quota is not exhausted; request rate limited",
    }}}]
    assert ex._classify_exit(1, ev) == "api_error_429"


def test_model_not_supported_uses_MODEL_UNAVAILABLE_prefix():
    ex = _dummy_executor()
    ev = [{"type": "error", "error": {"code": "model_not_supported", "message": "Model not supported"}}]
    result = ex._classify_exit(1, ev)
    assert result.startswith("MODEL_UNAVAILABLE:"), f"expected MODEL_UNAVAILABLE:..., got {result!r}"
    assert result == "MODEL_UNAVAILABLE:model_not_supported"


@pytest.mark.parametrize(("event", "expected"), [
    ({"type": "error", "error": {"message": "Model unavailable"}}, "model_provider_unavailable"),
    ({"type": "error", "error": {"message": "Requested model is unavailable"}}, "model_provider_unavailable"),
    ({"type": "error", "error": {"message": "Model 'provider/model' not found"}}, "model_provider_unavailable"),
    ({"type": "text", "message": "Model unavailable; invalid_api_key"}, "executor_nonzero"),
])
def test_generic_model_unavailable_keeps_existing_ui_classification(event, expected):
    assert _dummy_executor()._classify_exit(1, [event]) == expected


@pytest.mark.parametrize(("status", "message", "expected"), [
    (429, "Your quota has been exhausted", "quota_exhausted"),
    (429, "Request rate limited; reset unknown", "api_error_429"),
    (401, "Unauthorized", "auth_provider_route_failure"),
    (529, "Provider overloaded", "provider_overloaded"),
    (403, "content_policy_violation: Forbidden", "policy_refusal"),
    (429, "policy_refusal; quota has been exhausted", "policy_refusal"),
])
def test_actual_core_returns_specific_blocker_without_raw_payload(monkeypatch, tmp_path, status, message, expected):
    import json
    from reverse_agent.platform_v1 import opencode_executor as oe
    from reverse_agent.platform_v1.run_store import TaskStore
    store = TaskStore(":memory:")
    task = store.create_task(title="controlled provider failure", executor_kind="opencode")
    payload = {"type": "error", "error": {"data": {
        "statusCode": status, "message": message, "body": "private-body-marker",
        "headers": {"Authorization": "private-header-marker"},
    }}}
    monkeypatch.setattr(oe, "_run_owned_cli_process", lambda *a, **k:
        oe.OwnedCliProcessResult(returncode=1, stdout=json.dumps(payload), stderr="",
                                timed_out=False, cleanup_confirmed=True))
    monkeypatch.setattr(oe, "_collect_changed_files", lambda *a: [])
    events = []
    try:
        result = _dummy_executor()._run_executor_core(
            task_id=task.id, store=store, worktree=tmp_path, base_sha="controlled",
            execution_id="controlled", cli_path="fixture", is_cmd=False,
            event_callback=lambda tid, event: events.append(event),
            role_context=oe.RoleContext(role="executor", task_id=task.id, workspace=tmp_path))
        assert result.failure_classification == expected
        assert result.error == "opencode_nonzero:exit=1:" + expected
        finished = [e for e in events if e.get("title") == "OpenCode nonzero exit"]
        assert len(finished) == 1
        assert finished[0]["metadata"]["failure_classification"] == expected
        assert "private-body-marker" not in result.error + json.dumps(finished)
        assert "private-header-marker" not in result.error + json.dumps(finished)
    finally:
        store._conn.close()


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize(("status", "message"), [
    (401, "Unauthorized"), (403, "Forbidden"),
    (429, "Your quota has been exhausted"), (503, "Provider overloaded"),
    (529, "Provider at capacity"), (None, "Forbidden"),
])
def test_explicit_policy_precedes_generic_status_and_refusal_consumer(nested, status, message):
    from reverse_agent.platform_v1.routing_inputs import model_refused
    payload = {"code": "content_policy_violation", "message": message}
    if status is not None:
        payload["statusCode"] = status
    event = {"type": "error", "error": {"data": payload} if nested else payload}
    classification = _dummy_executor()._classify_exit(1, [event])
    assert classification == "policy_refusal"
    assert model_refused("", changed_files=[],
                         policy_refusal=classification in {"policy_refusal", "MODEL_REFUSED"})


def test_availability_exit_and_event_order_remain_ahead_of_policy():
    executor = _dummy_executor()
    policy = {"type": "error", "error": {"code": "policy_refusal", "message": "Forbidden", "statusCode": 403}}
    unavailable = {"type": "error", "error": {"code": "invalid_api_key", "message": "policy_refusal", "statusCode": 403}}
    auth = {"type": "error", "error": {"message": "Forbidden", "statusCode": 403}}
    assert executor._classify_exit(1, [unavailable]) == "MODEL_UNAVAILABLE:invalid_api_key"
    assert executor._classify_exit(127, [policy]) == "cli_unavailable"
    assert executor._classify_exit(124, [policy]) == "timeout"
    assert executor._classify_exit(1, [auth, policy]) == "auth_provider_route_failure"
    assert executor._classify_exit(1, [policy, auth]) == "policy_refusal"
