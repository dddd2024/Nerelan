"""Real local subprocess/Git fixtures, with zero model or provider calls."""

import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.codex_executor import (
    CodexExecutor, CodexPreparedContext, build_codex_argv, codex_child_env, validate_codex_model,
)
from reverse_agent.platform_v1.opencode_executor import RoleContext
from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True).stdout.strip()


@pytest.fixture
def repository(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "fixture.txt").write_text("original\n")
    git(repo, "add", "fixture.txt")
    git(repo, "commit", "-m", "fixture")
    return repo, git(repo, "rev-parse", "HEAD")


def fixture_executor(repo, base, script, *, timeout=5):
    launched = []
    def factory(argv, **kwargs):
        assert argv[1:5] == ["exec", "--ignore-user-config", "--ephemeral", "--json"]
        assert argv[-1] == "-" and kwargs["shell"] is False
        assert "OPENAI_API_KEY" not in kwargs["env"]
        proc = subprocess.Popen([sys.executable, "-u", "-c", script], **kwargs)
        launched.append(proc)
        return proc
    executor = CodexExecutor(model_id="gpt-5.4", repo_dir=str(repo), base_ref=base,
        codex_exe=sys.executable, timeout=timeout, process_factory=factory,
        readiness_probe=lambda _: "managed_login_ready",
        parent_env={"PATH": str(Path(sys.executable).parent), "OPENAI_API_KEY": "fixture-secret"})
    return executor, launched


EVENTS = [
    {"type": "thread.started", "thread_id": "fixture-thread"},
    {"type": "turn.started"},
    {"type": "item.completed", "item": {"type": "agent_message", "text": "Readable fixture result"}},
    {"type": "turn.completed"},
]
SUCCESS_SCRIPT = "import sys,json;sys.stdin.read();print(" + repr("\n".join(json.dumps(e) for e in EVENTS)) + ")"


def test_native_subprocess_worktree_progress_and_final_response(repository, tmp_path):
    repo, base = repository
    edit_script = "from pathlib import Path;Path('fixture.txt').write_text('updated\\n');" + SUCCESS_SCRIPT
    executor, launched = fixture_executor(repo, base, edit_script)
    seen = []
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Bounded fixture instruction"))
    result = executor.execute("native-1", store, workspace_root=str(tmp_path / "workspaces"),
        event_callback=lambda _, event: seen.append(event))
    assert result.success and result.process_exit_code == 0
    assert result.validation_command_id == "git_diff_check"
    assert git(Path(result.workspace), "rev-parse", "HEAD") == base
    assert git(repo, "status", "--porcelain") == ""
    assert len(launched) == 1 and launched[0].poll() == 0
    final = next(e for e in seen if e["type"] == "EXECUTOR_COMPLETED")
    assert final["metadata"]["final_text"] == "Readable fixture result"
    assert final["metadata"]["usage_status"] == "unknown"
    assert final["metadata"]["cost_status"] == "unknown"
    # The agent's own session id is the exact join key to upstream request logs
    # (Magpie reports the same value), so it must survive into the event.
    assert final["metadata"]["agent_session_id"] == "fixture-thread"
    assert any(e["type"] == "EXECUTOR_PROGRESS" for e in seen)


def test_native_noop_turn_is_not_accepted_as_implementation(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(
        title="Change fixture.txt so the requested regression passes"))
    result = executor.execute("native-noop", store,
        workspace_root=str(tmp_path / "workspaces"))
    assert not result.success
    assert result.failure_classification == "codex_no_product_changes"
    assert result.validation_command_id == "git_diff_check"
    assert result.validation_exit_code == 0  # Patch hygiene alone is green.
    assert result.process_exit_code == 0
    assert not result.changed_files
    assert git(Path(result.workspace), "status", "--short") == ""
    assert len(launched) == 1 and launched[0].poll() == 0


