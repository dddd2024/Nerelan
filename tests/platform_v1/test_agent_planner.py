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


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                          text=True).stdout.strip()


def _planner(tmp_path, goals, runner, roster=("claude_code", "claude-opus")):
    repo = tmp_path / "source"
    if not repo.exists():
        repo.mkdir()
        _git(repo, "init")
        (repo / ".gitignore").write_text(".nt/\n", encoding="utf-8")
        (repo / "tracked.txt").write_text("base", encoding="utf-8")
        _git(repo, "add", ".")
        _git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
             "commit", "-m", "fixture")
    calls = []

    def run(**kwargs):
        calls.append(kwargs)
        return runner(**kwargs)
    return AgentPlanner(goal_service=goals, roster_resolver=lambda role: roster,
                        binding_model=lambda ref: {"claude-opus": "opus"}[ref],
                        repo_dir_for=lambda repository: str(repo), runner=run,
                        workspace_root=tmp_path / "workspaces"), calls


def test_planner_job_saves_role_tagged_plan_without_launching(tmp_path):
    goals, goal = _goals()
    planner, calls = _planner(tmp_path, goals, lambda **_: json.dumps(PLAN))
    status = planner.start(goal.id, expected_revision=1, background=False)
    assert status["status"] == "PLANNED" and status["planner"] == {"executor_kind": "claude_code", "binding_ref": "claude-opus"}
    assert calls[0]["executor_kind"] == "claude_code" and calls[0]["model_id"] == "opus"
    assert Path(calls[0]["repo_dir"]).parent == tmp_path / "workspaces" / "planner"
    assert not Path(calls[0]["repo_dir"]).exists()
    assert "Add a status page" in calls[0]["prompt"]
    saved = goals.control_store.get_goal(goal.id)
    assert saved.status == "PLANNED"
    assert [task.get("agent_role") for task in saved.tasks] == ["complex", "coder", "simple"]
    assert goals.control_store.list_goal_tasks(goal.id) == () or len(goals.control_store.list_goal_tasks(goal.id)) == 0


def test_planner_failures_are_finite_and_leave_the_goal_unplanned(tmp_path):
    goals, goal = _goals()
    planner, _ = _planner(tmp_path, goals, lambda **_: "I could not decide")
    assert planner.start(goal.id, expected_revision=1, background=False)["error"] == "agent_plan_not_json"
    assert goals.control_store.get_goal(goal.id).status == "DRAFT"
    bad_role = {"tasks": [{"id": "T001", "title": "x", "instruction": "y", "agent_role": "wizard"}]}
    planner, _ = _planner(tmp_path, goals, lambda **_: json.dumps(bad_role))
    assert planner.start(goal.id, expected_revision=1, background=False)["error"] == "unsupported_agent_role:wizard"


def test_planner_requires_native_planner_and_current_revision(tmp_path):
    goals, goal = _goals()
    planner, _ = _planner(tmp_path, goals, lambda **_: json.dumps(PLAN), roster=("opencode", "cheap"))
    with pytest.raises(TaskStoreError, match="agent_planner_requires_native_executor"):
        planner.start(goal.id, expected_revision=1, background=False)
    planner, _ = _planner(tmp_path, goals, lambda **_: json.dumps(PLAN))
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
    planner, _ = _planner(tmp_path, goals, lambda **_: json.dumps(PLAN))
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


def test_planner_never_overwrites_a_plan_saved_while_it_ran(tmp_path):
    goals, goal = _goals()

    def owner_saves_first(**_):
        goals.plan(goal.id, expected_revision=1, tasks=[{"id": "T001", "title": "Owner", "instruction": "Owner plan"}])
        return json.dumps(PLAN)
    planner, _ = _planner(tmp_path, goals, owner_saves_first)
    status = planner.start(goal.id, expected_revision=1, background=False)
    assert status["status"] == "FAILED" and status["error"] == "goal_changed_during_planning"
    assert [task["title"] for task in goals.control_store.get_goal(goal.id).tasks] == ["Owner"]


