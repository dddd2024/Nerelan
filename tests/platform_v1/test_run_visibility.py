"""What a user can see while a task runs and after it stops."""
import json
import os
import sys

import pytest

from reverse_agent.platform_v1 import goal_service as gs
from reverse_agent.platform_v1 import opencode_executor as oe
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.run_read_model import RunReadModel
from reverse_agent.platform_v1.run_store import TaskStore
from test_contract_miss_fixup import case, wrong_tree  # noqa: F401 (fixture)
from test_goal_functional_checks import goal_checks  # noqa: F401 (fixture)


# --- live progress lines -------------------------------------------------------------------

def tool(name, **inputs):
    return {"type": "tool_use", "part": {"type": "tool", "tool": name, "state": {"status": "completed", "input": inputs}}}


@pytest.mark.parametrize("event, text, kind", [
    (tool("read", filePath="README.md"), "read README.md", "READ"),
    (tool("bash", command="python -m pytest -q tests"), "bash python -m pytest -q tests", "COMMAND"),
    (tool("edit", filePath="a.py", oldString="x", newString="y"), "edit a.py", "EDIT"),
    (tool("grep", pattern="def main"), "grep def main", "SEARCH"),
    (tool("todowrite"), "todowrite", "PLAN"),
    ({"type": "text", "part": {"type": "text", "text": "I'll add one line\n to the README."}},
     "I'll add one line to the README.", "PLAN"),
    ({"type": "error", "error": {"name": "APIError", "message": "429 Too Many Requests", "statusCode": 429}},
     None, "BLOCKED"),
])
def test_progress_summary_is_short_public_and_categorized(event, text, kind):
    summary = oe.progress_summary(event)
    assert summary is not None
    if text is not None:
        assert summary["text"] == text
    assert oe.progress_activity_kind(summary) == kind


def test_progress_summary_never_carries_tool_output_or_secrets():
    event = tool("bash", command="curl -H 'Authorization: Bearer sk-live-SECRETSECRETSECRET' x")
    event["part"]["state"]["output"] = "FILE CONTENTS THAT MUST NOT LEAVE"
    summary = oe.progress_summary(event)
    assert "SECRETSECRETSECRET" not in json.dumps(summary)
    assert "FILE CONTENTS" not in json.dumps(summary)
    assert oe.progress_summary({"type": "step_start"}) is None
    assert oe.progress_summary("not an event") is None


def test_sink_throttles_text_caps_count_and_survives_bad_lines(monkeypatch):
    sent = []
    sink = oe._progress_sink(lambda task_id, event: sent.append(event), "task-1", execution_id="exec-1", role="executor")
    sink(b"not json")
    text = json.dumps({"type": "text", "part": {"type": "text", "text": "thinking"}}).encode()
    sink(text)
    sink(text)  # within the text interval: dropped
    monkeypatch.setattr(oe, "MAX_PROGRESS_EVENTS", 3)
    for i in range(5):
        sink(json.dumps(tool("read", filePath=f"f{i}.py")).encode())
    assert [e["description"] for e in sent] == ["thinking", "read f0.py", "read f1.py"]
    assert all(e["type"] == "EXECUTOR_PROGRESS" for e in sent)
    assert sent[1]["metadata"]["activity_kind"] == "READ" and sent[1]["metadata"]["execution_id"] == "exec-1"
    assert oe._progress_sink(None, "task-1", execution_id="e", role="executor") is None


def test_lines_reach_the_sink_while_the_process_is_still_running():
    seen = []
    script = ("import json, time\n"
              "print(json.dumps({'type': 'tool_use', 'part': {'tool': 'read', 'state': {'input': {'filePath': 'a.py'}}}}), flush=True)\n"
              "time.sleep(1.5)\n"
              "print('tail-without-newline', end='', flush=True)\n")
    import time
    started = time.monotonic()
    token = oe._STDOUT_LINE_SINK.set(lambda line: seen.append((round(time.monotonic() - started, 1), line)))
    try:
        owned = oe._run_owned_cli_process([sys.executable, "-c", script], cwd=".", env=dict(os.environ),
                                          timeout=30, stall_seconds=None)
    finally:
        oe._STDOUT_LINE_SINK.reset(token)
    assert owned.returncode == 0
    assert len(seen) == 1 and b'"read"' in seen[0][1]
    assert seen[0][0] < 1.5  # delivered before the process slept and exited
    assert b"tail-without-newline" in owned.stdout if isinstance(owned.stdout, bytes) else "tail-without-newline" in owned.stdout


