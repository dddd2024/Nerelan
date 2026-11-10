"""Provider-free relay review tests with real retained artifacts and durable state."""
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from test_goal_functional_checks import goal_checks
from test_model_review_execution import review_setup, evidence, ACCEPT, REJECT
from test_functional_execution import durable, LocalBinding
from reverse_agent.platform_v1 import model_review, model_review_transport as transport
from reverse_agent.platform_v1.run_store import TaskStoreError


@pytest.fixture
def toolless(review_setup, monkeypatch):
    store, router, producer, consumer, created, options, root = review_setup
    store._conn.execute("UPDATE tasks SET executor_kind = 'opencode' WHERE id = ?", (consumer,))
    original = LocalBinding.resolve
    def resolve(self, ref, *, task_executor):
        return replace(original(self, ref, task_executor=task_executor), auth_method="api_key",
                       relay_required=True)
    monkeypatch.setattr(LocalBinding, "resolve", resolve)
    state = {"calls": [], "released": [], "deadlines": [], "payload": {
        "id": "review-request", "model": "test", "choices": [{"finish_reason": "stop",
        "message": {"role": "assistant", "content": ACCEPT}}]}}
    def lease(resolution):
        return SimpleNamespace(model_id="reverse-agent-relay/test", lease_id="fake-lease",
            relay_url="http://127.0.0.1:1234",
            bind_execution_deadline=state["deadlines"].append,
            release=lambda: state["released"].append(True))
    def chat(handle, body):
        state["calls"].append(body)
        return state["payload"]
    monkeypatch.setattr(transport, "chat", chat)
    def forbidden(**kwargs):
        pytest.fail("ordinary executor constructed")
    router.replace("opencode", forbidden)
    service = durable(store, router)
    service.lease_provider = lease
    state.update(service=service, consumer=consumer, root=root, store=store, producer=producer)
    return state


def run(state):
    return state["service"].execute_durable_single(state["consumer"], workspace_root=str(state["root"]))


def test_toolless_accept_and_replay(toolless):
    s = toolless
    result = run(s)
    assert result.success, result
    assert len(s["calls"]) == 1 and s["released"] == [True]
    assert s["deadlines"] == [transport.TIMEOUT_SECONDS]
    body = s["calls"][0]
    assert set(body) == {"model", "messages", "stream", "max_tokens"}
    assert body["messages"][0]["role"] == "user"
    prompt = body["messages"][0]["content"]
    request = json.loads(prompt.split("\n", 1)[1])
    assert "-value = 1" in request["diff"] and "+value = 2" in request["diff"]
    assert request["response_contract"] == model_review.response_schema()
    assert request["acceptance_criteria"] and request["producer_functional_results"]
    assert str(s["root"]) not in prompt
    assert s["service"].resume_single(s["consumer"]).success
    assert len(s["calls"]) == 1


@pytest.mark.parametrize("case,reason", [
    ("malformed", "model_review_invalid_output"), ("duplicate", "model_review_invalid_output"),
    ("reject", "model_review_rejected"), ("tools", "model_review_invalid_output"),
    ("unexpected", "review_not_independent"), ("missing", "review_not_independent"),
    ("timeout", "model_review_completion_unknown")])
def test_failed_response_cleans_lease(toolless, monkeypatch, case, reason):
    s = toolless
    message = s["payload"]["choices"][0]["message"]
    if case == "malformed": message["content"] = "not json"
    if case == "duplicate": message["content"] = '{"verdict":"ACCEPT","verdict":"ACCEPT","findings":[]}'
    if case == "reject": message["content"] = REJECT
    if case == "tools": message["tool_calls"] = [{"id": "call"}]
    if case == "unexpected": s["payload"]["model"] = "other"
    if case == "missing": del s["payload"]["model"]
    if case == "timeout":
        def fail(*args): raise TimeoutError()
        monkeypatch.setattr(transport, "chat", fail)
    result = run(s)
    assert not result.success and result.failure_classification == reason, result
    assert s["released"] == [True]


@pytest.mark.parametrize("diff", ["x" * 17, "\u00e9" * 9])
def test_oversize_fails_before_dispatch(toolless, monkeypatch, diff):
    monkeypatch.setattr(model_review, "MAX_DIFF_BYTES", 16)
    original = model_review.subprocess.run
    def command(argv, **kwargs):
        if "--no-textconv" in argv:
            return SimpleNamespace(returncode=0, stdout=diff.encode("utf-8"))
        return original(argv, **kwargs)
    monkeypatch.setattr(model_review.subprocess, "run", command)
    result = run(toolless)
    assert result.failure_classification == "review_diff_too_large", result
    assert not toolless["calls"] and not toolless["released"]