def test_planner_only_runs_for_agent_team_goals(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    goals = GoalService(store=store, control_store=control)
    goal = goals.create({"objective": "Fixture goal", "repository": "dddd2024/Nerelan", "idempotency_key": "plan-fixture",
                         "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    planner, calls = _planner(tmp_path, goals, lambda **_: json.dumps(PLAN))
    with pytest.raises(TaskStoreError, match="agent_planner_requires_agent_team_goal"):
        planner.start(goal.id, expected_revision=1, background=False)
    assert calls == []


def test_planned_chain_hands_artifacts_to_dependent_tasks(tmp_path):
    checks = [{"profile_id": "python_pytest", "working_directory": "."}]
    chain = {"tasks": [
        {"id": "T001", "title": "Implement", "instruction": "Implement it", "agent_role": "coder", "validation_checks": checks},
        {"id": "T002", "title": "Docs", "instruction": "Document the change", "agent_role": "simple",
         "dependencies": ["T001"], "artifact_input": {"plan_task_id": "T001"}, "validation_checks": checks},
    ], "acceptance_criteria": ["Works and is documented"]}
    goals, goal = _goals()
    planner, _ = _planner(tmp_path, goals, lambda **_: json.dumps(chain))
    status = planner.start(goal.id, expected_revision=1, background=False)
    assert status["status"] == "PLANNED" and status["usage_status"] == "unknown"
    saved = goals.control_store.get_goal(goal.id).tasks
    assert saved[1]["artifact_input"] == {"plan_task_id": "T001"} and saved[0]["validation_checks"]


def test_planned_artifact_without_checks_is_rejected_by_plan_validation(tmp_path):
    bad = {"tasks": [
        {"id": "T001", "title": "Implement", "instruction": "Implement it"},
        {"id": "T002", "title": "Docs", "instruction": "Docs", "dependencies": ["T001"],
         "artifact_input": {"plan_task_id": "T001"}},
    ]}
    goals, goal = _goals()
    planner, _ = _planner(tmp_path, goals, lambda **_: json.dumps(bad))
    status = planner.start(goal.id, expected_revision=1, background=False)
    assert status["status"] == "FAILED" and status["error"].startswith("artifact_input_requires_functional_checks")


def test_prompt_explains_artifact_handoff_and_check_catalog():
    prompt = build_planner_prompt(objective="x", repository="o/r")
    assert "artifact_input" in prompt and "python_pytest" in prompt and "npm_test" in prompt
    assert "targets" in prompt and "within 600 seconds" in prompt  # fast, focused checks


def test_consecutive_runs_use_fresh_real_scratch_and_preserve_source(tmp_path):
    from reverse_agent.platform_v1 import codex_executor, agent_planner
    goals, goal = _goals()
    seen = []

    def detached_runner(**kwargs):
        workspace = Path(kwargs["repo_dir"])
        assert subprocess.run(["git", "symbolic-ref", "-q", "HEAD"], cwd=workspace,
                              capture_output=True).returncode == 1
        environment = codex_executor._task_temp_env(workspace, {})
        assert Path(environment["TMP"]).parent == workspace
        assert Path(environment["TMP"]).name.startswith(".nt-")
        seen.append(workspace)
        return agent_planner.PlannerOutput(json.dumps(PLAN), {"input_tokens": 7})

    planner, _ = _planner(tmp_path, goals, detached_runner)
    source = tmp_path / "source"
    (source / "tracked.txt").write_text("owner edits", encoding="utf-8")
    (source / "untracked.txt").write_text("owner work", encoding="utf-8")
    before = _git(source, "status", "--porcelain", "--ignored")
    for _ in range(2):
        status = planner.start(goal.id, expected_revision=1, background=False)
        assert status["status"] == "PLANNED"
        assert status["token_usage"] == {"input_tokens": 7}
    assert len(set(seen)) == 2 and all(not path.exists() for path in seen)
    assert not list(source.glob(".nt*"))
    assert _git(source, "status", "--porcelain", "--ignored") == before
    assert (source / "tracked.txt").read_text() == "owner edits"
    assert (source / "untracked.txt").read_text() == "owner work"
    assert len(_git(source, "worktree", "list", "--porcelain").split("worktree ")) == 2


@pytest.mark.parametrize("explicit", [False, True])
def test_base_is_captured_before_background_dispatch(tmp_path, monkeypatch, explicit):
    from reverse_agent.platform_v1 import agent_planner
    goals, goal = _goals()
    observed = []
    planner, _ = _planner(tmp_path, goals, lambda **kw: (
        observed.append(_git(Path(kw["repo_dir"]), "rev-parse", "HEAD")) or json.dumps(PLAN)))
    source = tmp_path / "source"
    first = _git(source, "rev-parse", "HEAD")

    def advance():
        (source / "tracked.txt").write_text("next", encoding="utf-8")
        _git(source, "add", "tracked.txt")
        _git(source, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
             "commit", "-m", "next")

    if explicit:
        advance()
    pending = []

    class DeferredThread:
        def __init__(self, *, target, **_):
            pending.append(target)
        def start(self):
            pass

    from types import SimpleNamespace
    monkeypatch.setattr(agent_planner, "threading", SimpleNamespace(Thread=DeferredThread))
    kwargs = {"base_commit": first} if explicit else {}
    assert planner.start(goal.id, expected_revision=1, **kwargs)["status"] == "RUNNING"
    if not explicit:
        advance()
    pending.pop()()
    assert planner.status(goal.id)["status"] == "PLANNED"
    assert observed == [first]
    assert _git(source, "rev-parse", "HEAD") != first


@pytest.mark.parametrize("failure,code", [
    ("parse", "agent_plan_not_json"),
    ("unexpected", "agent_planner_error:ValueError"),
    ("native_task_temp_unavailable:C:/private/output", "agent_planner_error:native_task_temp_unavailable"),
    ("codex_cli_missing:raw output", "agent_planner_error:codex_cli_missing"),
    ("planner_git_failed:private output", "agent_planner_error:planner_git_failed"),
    ("arbitrary_private_message", "agent_planner_error:ExecutorRuntimeError"),
])
def test_failure_cleanup_and_safe_runtime_codes(tmp_path, failure, code):
    from reverse_agent.platform_v1 import codex_executor, task_runtime
    goals, goal = _goals()
    seen = []

    def runner(**kw):
        workspace = Path(kw["repo_dir"])
        seen.append(workspace)
        codex_executor._task_temp_env(workspace, {})
        if failure == "parse":
            return "not json"
        if failure == "unexpected":
            raise ValueError("private output")
        raise task_runtime.ExecutorRuntimeError(failure)

    planner, _ = _planner(tmp_path, goals, runner)
    status = planner.start(goal.id, expected_revision=1, background=False)
    assert status["status"] == "FAILED" and status["error"] == code
    assert len(seen) == 1 and not seen[0].exists()
    assert not list((tmp_path / "source").glob(".nt*"))
    assert goals.control_store.get_goal(goal.id).status == "DRAFT"
    if failure != "parse":
        assert "raw_excerpt" not in status


def test_concurrent_goals_have_distinct_workspaces(tmp_path):
    import threading
    from reverse_agent.platform_v1 import codex_executor
    goals, goal = _goals()
    other = goals.create({"objective": "Other", "repository": goal.repository,
                          "idempotency_key": "other", "executor_kind": "opencode",
                          "orchestration_mode": "agent_team", "binding_ref": ""})
    barrier = threading.Barrier(3)
    release = threading.Event()
    seen = []

    def runner(**kw):
        workspace = Path(kw["repo_dir"])
        codex_executor._task_temp_env(workspace, {})
        seen.append(workspace)
        barrier.wait(timeout=10)
        assert release.wait(timeout=10)
        return json.dumps(PLAN)

    planner, _ = _planner(tmp_path, goals, runner)
    workers = [threading.Thread(target=lambda g=g: planner.start(g.id, expected_revision=1, background=False))
               for g in (goal, other)]
    for worker in workers:
        worker.start()
    try:
        try:
            barrier.wait(timeout=10)
        except threading.BrokenBarrierError:
            pytest.fail(repr([planner.status(g.id) for g in (goal, other)]))
        assert len(set(seen)) == 2 and all(path.exists() for path in seen)
    finally:
        release.set()
        for worker in workers:
            worker.join(timeout=15)
    assert all(not worker.is_alive() for worker in workers)
    assert all(planner.status(g.id)["status"] == "PLANNED" for g in (goal, other))
    assert all(not path.exists() for path in seen)


def test_planner_start_recovers_crashed_workspace(tmp_path):
    goals, goal = _goals()
    planner, _ = _planner(tmp_path, goals, lambda **_: json.dumps(PLAN))
    source = tmp_path / "source"
    root = tmp_path / "workspaces"
    script = (
        "import os,sys; from reverse_agent.platform_v1.repository_preparation import planner_worktree; "
        "ctx=planner_worktree(sys.argv[1],sys.argv[2],'crashed',1); "
        "path,_=ctx.__enter__(); print(path,flush=True); os._exit(0)"
    )
    crashed = Path(subprocess.run([sys.executable, "-c", script, str(source), str(root)],
                                  capture_output=True, text=True, check=True).stdout.strip())
    assert crashed.exists()
    assert planner.start(goal.id, expected_revision=1, background=False)["status"] == "PLANNED"
    assert not crashed.exists()


@pytest.mark.parametrize("base", ["-invalid", "missing-reference", ""])
def test_base_capture_failure_is_safe_and_does_not_invoke_runner(tmp_path, base):
    goals, goal = _goals()
    planner, calls = _planner(tmp_path, goals, lambda **_: pytest.fail("runner must not start"))
    status = planner.start(goal.id, expected_revision=1, background=False, base_commit=base)
    assert status["status"] == "FAILED"
    assert status["error"] in {"agent_planner_error:planner_base_invalid", "agent_planner_error:planner_git_failed"}
    assert not calls
    assert not list((tmp_path / "source").glob(".nt*"))


@pytest.mark.parametrize("args", [(), (object(),), ("private/path",), ("codex_cli_missing raw output",)])
def test_runtime_error_without_known_code_uses_class_name(tmp_path, args):
    from reverse_agent.platform_v1 import task_runtime
    goals, goal = _goals()

    def fail(**_):
        raise task_runtime.ExecutorRuntimeError(*args)

    planner, _ = _planner(tmp_path, goals, fail)
    status = planner.start(goal.id, expected_revision=1, background=False)
    assert status["error"] == "agent_planner_error:ExecutorRuntimeError"
    assert "raw_excerpt" not in status


@pytest.mark.parametrize("persistent", [False, True])
def test_planner_path_retry_keeps_canonical_path_guard(tmp_path, monkeypatch, persistent):
    from reverse_agent.platform_v1 import repository_preparation, task_runtime
    original = repository_preparation.Path.resolve
    calls = []

    def resolve(path, *args, **kwargs):
        if path == tmp_path:
            calls.append(path)
            if persistent or len(calls) == 1:
                return tmp_path / "different"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(repository_preparation.Path, "resolve", resolve)
    if persistent:
        with pytest.raises(task_runtime.ExecutorRuntimeError, match="planner_path_invalid"):
            repository_preparation._planner_path(tmp_path)
    else:
        assert repository_preparation._planner_path(tmp_path) == tmp_path
    assert len(calls) == 2


def test_planner_prompt_sizes_work_for_a_wide_model_pool():
    # #1313: difficulty 4-5 tasks have almost no qualifying models and stall on quota holds.
    from reverse_agent.platform_v1.agent_planner import build_planner_prompt
    prompt = build_planner_prompt(objective="Build a feature", repository="owner/repo")
    assert "most tasks are difficulty 3 or lower" in prompt
    assert "use 5 only for one irreducible core step" in prompt
    assert "split the work rather than lowering a rating" in prompt