def test_a_failing_sink_never_affects_the_owned_process():
    def broken(line):
        raise RuntimeError("sink failure")
    token = oe._STDOUT_LINE_SINK.set(broken)
    try:
        owned = oe._run_owned_cli_process([sys.executable, "-c", "print('{}'); print('{}')"], cwd=".",
                                          env=dict(os.environ), timeout=30, stall_seconds=None)
    finally:
        oe._STDOUT_LINE_SINK.reset(token)
    assert owned.returncode == 0


# --- read model keeps the description of progress and stop events -----------------------------

def test_read_model_shows_progress_and_stop_explanations_but_not_other_descriptions():
    store = TaskStore()
    model = RunReadModel(store=store, control_store=PlatformControlStore(store))
    task = store.create_task(title="visible")
    store.add_event(task.id, event_type="EXECUTOR_PROGRESS", title="OpenCode", description="read README.md",
                    metadata={"activity_kind": "READ", "role": "executor"})
    store.add_event(task.id, event_type="EXECUTOR_FINISHED", title="OpenCode stalled",
                    description="OpenCode CLI wrote nothing for too long (often a provider 429 it waits out)",
                    metadata={"failure_classification": "executor_stalled", "role": "executor"})
    store.add_event(task.id, event_type="EXECUTOR_FINISHED", title="Read source", description="internal detail",
                    metadata={"activity_kind": "READ"})
    events = model.run_detail(task.id)["events"]
    by_desc = {e["description"] for e in events}
    assert "read README.md" in by_desc
    assert any("provider 429" in d for d in by_desc)
    assert "internal detail" not in by_desc


# --- goal detail: activity, failure and attempts ------------------------------------------------

def test_goal_detail_says_why_a_task_stopped_and_lists_earlier_attempts(case, monkeypatch):
    root, _, store, _, service, goal, _, task = case
    store.add_event(task.id, event_type="WORKSPACE_READY", title="Workspace ready",
                    metadata={"execution_id": task.execution_id, "workspace": str(root)})
    store.add_event(task.id, event_type="EXECUTOR_FINISHED", title="OpenCode stalled",
                    description="OpenCode CLI wrote nothing for too long (often a provider 429 it waits out)")
    store.add_event(task.id, event_type="EXECUTOR_FINISHED", title="Executor action evidence", description="step_start")
    # Old enough that the overload backoff has passed.
    store._conn.execute("UPDATE tasks SET status='FAILED', failure_classification='provider_overloaded', "
                        "failure_detail='overloaded', updated_at='2000-01-01T00:00:00Z' WHERE id=?", (task.id,))
    store._conn.commit()
    [step] = service.escalate_failed_tasks(goal.id)
    retry_id = step["to_task_id"]
    store.add_event(retry_id, event_type="EXECUTOR_PROGRESS", title="OpenCode", description="read README.md")

    [link] = [row for row in service.detail(goal.id)["task_links"] if row["task_id"] == retry_id]
    assert link["activity"]["description"] == "read README.md"
    assert link["failure"] is None  # the retry has not stopped
    [attempt] = link["attempts"]
    assert attempt["task_id"] == task.id and attempt["status"] == "FAILED"
    assert attempt["failure"]["classification"] == "provider_overloaded"
    # The bulk per-action evidence rows never stand in for the host's explanation.
    assert attempt["failure"]["message"].startswith("OpenCode stalled: OpenCode CLI wrote nothing")


def test_latest_events_skips_action_evidence_and_filters_types():
    store = TaskStore()
    task = store.create_task(title="t")
    store.add_event(task.id, event_type="EXECUTOR_RUNNING", title="OpenCode CLI started")
    store.add_event(task.id, event_type="EXECUTOR_FINISHED", title="Executor action evidence", description="tool_use")
    assert store.latest_events(task.id)[0]["title"] == "OpenCode CLI started"
    assert store.latest_events(task.id, types=("VALIDATED",)) == []
    assert len(store.latest_events(task.id, limit=10)) == 2  # DISCOVERED + started, evidence excluded