@pytest.mark.parametrize("changes", [{"auth_method": "none"}, {"native_endpoint": "/responses"},
    {"executor_id": "claude_code"}, {"relay_required": False}])
def test_unsupported_connection(changes):
    resolution = SimpleNamespace(executor_id="opencode", auth_method="api_key",
        native_endpoint="/chat/completions", relay_required=True)
    for key, value in changes.items(): setattr(resolution, key, value)
    with pytest.raises(TaskStoreError, match="model_review_connection_unsupported"):
        transport.review("prompt", resolution, lambda r: pytest.fail("lease acquired"))


def gateway(**changes):
    values = dict(executor_id="opencode", auth_method="none", relay_required=False,
                  native_endpoint="/chat/completions", base_url="http://127.0.0.1:3425/v1",
                  provider_id="magpie", model_id="magpie/claude/claude-sonnet-5-5")
    values.update(changes)
    return SimpleNamespace(**values)


def test_a_keyless_loopback_gateway_is_a_review_transport_without_a_lease():
    transport.validate_connection(gateway(), None)
    assert transport.keyless_gateway(gateway(base_url="http://localhost:3425/v1"))
    assert transport.keyless_gateway(gateway(base_url="http://[::1]:3425/v1"))


@pytest.mark.parametrize("changes", [
    {"base_url": "https://127.0.0.1:3425/v1"}, {"base_url": "http://example.com:3425/v1"},
    {"base_url": "http://127.0.0.1.example.com:80/v1"}, {"base_url": "http://user:pw@127.0.0.1:3425/v1"},
    {"base_url": "http://127.0.0.1/v1"}, {"base_url": "http://127.0.0.1:3425/v1?x=1"},
    {"base_url": "http://127.0.0.1:99999/v1"}, {"base_url": ""}, {"base_url": None},
    {"relay_required": True}, {"native_endpoint": "/responses"}, {"executor_id": "claude_code"},
    {"auth_method": "external_cli_session"}])
def test_other_keyless_or_remote_connections_stay_unsupported(changes):
    resolution = gateway(**changes)
    assert not transport.keyless_gateway(resolution)
    with pytest.raises(TaskStoreError, match="model_review_connection_unsupported"):
        transport.review("prompt", resolution, None)


def gateway_reply(**changes):
    payload = {"id": "request-1", "model": "claude/claude-sonnet-5-5", "choices": [{
        "finish_reason": "stop", "message": {"role": "assistant", "content": ACCEPT}}]}
    payload.update(changes)
    return payload


def test_gateway_review_sends_the_gateways_own_model_id_and_no_credential(monkeypatch):
    seen = {}
    def post(base_url, body, headers):
        seen.update(base_url=base_url, body=body, headers=headers)
        return gateway_reply()
    monkeypatch.setattr(transport, "_post", post)
    reply = transport.review("prompt", gateway(), lambda r: pytest.fail("lease acquired"))
    assert seen["base_url"] == "http://127.0.0.1:3425/v1" and seen["headers"] == {}
    assert seen["body"] == {"model": "claude/claude-sonnet-5-5", "stream": False, "max_tokens": 8192,
                            "messages": [{"role": "user", "content": "prompt"}]}
    assert reply["actual_models"] == ["magpie/claude/claude-sonnet-5-5"] and reply["request_id"] == "request-1"


@pytest.mark.parametrize("changes,reason", [
    ({"model": "claude/claude-opus-5-5"}, "review_not_independent"),
    ({"model": ""}, "review_not_independent"),
    ({"id": ""}, "model_review_invalid_output"),
    ({"choices": []}, "model_review_invalid_output")])
def test_gateway_answers_are_checked_like_relay_answers(monkeypatch, changes, reason):
    monkeypatch.setattr(transport, "_post", lambda *args: gateway_reply(**changes))
    with pytest.raises(TaskStoreError, match=reason):
        transport.review("prompt", gateway(), None)


