"""Routing and durable artifact execution with fake transports only."""
from types import SimpleNamespace

import pytest

from test_model_router import candidate, choose, fixture_host
from test_model_review_toolless import toolless, run
from test_model_review_execution import review_setup
from test_goal_functional_checks import goal_checks
from reverse_agent.platform_v1 import model_review_transport as transport
from reverse_agent.platform_v1.goal_service import PlannedTask
from reverse_agent.platform_v1.model_router import ModelSelectionError
from reverse_agent.platform_v1.run_store import TaskStoreError


def test_codex_authored_routing_executes_independent_toolless(toolless, monkeypatch):
    s = toolless
    checked = []
    original_validate = transport.validate_connection
    def validate(resolution, lease_provider):
        checked.append(resolution.model_id if hasattr(resolution, "model_id") else "routing")
        return original_validate(resolution, lease_provider)
    monkeypatch.setattr(transport, "validate_connection", validate)
    s["store"]._conn.execute("UPDATE tasks SET executor_kind = 'codex' WHERE id = ?", (s["producer"],))
    s["store"].add_event(s["producer"], event_type="EXECUTOR_COMPLETED", title="Author execution",
        metadata={"models": ["local/author"]})
    task = s["store"].get_task(s["consumer"])
    pool = [candidate("author", "author", executor="codex"),
            candidate("fallback", "other", executor="codex"),
            candidate(task.binding_ref, "local/test", "subscription")]
    decision = choose(pool, kind="review", author_models=["author"])
    assert decision["binding_ref"] == task.binding_ref
    assert decision["executor_kind"] == "opencode"
    # The selected binding is the one admitted by durable execution.
    resolution = s["service"].binding_resolver.resolve(task.binding_ref, task_executor="opencode")
    assert resolution.model_id == decision["model_id"]
    result = run(s)
    assert result.success, result
    assert len(s["calls"]) == 1 and s["released"] == [True]
    assert "routing" in checked and decision["model_id"] in checked


@pytest.mark.parametrize("changes", [
    {"auth_method": "none"}, {"relay_required": False},
    {"native_endpoint": "/responses"}, {"native_endpoint": "/messages"}])
def test_unsupported_cheaper_transport_and_misleading_provider(changes):
    bad = candidate("bad", "codex-provider/independent")
    bad["review_connection"].update(changes)
    good = candidate("good", "unfamiliar/model", "subscription")
    result = choose([bad, good], kind="review", author_models=["author"], author_executors=["codex"])
    assert result["binding_ref"] == "good"
    assert result["excluded_candidates"][0]["filter"] == "review_transport_unsupported"
    assert choose([bad, good])["binding_ref"] == "bad"


@pytest.mark.parametrize("executor,lease", [("claude_code", lambda r: None), ("opencode", None)])
def test_no_eligible_transport(executor, lease):
    row = candidate("bad", "independent", executor=executor)
    row["review_lease_provider"] = lease
    with pytest.raises(ModelSelectionError, match="review_not_independent"):
        choose([row], kind="review", author_models=["author"])


def test_aliases_repair_authors_and_codex_fallback():
    pool = [candidate("old", "gateway/AUTHOR:free"), candidate("repair", "vendor/repair-free"),
            candidate("fallback", "independent", executor="codex")]
    result = choose(pool, kind="review", author_models=["author", "repair"], author_executors=["codex"])
    assert result["binding_ref"] == "fallback"
    assert {r["filter"] for r in result["excluded_candidates"]} == {"reviewer_is_author"}


@pytest.mark.parametrize("authors", [[""], ["vendor/"], [None], ["author", " "]])
def test_unknown_author_fails_closed(authors):
    with pytest.raises(ModelSelectionError, match="review_not_independent"):
        choose([candidate("reviewer", "independent")], kind="review", author_models=authors)


@pytest.mark.parametrize("extra,kwargs", [
    ({"quota": {"reason": "observed_exhausted"}}, {}),
    ({"availability": {"state": "UNAVAILABLE"}}, {}),
    ({"cost_class": "paid_api"}, {"allow_paid": False}),
    ({"metadata": {"context_window": 100}}, {"context_need": 1000}),
    ({"metadata": {"input_modalities": ["text"]}}, {"needs": ["vision"]})])
