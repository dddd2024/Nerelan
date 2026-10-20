"""Planner agent: decomposition into role-tagged tasks (zero model calls)."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from reverse_agent.platform_v1.agent_planner import (
    AgentPlanner, build_planner_prompt, extract_plan, run_planner_cli,
)
from reverse_agent.platform_v1.claude_executor import ClaudeCodeExecutor
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError

PLAN = {"tasks": [
    {"id": "T001", "title": "Design", "instruction": "Design the change", "agent_role": "complex"},
    {"id": "T002", "title": "Implement", "instruction": "Implement it", "agent_role": "coder", "dependencies": ["T001"]},
    {"id": "T003", "title": "Docs", "instruction": "Update docs", "agent_role": "simple", "dependencies": ["T002"]},
], "acceptance_criteria": ["Feature works", "Docs updated"]}


def test_prompt_names_roles_and_demands_json():
    prompt = build_planner_prompt(objective="Add a status page", repository="dddd2024/Nerelan")
    for token in ("Add a status page", "dddd2024/Nerelan", "simple", "complex", '"tasks"', "difficulty"):
        assert token in prompt


@pytest.mark.parametrize("text", [
    json.dumps(PLAN),
    "Here is the plan:\n```json\n" + json.dumps(PLAN) + "\n```",
    "Plan follows " + json.dumps(PLAN) + " end.",
])
def test_extract_plan_accepts_plain_fenced_and_embedded_json(text):
    plan = extract_plan(text)
    assert [task["agent_role"] for task in plan["tasks"]] == ["complex", "coder", "simple"]
    assert plan["acceptance_criteria"] == ["Feature works", "Docs updated"]


@pytest.mark.parametrize("text", [
    # JSON followed by prose whose braces would defeat the first-'{'..last-'}' slice.
    json.dumps(PLAN) + "\nThat covers {scope} and {more}.",
    # JSON preceded by prose containing braces.
    "Here is my {reasoning}:\n" + json.dumps(PLAN),
])
def test_extract_plan_tolerates_prose_with_braces(text):
    plan = extract_plan(text)
    assert [task["agent_role"] for task in plan["tasks"]] == ["complex", "coder", "simple"]
    assert plan["acceptance_criteria"] == ["Feature works", "Docs updated"]


def test_extract_plan_accepts_fenced_block_with_backticks_in_instruction():
    raw = {"tasks": [{"id": "T001", "title": "Wrap code", "agent_role": "coder",
                      "instruction": "Wrap the snippet in ```python\nx = 1\n``` blocks."}],
           "acceptance_criteria": ["Code wrapped"]}
    text = "```json\n" + json.dumps(raw) + "\n```"
    plan = extract_plan(text)
    assert plan["tasks"][0]["instruction"] == "Wrap the snippet in ```python\nx = 1\n``` blocks."
    assert plan["tasks"][0]["agent_role"] == "coder"


def test_extract_plan_strips_fields_a_planner_may_not_request():
    raw = {"tasks": [{"id": "T001", "title": "x", "instruction": "y", "capability": "validate_task",
                      "validation_command_id": "git_diff_check", "artifact_input": {"plan_task_id": "T0"}}]}
    assert extract_plan(json.dumps(raw))["tasks"] == [
        {"id": "T001", "title": "x", "instruction": "y", "artifact_input": {"plan_task_id": "T0"},
         "difficulty": 3, "kind": "code", "context_need": 0, "needs": ()}]


def test_reviewer_tasks_validate_without_changing_their_input():
    raw = {"tasks": [
        {"id": "T001", "title": "fix", "instruction": "fix", "agent_role": "coder"},
        {"id": "T002", "title": "review", "instruction": "review", "agent_role": "reviewer",
         "capability": "execute_task", "dependencies": ["T001"], "artifact_input": {"plan_task_id": "T001"}}]}
    first, review = extract_plan(json.dumps(raw))["tasks"]
    assert "capability" not in first  # GoalService defaults it to execute_task
    assert review["capability"] == "validate_task"  # derived from the role, never taken from the planner


@pytest.mark.parametrize("text,error", [
    ("", "agent_plan_empty"),
    ("no json here", "agent_plan_not_json"),
    ('{"tasks": []}', "agent_plan_tasks_required"),
    (json.dumps({"tasks": [{"id": f"T{i:03d}", "title": "t", "instruction": "i"} for i in range(1, 14)]}),
     "agent_plan_too_many_tasks"),
])
def test_extract_plan_rejects_bad_output(text, error):
    with pytest.raises(TaskStoreError, match=error):
        extract_plan(text)


def _goals():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)
    goal = goals.create({"objective": "Add a status page", "repository": "dddd2024/Nerelan",
                         "idempotency_key": "plan-goal-1", "executor_kind": "opencode",
                         "orchestration_mode": "agent_team", "binding_ref": ""})
    return goals, goal


def _planner(goals, runner, roster=("claude_code", "claude-opus")):
    calls = []

    def run(**kwargs):
        calls.append(kwargs)
        return runner(**kwargs)
    return AgentPlanner(goal_service=goals, roster_resolver=lambda role: roster,
                        binding_model=lambda ref: {"claude-opus": "opus"}[ref],
                        repo_dir_for=lambda repository: "/fixture/repo", runner=run), calls


def test_planner_job_saves_role_tagged_plan_without_launching():
    goals, goal = _goals()
    planner, calls = _planner(goals, lambda **_: json.dumps(PLAN))
    status = planner.start(goal.id, expected_revision=1, background=False)
    assert status["status"] == "PLANNED" and status["planner"] == {"executor_kind": "claude_code", "binding_ref": "claude-opus"}
    assert calls[0]["executor_kind"] == "claude_code" and calls[0]["model_id"] == "opus"
    assert calls[0]["repo_dir"] == "/fixture/repo" and "Add a status page" in calls[0]["prompt"]
    saved = goals.control_store.get_goal(goal.id)
    assert saved.status == "PLANNED"
    assert [task.get("agent_role") for task in saved.tasks] == ["complex", "coder", "simple"]
    assert goals.control_store.list_goal_tasks(goal.id) == () or len(goals.control_store.list_goal_tasks(goal.id)) == 0


def test_planner_failures_are_finite_and_leave_the_goal_unplanned():
    goals, goal = _goals()
    planner, _ = _planner(goals, lambda **_: "I could not decide")
    assert planner.start(goal.id, expected_revision=1, background=False)["error"] == "agent_plan_not_json"
    assert goals.control_store.get_goal(goal.id).status == "DRAFT"
    bad_role = {"tasks": [{"id": "T001", "title": "x", "instruction": "y", "agent_role": "wizard"}]}
    planner, _ = _planner(goals, lambda **_: json.dumps(bad_role))
    assert planner.start(goal.id, expected_revision=1, background=False)["error"] == "unsupported_agent_role:wizard"


def test_planner_requires_native_planner_and_current_revision():
    goals, goal = _goals()
    planner, _ = _planner(goals, lambda **_: json.dumps(PLAN), roster=("opencode", "cheap"))
    with pytest.raises(TaskStoreError, match="agent_planner_requires_native_executor"):
        planner.start(goal.id, expected_revision=1, background=False)
    planner, _ = _planner(goals, lambda **_: json.dumps(PLAN))
    with pytest.raises(TaskStoreError, match="goal_revision_mismatch"):
        planner.start(goal.id, expected_revision=2, background=False)


def test_read_only_cli_run_parses_claude_stream(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    events = [{"type": "system", "subtype": "init", "session_id": "plan-session"},
              {"type": "result", "subtype": "success", "is_error": False, "result": json.dumps(PLAN)}]
    script = "import sys,json;sys.stdin.read();print(" + repr("\n".join(json.dumps(e) for e in events)) + ")"
    seen = {}

    def factory(**kwargs):
        def process(argv, **popen):
            seen["argv"], seen["cwd"] = argv, popen["cwd"]
            return subprocess.Popen([sys.executable, "-u", "-c", script], **popen)
        return ClaudeCodeExecutor(claude_exe=sys.executable, process_factory=process,
                                  readiness_probe=lambda _: "managed_login_ready",
                                  parent_env={"PATH": str(Path(sys.executable).parent)}, **kwargs)

    output = run_planner_cli(executor_kind="claude_code", model_id="opus", repo_dir=str(repo),
                             prompt="plan it", executor_factory=factory)
    assert extract_plan(output.text)["tasks"][0]["agent_role"] == "complex"
    assert output.usage is None  # no usage in this stream: reported as unknown, never zero
    tools = seen["argv"][seen["argv"].index("--tools") + 1]
    assert tools == "Read,Glob,Grep" and Path(seen["cwd"]).resolve() == repo.resolve()


def test_agent_plan_http_routes(tmp_path):
    import threading
    from http.server import ThreadingHTTPServer
    from urllib.request import Request, urlopen
    from _local_client_fixture import client_headers, client_session
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter
    from reverse_agent.platform_v1.task_service import _handler_factory

    goals, goal = _goals()
    planner, _ = _planner(goals, lambda **_: json.dumps(PLAN))
    handler = _handler_factory(goals.store, ExecutorRouter(), allowed_origin="http://localhost:5173",
                               execution_authority_sha="fixture-authority", planning_sha="fixture-plan",
                               control_store=goals.control_store, goal_service=goals, agent_planner=planner,
                               local_client_session=client_session())
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        def call(method, path, payload=None):
            req = Request(base + path, method=method, data=None if payload is None else json.dumps(payload).encode(),
                          headers=client_headers({"Content-Type": "application/json"}))
            with urlopen(req, timeout=10) as response:
                return response.status, json.load(response)
        assert call("GET", f"/api/goals/{goal.id}/agent-plan") == (200, {"goal_id": goal.id, "status": "NONE", "error": ""})
        status, started = call("POST", f"/api/goals/{goal.id}/agent-plan", {"expected_revision": 1})
        assert status == 202 and started["status"] in {"RUNNING", "PLANNED"}
        for _ in range(50):
            _, current = call("GET", f"/api/goals/{goal.id}/agent-plan")
            if current["status"] != "RUNNING":
                break
            threading.Event().wait(0.05)
        assert current["status"] == "PLANNED"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_planner_never_overwrites_a_plan_saved_while_it_ran():
    goals, goal = _goals()

    def owner_saves_first(**_):
        goals.plan(goal.id, expected_revision=1, tasks=[{"id": "T001", "title": "Owner", "instruction": "Owner plan"}])
        return json.dumps(PLAN)
    planner, _ = _planner(goals, owner_saves_first)
    status = planner.start(goal.id, expected_revision=1, background=False)
    assert status["status"] == "FAILED" and status["error"] == "goal_changed_during_planning"
    assert [task["title"] for task in goals.control_store.get_goal(goal.id).tasks] == ["Owner"]


def test_planner_only_runs_for_agent_team_goals():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)
    goal = goals.create({"objective": "Fixture goal", "repository": "dddd2024/Nerelan", "idempotency_key": "plan-fixture",
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    planner, calls = _planner(goals, lambda **_: json.dumps(PLAN))
    with pytest.raises(TaskStoreError, match="agent_planner_requires_agent_team_goal"):
        planner.start(goal.id, expected_revision=1, background=False)
    assert calls == []


def test_planned_chain_hands_artifacts_to_dependent_tasks():
    checks = [{"profile_id": "python_pytest", "working_directory": "."}]
    chain = {"tasks": [
        {"id": "T001", "title": "Implement", "instruction": "Implement it", "agent_role": "coder", "validation_checks": checks},
        {"id": "T002", "title": "Docs", "instruction": "Document the change", "agent_role": "simple",
         "dependencies": ["T001"], "artifact_input": {"plan_task_id": "T001"}, "validation_checks": checks},
    ], "acceptance_criteria": ["Works and is documented"]}
    goals, goal = _goals()
    planner, _ = _planner(goals, lambda **_: json.dumps(chain))
    status = planner.start(goal.id, expected_revision=1, background=False)
    assert status["status"] == "PLANNED" and status["usage_status"] == "unknown"
    saved = goals.control_store.get_goal(goal.id).tasks
    assert saved[1]["artifact_input"] == {"plan_task_id": "T001"} and saved[0]["validation_checks"]


def test_planned_artifact_without_checks_is_rejected_by_plan_validation():
    bad = {"tasks": [
        {"id": "T001", "title": "Implement", "instruction": "Implement it"},
        {"id": "T002", "title": "Docs", "instruction": "Docs", "dependencies": ["T001"],
         "artifact_input": {"plan_task_id": "T001"}},
    ]}
    goals, goal = _goals()
    planner, _ = _planner(goals, lambda **_: json.dumps(bad))
    status = planner.start(goal.id, expected_revision=1, background=False)
    assert status["status"] == "FAILED" and status["error"].startswith("artifact_input_requires_functional_checks")


def test_prompt_explains_artifact_handoff_and_check_catalog():
    prompt = build_planner_prompt(objective="x", repository="o/r")
    assert "artifact_input" in prompt and "python_pytest" in prompt and "npm_test" in prompt
    assert "targets" in prompt and "within 600 seconds" in prompt  # fast, focused checks