@pytest.mark.parametrize("write_product", [False, True])
def test_native_bytecode_only_cannot_mask_no_product_changes(repository, tmp_path, write_product):
    repo, base = repository
    generate = (
        "from pathlib import Path;"
        "Path('__pycache__').mkdir();"
        "Path('__pycache__/fixture.cpython-313.pyc').write_bytes(b'compiled');"
    )
    if write_product:
        generate += "Path('fixture.txt').write_text('changed\\n');"
    executor, _ = fixture_executor(repo, base, generate + SUCCESS_SCRIPT)
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Change fixture.txt"))
    result = executor.execute("bytecode-work", store,
        workspace_root=str(tmp_path / "workspaces"))
    assert result.process_exit_code == result.validation_exit_code == 0
    if write_product:
        assert result.success
        assert [item["path"] for item in result.changed_files] == ["fixture.txt"]
    else:
        assert not result.success
        assert result.failure_classification == "codex_no_product_changes"
        assert not result.changed_files
    assert (Path(result.workspace) / "__pycache__" / "fixture.cpython-313.pyc").exists()


def test_literal_posix_backslash_cannot_hide_tracked_bytecode(monkeypatch, tmp_path):
    """Git byte paths must not be folded across POSIX backslash/slash identities."""
    from reverse_agent.platform_v1 import opencode_executor as collector

    def fake_ls_files(argv, **_kwargs):
        if argv[:3] != ["git", "ls-files", "--others"]:
            assert argv[:3] == ["git", "diff", "--no-renames"]
            return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
        return SimpleNamespace(
            returncode=0,
            stdout=b"__pycache__" + bytes([92]) + b"fixture.pyc" + bytes([0]),
            stderr=b"",
        )

    monkeypatch.setattr(collector.subprocess, "run", fake_ls_files)
    monkeypatch.setattr(collector, "_collect_changed_files", lambda _root: [
        {"path": "__pycache__/fixture.pyc", "status": "modified"}
    ])
    files = collector._collect_final_product_files(tmp_path)
    assert [f["path"] for f in files] == ["__pycache__/fixture.pyc"]


def test_head_tracked_change_wins_over_untracked_cache_view(monkeypatch, tmp_path):
    """The same path in the HEAD delta must remain product evidence."""
    from reverse_agent.platform_v1 import opencode_executor as collector

    path = "__pycache__/original.pyc"

    def fake_git(argv, **_kwargs):
        assert argv[0] == "git"
        if argv[1] == "ls-files":
            return SimpleNamespace(returncode=0, stdout=path.encode() + bytes([0]))
        assert argv[1] == "diff"
        return SimpleNamespace(returncode=0, stdout=path.encode() + bytes([0]))

    monkeypatch.setattr(collector.subprocess, "run", fake_git)
    monkeypatch.setattr(collector, "_collect_changed_files", lambda _root: [
        {"path": path, "status": "modified"}
    ])
    assert collector._collect_final_product_files(tmp_path) == [
        {"path": path, "status": "modified"}
    ]


def test_tracked_python_bytecode_still_counts_as_product_change(repository):
    from reverse_agent.platform_v1.opencode_executor import _collect_final_product_files
    repo, _ = repository
    cache = repo / "__pycache__"
    cache.mkdir()
    tracked = cache / "intentionally-tracked.pyc"
    tracked.write_bytes(b"original")
    git(repo, "add", "--", "__pycache__/intentionally-tracked.pyc")
    git(repo, "commit", "-m", "track binary fixture")
    tracked.write_bytes(b"changed")
    (cache / "runtime.pyc").write_bytes(b"generated")
    files = _collect_final_product_files(repo)
    assert [item["path"] for item in files] == ["__pycache__/intentionally-tracked.pyc"]


