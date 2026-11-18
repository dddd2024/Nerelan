"""#1526: an OpenCode attempt prepares its worktree at the base its contract froze, not at HEAD."""
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1 import artifact_handoff, durable_execution, functional_validation as fv
from reverse_agent.platform_v1 import task_execution
from reverse_agent.platform_v1.run_store import TaskStoreError

BASE, OTHER = "a" * 40, "b" * 40


@pytest.fixture
def contracts(monkeypatch):
    found = {"functional": None, "handoff": None}

    def loader(kind):
        def load(task):
            value = found[kind]
            if isinstance(value, Exception):
                raise value
            return value
        return load
    monkeypatch.setattr(fv, "load_contract", loader("functional"))
    monkeypatch.setattr(artifact_handoff, "load_handoff_contract", loader("handoff"))
    monkeypatch.setattr(durable_execution, "load_input_binding", lambda task: None)
    return found


def test_frozen_base_reads_either_contract(contracts):
    task = SimpleNamespace(id="t")
    assert fv.frozen_base(task) == ""
    contracts["functional"] = {"base_commit": BASE}
    assert fv.frozen_base(task) == BASE
    contracts["handoff"] = {"base_commit": BASE}
    assert fv.frozen_base(task) == BASE
    contracts["functional"] = None
    assert fv.frozen_base(task) == BASE


def test_frozen_base_is_empty_when_contracts_conflict_or_are_unreadable(contracts):
    task = SimpleNamespace(id="t")
    contracts.update(functional={"base_commit": BASE}, handoff={"base_commit": OTHER})
    assert fv.frozen_base(task) == ""
    contracts.update(functional=TaskStoreError("functional_contract_invalid_or_stale"), handoff=None)
    assert fv.frozen_base(task) == ""  # validation reports the bad contract later, as before
    contracts.update(functional={"base_commit": "main"})
    assert fv.frozen_base(task) == ""


def test_resume_kwargs_fall_back_to_the_frozen_base(contracts):
    contracts["functional"] = {"base_commit": BASE}
    task = SimpleNamespace(id="t", executor_kind="opencode", binding_ref="", model_profile_ref="m", branch="")
    assert durable_execution._build_resume_executor_kwargs(stored_task=task)["base_ref"] == BASE
    # An explicit branch (native agents, same-model retries) still wins.
    task.branch = OTHER
    assert durable_execution._build_resume_executor_kwargs(stored_task=task)["base_ref"] == OTHER


def test_task_execution_kwargs_fall_back_to_the_frozen_base(contracts, monkeypatch):
    contracts["handoff"] = {"base_commit": BASE}
    monkeypatch.setattr(artifact_handoff, "bind_consumer_input", lambda store, task_id: None)
    store = SimpleNamespace(get_task=lambda task_id: SimpleNamespace(id=task_id))
    task = {"id": "t", "executor_kind": "opencode", "binding_ref": "", "model_profile_ref": "m", "branch": ""}
    assert task_execution._build_executor_kwargs(task, store=store)["base_ref"] == BASE
    assert task_execution._build_executor_kwargs(task)["base_ref"] == ""  # no store: unchanged


def test_a_worktree_prepared_elsewhere_is_refused_before_any_model_call(contracts, monkeypatch):
    task = SimpleNamespace(id="t")
    durable_execution._require_frozen_base(task, OTHER)  # no contract: nothing to hold to
    contracts["functional"] = {"base_commit": BASE}
    durable_execution._require_frozen_base(task, BASE)
    with pytest.raises(TaskStoreError, match="functional_base_mismatch"):
        durable_execution._require_frozen_base(task, OTHER)
    # An artifact consumer is bound to its producer's commit instead.
    monkeypatch.setattr(durable_execution, "load_input_binding", lambda task: {"base_commit": OTHER})
    durable_execution._require_frozen_base(task, OTHER)