def test_a_gateway_review_runs_end_to_end_without_a_lease(toolless, monkeypatch):
    s = toolless
    from test_functional_execution import LocalBinding
    relay = LocalBinding.resolve
    def resolve(self, ref, *, task_executor):
        return replace(relay(self, ref, task_executor=task_executor), auth_method="none",
                       relay_required=False, base_url="http://127.0.0.1:3425/v1")
    monkeypatch.setattr(LocalBinding, "resolve", resolve)
    bodies = []
    def post(base_url, body, headers):
        bodies.append((base_url, headers, body["model"]))
        return {**s["payload"], "model": "test"}
    monkeypatch.setattr(transport, "_post", post)
    s["service"].lease_provider = lambda r: pytest.fail("lease acquired")
    result = run(s)
    assert result.success, result
    assert bodies == [("http://127.0.0.1:3425/v1", {}, "test")] and not s["calls"] and not s["released"]


def test_multibyte_exact_boundary(monkeypatch):
    monkeypatch.setattr(model_review, "MAX_DIFF_BYTES", 4)
    monkeypatch.setattr(model_review.subprocess, "run", lambda *a, **k:
        SimpleNamespace(returncode=0, stdout="\u00e9\u00e9".encode("utf-8")))
    assert model_review.exact_diff(None, "base", "head") == "\u00e9\u00e9"


def test_codex_author_independent_non_codex_review(toolless):
    s = toolless
    s["store"]._conn.execute("UPDATE tasks SET executor_kind = 'codex' WHERE id = ?", (s["producer"],))
    s["store"].add_event(s["producer"], event_type="EXECUTOR_COMPLETED", title="Codex author fixture",
        metadata={"models": ["local/author"]})
    result = run(s)
    assert result.success, result
    record = json.loads(evidence(s["store"], s["consumer"])[0]["detail"])
    assert record["authors"] == ["author"]
    assert record["actual_models"] == ["local/test"]


def test_chat_request_is_bounded_and_has_no_tools(monkeypatch):
    observed = {}
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, limit):
            observed["limit"] = limit
            return b'{"id":"request"}'
    def open_request(request, *, timeout):
        observed.update(url=request.full_url, body=json.loads(request.data), timeout=timeout)
        return Response()
    monkeypatch.setattr(transport, "urlopen", open_request)
    lease = SimpleNamespace(relay_url="http://127.0.0.1:1234", lease_id="fake")
    body = {"model": "test", "messages": [{"role": "user", "content": "assembled prompt"}],
            "stream": False, "max_tokens": 8192}
    assert transport.chat(lease, body) == {"id": "request"}
    assert observed == {"url": "http://127.0.0.1:1234/chat/completions", "body": body,
        "timeout": transport.TIMEOUT_SECONDS, "limit": transport.MAX_RESPONSE_BYTES + 1}


def test_deadline_failure_releases_lease(monkeypatch):
    released = []
    def deadline(seconds): raise RuntimeError("deadline failed")
    lease = SimpleNamespace(bind_execution_deadline=deadline, release=lambda: released.append(True))
    resolution = SimpleNamespace(executor_id="opencode", auth_method="api_key",
        relay_required=True, native_endpoint="/chat/completions")
    with pytest.raises(TaskStoreError, match="transport_error"):
        transport.review("prompt", resolution, lambda r: lease)
    assert released == [True]


def test_replay_after_persisted_evidence_has_no_second_call(toolless, monkeypatch):
    import time
    from reverse_agent.platform_v1 import durable_execution
    s = toolless
    original = durable_execution._check_crash_seam
    def crash(checkpoint):
        if checkpoint == "MODEL_REVIEW_AFTER_EVIDENCE":
            raise durable_execution._CrashSimulated(checkpoint)
        return original(checkpoint)
    monkeypatch.setattr(durable_execution, "_check_crash_seam", crash)
    with pytest.raises(durable_execution._CrashSimulated):
        run(s)
    monkeypatch.setattr(durable_execution, "_check_crash_seam", original)
    now = int(time.time() * 1000)
    s["store"]._conn.execute("UPDATE durable_runs SET lease_expiry_ms = ? WHERE task_id = ?",
                           (now - 10000, s["consumer"]))
    s["service"].reconcile_expired_runs(now_ms=now, max_age_ms=1000)
    result = s["service"].resume_single(s["consumer"], lease_owner="relay-restart")
    assert result.success, result
    assert len(s["calls"]) == 1 and s["released"] == [True]