@pytest.mark.parametrize("helper_fields", [
    {"status": "failed", "exit_code": -1},
    {"aggregated_output": "helper_unknown_error: setup refresh had errors"},
])
def test_native_cli_helper_failure_prevents_false_ready_for_review(repository, tmp_path, helper_fields):
    repo, base = repository
    # Codex may report turn.completed and exit 0 even when its sandbox helper
    # failed before creating the requested child process.
    events = [
        {"type": "thread.started", "thread_id": "helper-failed"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {
            "type": "command_execution", "command": "git rev-parse HEAD",
            **helper_fields,
        }},
        {"type": "item.completed", "item": {
            "type": "agent_message", "text": "BLOCKED - helper_unknown_error",
        }},
        {"type": "turn.completed"},
    ]
    script = "import sys,json;sys.stdin.read();print(" + repr(
        "\n".join(json.dumps(event) for event in events)
    ) + ")"
    executor, launched = fixture_executor(repo, base, script)
    seen = []
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Read-only smoke"))
    result = executor.execute("native-helper-1", store,
        workspace_root=str(tmp_path / "workspaces"),
        event_callback=lambda _, event: seen.append(event))
    assert not result.success
    assert result.failure_classification == "codex_tool_launch_failed"
    assert result.validation_command_id == ""
    assert result.validation_exit_code == -1
    assert all(event["type"] != "EXECUTOR_COMPLETED" for event in seen)
    assert any(event["type"] == "EXECUTOR_PROGRESS" for event in seen)
    assert len(launched) == 1 and launched[0].poll() == 0


@pytest.mark.parametrize("script,classification", [
    ("import sys;sys.stdin.read();print('invalid json')", "codex_invalid_jsonl"),
    (SUCCESS_SCRIPT + ";raise SystemExit(7)", "codex_process_failed"),
    ("import sys;sys.stdin.read();sys.stderr.write('Authorization: Bearer private-token')", "codex_turn_incomplete"),
])
def test_process_and_protocol_failures_remain_failures(repository, tmp_path, script, classification):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, script)
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Fixture"))
    result = executor.execute("native-1", store, workspace_root=str(tmp_path / "workspaces"))
    assert not result.success and result.failure_classification == classification
    assert "private-token" not in repr(result)
    assert len(launched) == 1 and launched[0].poll() is not None


def test_timeout_is_bounded_and_terminates_only_owned_fixture_process(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base,
        "import sys,time;sys.stdin.read();time.sleep(30)", timeout=0.2)
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Fixture"))
    result = executor.execute("native-1", store, workspace_root=str(tmp_path / "workspaces"))
    assert result.failure_classification == "codex_timeout"
    assert launched[0].poll() is not None