def test_admission_constraints_survive_toolless_preference(extra, kwargs):
    row = candidate("reviewer", "independent")
    row.update(extra)
    fallback = candidate("fallback", "another", executor="codex", metadata={"input_modalities": ["image"]})
    result = choose([row, fallback], kind="review", author_models=["author"],
                    author_executors=["codex"], **kwargs)
    assert result["binding_ref"] == "fallback"
    with pytest.raises(ModelSelectionError):
        choose([row, fallback], kind="review", author_models=["author"], pin="reviewer", **kwargs)


def test_host_rejects_unsupported_before_probe(monkeypatch, tmp_path):
    host = fixture_host(monkeypatch, tmp_path)
    original = host._store.list_bindings_public
    monkeypatch.setattr(host._store, "list_bindings_public", lambda: [
        {**b, "native_endpoint": "/responses"} for b in original()])
    connections = host._store.list_connections_public
    monkeypatch.setattr(host._store, "list_connections_public", lambda: [
        {**c, "auth_method": "api_key"} for c in connections()])
    monkeypatch.setattr(host, "_routing_paid_allowed", lambda *a: True)
    probes = []
    monkeypatch.setattr(host, "_routing_availability", lambda *a, **kw:
        probes.append(kw["probe_allowed"]) or {"state": "AVAILABLE"})
    task = PlannedTask("R", "Review", "Review", kind="review", difficulty=2,
                       artifact_input={"plan_task_id": "P"})
    with pytest.raises(TaskStoreError, match="review_not_independent"):
        host._resolve_task_model(task, author_models=["author"])
    assert probes and not any(probes)


@pytest.mark.parametrize("model", [None, "", "gateway/", " "])
def test_unknown_reviewer_fails_closed(model):
    with pytest.raises(ModelSelectionError, match="review_not_independent"):
        choose([candidate("bad", model)], kind="review", author_models=["author"])


def test_missing_transport_metadata_fails_closed():
    row = candidate("bad", "independent")
    row.pop("review_connection")
    with pytest.raises(ModelSelectionError, match="review_not_independent"):
        choose([row], kind="review", author_models=["author"])


def test_pin_retry_tier_and_known_availability_survive_preference():
    tool = candidate("tool", "independent")
    codex = candidate("codex", "another", executor="codex")
    args = dict(kind="review", author_models=["author"], author_executors=["codex"])
    assert choose([tool, codex], pin="codex", **args)["binding_ref"] == "codex"
    tool["availability"] = {"state": "UNKNOWN"}
    assert choose([tool, codex], **args)["binding_ref"] == "codex"
    tool["availability"] = {"state": "AVAILABLE"}
    assert choose([tool, codex], failed_model="independent", failed_tier=2, **args)["binding_ref"] == "codex"
    with pytest.raises(ModelSelectionError, match="review_not_independent"):
        choose([tool], difficulty=4, **args)


def test_retained_attempt_executors_and_models_reach_review_routing():
    from reverse_agent.platform_v1 import goal_service
    service = object.__new__(goal_service.GoalService)
    service.control_store = SimpleNamespace(
        list_goal_tasks=lambda goal: [{"plan_task_id": "P", "task_id": "repair", "goal_revision": 1}],
        list_task_escalations=lambda goal: [{"plan_task_id": "P", "from_task_id": "original", "goal_revision": 1}])
    attempts = {"original": SimpleNamespace(executor_kind="codex", binding_ref="gone", status="SUCCEEDED"),
                "repair": SimpleNamespace(executor_kind="opencode", binding_ref="repair", status="SUCCEEDED")}
    service.store = SimpleNamespace(get_task=attempts.__getitem__, list_usage_observations=lambda task: [
        SimpleNamespace(model_id="gateway/author:free" if task == "original" else "repair-author")])
    producer = PlannedTask("P", "Producer", "Edit")
    review = PlannedTask("R", "Review", "Review", kind="review", artifact_input={"plan_task_id": "P"})
    facts = service._review_authors(review, SimpleNamespace(id="goal", revision=1), {"P": producer, "R": review})
    assert set(facts["author_executors"]) == {"codex", "opencode"}
    pool = [candidate("alias", "author"), candidate("repair", "repair-author"),
            candidate("fallback", "independent", executor="codex"),
            candidate("tool", "supported", "subscription")]
    facts.pop("author_bindings")
    assert choose(pool, kind="review", **facts)["binding_ref"] == "tool"