def test_resume_preserves_native_identity_and_never_prepares_or_dispatches(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    original = executor.prepare_worktree_once("native-1", tmp_path / "workspaces")
    prepared = executor.reconstruct_prepared_context(worktree_path=str(original.worktree), base_sha=base, execution_id="exec-native-1")
    assert prepared.executor_kind == "codex" and prepared.base_sha == base
    assert not launched
    with pytest.raises(ExecutorRuntimeError, match="codex_worktree_head_mismatch"):
        executor.reconstruct_prepared_context(worktree_path=str(original.worktree), base_sha="0" * 40, execution_id="exec-native-1")
    with pytest.raises(ExecutorRuntimeError, match="codex_worktree_identity_invalid"):
        executor.reconstruct_prepared_context(worktree_path=str(repo), base_sha=base, execution_id="exec-native-1")
    assert not launched


def test_unsupported_role_and_wrong_prepared_identity_deny_before_dispatch(repository):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    prepared = CodexPreparedContext(repo, base, "exec-native-1", sys.executable)
    with pytest.raises(ExecutorRuntimeError, match="codex_single_mode_only"):
        executor.execute_role_prepared(prepared, None, role_context=RoleContext("reviewer", "native-1", repo))
    with pytest.raises(ExecutorRuntimeError, match="codex_task_identity_mismatch"):
        executor.execute_role_prepared(prepared, None, role_context=RoleContext("executor", "other-task", repo))
    assert not launched


def test_existing_workspace_is_preserved_and_floating_base_denied(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    root = tmp_path / "workspaces"
    existing = root / "native-1"
    existing.mkdir(parents=True)
    (existing / "preserve.txt").write_text("owner content")
    with pytest.raises(ExecutorRuntimeError, match="workspace_destination_exists"):
        executor.prepare_worktree_once("native-1", root)
    assert (existing / "preserve.txt").read_text() == "owner content"
    executor._base_ref = "main"
    with pytest.raises(ExecutorRuntimeError, match="codex_requires_exact_base_sha"):
        executor.prepare_worktree_once("native-2", root)
    assert not launched


def test_child_environment_and_argv_preserve_policy_and_exclude_provider_authority():
    env = codex_child_env({"Path": "safe", "CODEX_HOME": "managed-login-home",
        "OPENAI_API_KEY": "secret", "OPENAI_BASE_URL": "https://untrusted.invalid",
        "OPENCODE_CONFIG_CONTENT": "private", "HTTP_PROXY": "http://user:password@host"})
    assert env == {"Path": "safe", "CODEX_HOME": "managed-login-home"}
    argv = build_codex_argv("native.exe", Path("owned space"), "gpt-5.4", "workspace-write")
    assert "owned space" in argv and "--ignore-rules" not in argv
    assert "--dangerously-bypass-approvals-and-sandbox" not in argv
    assert "--sandbox" in argv and argv[-1] == "-"
    assert "--ignore-user-config" in argv
    if sys.platform == "win32":
        assert 'windows.sandbox="elevated"' in argv
    with pytest.raises(ExecutorRuntimeError, match="codex_sandbox_invalid"):
        build_codex_argv("native.exe", Path("."), "gpt-5.4", "danger-full-access")


def test_project_provider_or_hook_configuration_is_denied_without_dispatch(repository, tmp_path):
    repo, base = repository
    executor, launched = fixture_executor(repo, base, SUCCESS_SCRIPT)
    prepared = executor.prepare_worktree_once("native-1", tmp_path / "workspaces")
    directory = prepared.worktree / ".codex"
    directory.mkdir()
    (directory / "config.toml").write_text('model_provider="unapproved-provider"\n')
    with pytest.raises(ExecutorRuntimeError, match="codex_project_configuration_unapproved"):
        executor.execute_role_prepared(prepared, None, role_context=RoleContext("executor", "native-1", prepared.worktree))
    assert not launched


@pytest.mark.parametrize("model", ["openai/gpt-5.4", "--flag", "gpt\n5", "", "a" * 129])
def test_opencode_prefixes_and_argv_injection_are_not_native_model_ids(model):
    with pytest.raises(ExecutorRuntimeError, match="codex_model_id_invalid"):
        validate_codex_model(model)


@pytest.mark.parametrize("kind", ["codex", "claude_code"])
def test_shared_executor_preserves_structured_failure_reset(tmp_path, monkeypatch, kind):
    from reverse_agent.platform_v1.claude_executor import ClaudeCodeExecutor
    from reverse_agent.platform_v1.codex_protocol import CodexTurn
    from reverse_agent.platform_v1.run_store import TaskStore
    from reverse_agent.platform_v1.task_execution import TaskExecutionService
    from reverse_agent.platform_v1.task_runtime import ExecutorRouter
    from reverse_agent.platform_v1 import run_store

    monkeypatch.setattr(run_store, "_utc_now", lambda: "2026-10-19T11:00:00Z")
    executor_class = CodexExecutor if kind == "codex" else ClaudeCodeExecutor
    executor = object.__new__(executor_class)
    executor._model_id = "offline"
    executor._binding_resolution = None
    store = TaskStore(str(tmp_path / "tasks.db"))
    task = store.create_task(title="offline test")
    task_id = task.id
    workspace = tmp_path / task_id
    workspace.mkdir()
    prepared = SimpleNamespace(executor_kind=kind, worktree=workspace,
                               base_sha="a" * 40, execution_id=f"exec-{task_id}")
    turn = CodexTurn(failed=True, failure_classification=f"{kind}_usage_limit",
                     failure_detail="Historical diagnostics mention a different reset",
                     failure_reset_at="2026-10-19T16:00:00Z")
    monkeypatch.setattr(executor, "_verify_workspace", lambda *a: None)
    monkeypatch.setattr(executor, "_parser", lambda *a: SimpleNamespace(turn=turn, finish=lambda: turn))
    monkeypatch.setattr(executor, "_stream", lambda *a: 1)
    result = executor.execute_role_prepared(prepared, store,
        role_context=RoleContext("executor", task_id, workspace))
    assert result.failure_reset_at == "2026-10-19T16:00:00Z"
    assert not result.success

    class OfflineRouter(ExecutorRouter):
        def dispatch_execute(self, **kwargs):
            return result

    TaskExecutionService(store=store, router=OfflineRouter()).execute(task.id, workspace_root=str(tmp_path / "ws"))
    # Reopen to verify durable task storage, not only the in-memory result.
    reopened = TaskStore(str(tmp_path / "tasks.db"))
    persisted = reopened.get_task(task.id)
    assert persisted.failure_reset_at == result.failure_reset_at
    assert persisted.failure_at == "2026-10-19T11:00:00Z"
    assert persisted.failure_classification == turn.failure_classification
    reopened._conn.close()
    store._conn.close()


# --- end-to-end: executor session id -> task -> attributed cost ------------------
#
# Lives here because it needs the real subprocess fixture above. Everything after
# the executor is the production path: a real TaskStore, the real completion
# event, then the read-only cost report modules. No model call is made.

def _usage_csv(*rows: str) -> str:
    header = ("time,agent,provider,served_model,cost_usd,status,rejected,"
              "request_id,session,session_account,provider_key_id\n")
    return header + "".join(rows)


def test_agent_session_id_drives_exact_cost_attribution(repository, tmp_path):
    from reverse_agent.platform_v1.magpie_usage_ingest import (
        attempts_from_store, correlate_usage, economics_runs, parse_usage_csv,
    )
    from reverse_agent.platform_v1.orchestration_selector import all_in_economics
    from reverse_agent.platform_v1.run_store import TaskStore

    repo, base = repository
    store = TaskStore(":memory:")
    task = store.create_task(title="cost chain", executor_kind="codex",
                             binding_ref="binding-1", repository="o/r")
    # A run must produce a product diff, so the fixture edits the tracked file.
    edit_script = ("from pathlib import Path;Path('fixture.txt').write_text('updated\\n');"
                   + SUCCESS_SCRIPT)
    executor, launched = fixture_executor(repo, base, edit_script)

    def persist(task_id, event):
        store.add_event(task_id, event_type=event["type"], title=event.get("title", ""),
                        description=event.get("description", ""),
                        metadata=event.get("metadata") or {})

    result = executor.execute(task.id, store, workspace_root=str(tmp_path / "workspaces"),
                              event_callback=persist)
    assert result.success and len(launched) == 1

    # Mark execution readiness (not independent acceptance), far from usage rows.
    store._conn.execute(
        "UPDATE tasks SET status='READY_FOR_REVIEW', created_at=?, updated_at=? WHERE id=?",
        ("2026-11-01T09:00:00+00:00", "2026-11-01T09:10:00+00:00", task.id))
    store._conn.commit()

    attempts = attempts_from_store(store)
    mine = next(item for item in attempts if item["task_id"] == task.id)
    assert mine["agent_session_id"] == "fixture-thread", "executor must publish its session id"
    assert mine["accepted"] is True

    # Requests carrying that session id are attributed even two days away in time.
    rows = parse_usage_csv(_usage_csv(
        "2026-11-03T22:00:00+00:00,codex,openai,gpt-x,0.2500,200,false,req-1,fixture-thread,,fixture-key\n"))
    correlated = correlate_usage(rows, attempts)
    assert correlated["ambiguous"] == []
    assert correlated["attempts"][task.id]["requests"] == 1
    assert correlated["attempts"][task.id]["cash_cost_usd"] == 0.25

    economy = all_in_economics(economics_runs(correlated), basis="cash")["single"]
    assert economy["accepted_runs"] == 1
    # Exact session identity proves attribution, not export completeness.
    assert economy["cost_per_accepted_all_in"] is None
    assert economy["unpriced_runs"] == 1

    # Only this complete fixture can explicitly attest its full export interval.
    correlated = correlate_usage(rows, attempts, coverage_window=(mine["started_at"],
                                                                 mine["finished_at"]))
    complete = all_in_economics(economics_runs(correlated), basis="cash")["single"]
    assert complete["cost_per_accepted_all_in"] == 0.25
    assert complete["unpriced_runs"] == 0
