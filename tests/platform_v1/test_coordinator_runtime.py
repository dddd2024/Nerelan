from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from reverse_agent.platform_v1.coordinator import PlatformV1Coordinator
from reverse_agent.platform_v1.execution_adapters import (
    CodexExecutorAdapter,
    CommandResult,
    ExecutorResult,
    FailureClassifier,
    FakeCodexExecutorAdapter,
    GitWorktreeManager,
    LocalValidationRunner,
    redact_secrets,
)
from reverse_agent.platform_v1.issue_task import IssueTaskError, IssueTaskLoader
from reverse_agent.platform_v1.run_store import RunState, SQLiteRunStore


BASE = "1142dd324fdd4c4bf2a1353d9d5e93bc04b33507"


def _issue_body(**overrides: object) -> str:
    task: dict[str, object] = {
        "schema_version": 1,
        "repository": "dddd2024/reverse-agent",
        "base_sha": BASE,
        "goal": "Create one bounded evidence file.",
        "allowed_paths": ["examples/platform_v1_target/e2e_canary_115.txt"],
        "forbidden_operations": [
            "push_main",
            "merge",
            "mark_ready",
            "auto_merge",
            "force_push",
            "release",
            "deployment",
            "credential_access",
            "credential_publication",
        ],
        "required_checks": ["python -m pytest tests/platform_v1/test_cli.py -q", "git diff --check"],
        "target_branch": "agent/platform-v1-e2e-canary-115",
        "publication": "draft_pr",
        "risk_tier": "R1",
        "max_rework_attempts": 1,
    }
    task.update(overrides)
    return "# Canary\n\n```json\n" + json.dumps(task, indent=2) + "\n```\n"


def _issue(**overrides: object) -> dict[str, object]:
    issue: dict[str, object] = {
        "number": 115,
        "state": "OPEN",
        "body": _issue_body(),
        "labels": [{"name": "r1-approved"}, {"name": "work-item"}],
    }
    issue.update(overrides)
    return issue


def _events() -> list[dict[str, object]]:
    return [{
        "id": 9001,
        "event": "labeled",
        "label": {"name": "r1-approved"},
        "actor": {"login": "dddd2024"},
        "created_at": "2026-08-05T03:08:56Z",
    }]


def _task():
    return IssueTaskLoader.parse(
        issue=_issue(),
        events=_events(),
        expected_repository="dddd2024/reverse-agent",
        expected_base_sha=BASE,
    )


class TestIssueTaskLoader:
    def test_live_loader_forces_utf8_for_github_json(self) -> None:
        calls: list[dict[str, object]] = []

        def runner(argv, **kwargs):
            calls.append(kwargs)
            if argv[:3] == ["gh", "issue", "view"]:
                payload = _issue(body=_issue_body(goal="Create one file \u2192 verify it."))
            else:
                payload = _events()
            return subprocess.CompletedProcess(argv, 0, json.dumps(payload, ensure_ascii=False), "")

        loaded = IssueTaskLoader(runner=runner).load("dddd2024/reverse-agent", 115, BASE)
        assert loaded.work_item.source_issue_number == 115
        assert calls
        assert all(call["encoding"] == "utf-8" for call in calls)
        assert all(call["errors"] == "replace" for call in calls)

    def test_extracts_one_task_and_owner_approval(self) -> None:
        loaded = _task()
        assert loaded.work_item.source_issue_number == 115
        assert loaded.work_item.base_sha == BASE
        assert loaded.work_item.allowed_paths == ("examples/platform_v1_target/e2e_canary_115.txt",)
        assert loaded.approval.approved_by == "dddd2024"
        assert loaded.approval.approved_at == "2026-08-05T03:08:56Z"
        assert loaded.publication == "draft_pr"
        assert len(loaded.issue_body_sha256) == 64
        assert loaded.normalized_issue_body.startswith("# Canary")

    def test_task_and_execution_identity_are_stable(self) -> None:
        first = _task()
        second = _task()
        assert first.task_digest == second.task_digest
        assert first.execution_id == second.execution_id

    @pytest.mark.parametrize(
        ("issue_override", "task_override", "code"),
        [
            ({"state": "CLOSED"}, {}, "issue_not_open"),
            ({}, {"repository": "other/repo"}, "repository_mismatch"),
            ({}, {"base_sha": "0" * 40}, "base_mismatch"),
            ({}, {"target_branch": "main"}, "main_target_rejected"),
            ({}, {"allowed_paths": ["**/*"]}, "broad_path_rejected"),
            ({}, {"allowed_paths": ["../escape.txt"]}, "path_traversal_rejected"),
            ({}, {"allowed_paths": ["C:/secret.txt"]}, "absolute_path_rejected"),
            ({}, {"publication": "merge"}, "publication_rejected"),
        ],
    )
    def test_rejects_unsafe_authority(
        self,
        issue_override: dict[str, object],
        task_override: dict[str, object],
        code: str,
    ) -> None:
        issue = _issue(**issue_override)
        if task_override:
            issue["body"] = _issue_body(**task_override)
        with pytest.raises(IssueTaskError) as caught:
            IssueTaskLoader.parse(
                issue=issue,
                events=_events(),
                expected_repository="dddd2024/reverse-agent",
                expected_base_sha=BASE,
            )
        assert caught.value.code == code

    def test_rejects_multiple_machine_blocks(self) -> None:
        issue = _issue(body=_issue_body() + _issue_body())
        with pytest.raises(IssueTaskError) as caught:
            IssueTaskLoader.parse(
                issue=issue,
                events=_events(),
                expected_repository="dddd2024/reverse-agent",
                expected_base_sha=BASE,
            )
        assert caught.value.code == "task_block_count_invalid"

    def test_rejects_missing_owner_approval_event(self) -> None:
        with pytest.raises(IssueTaskError) as caught:
            IssueTaskLoader.parse(
                issue=_issue(),
                events=[],
                expected_repository="dddd2024/reverse-agent",
                expected_base_sha=BASE,
            )
        assert caught.value.code == "approval_event_missing"


class TestSQLiteRunStore:
    def test_persists_state_and_events_across_restart(self, tmp_path: Path) -> None:
        loaded = _task()
        database = tmp_path / "runs.sqlite3"
        store = SQLiteRunStore(database)
        run = store.get_or_create(loaded, str(tmp_path / loaded.execution_id))
        store.transition(run.execution_id, RunState.VALIDATED, detail={"source": "test"})
        store.close()

        reopened = SQLiteRunStore(database)
        observed = reopened.get(run.execution_id)
        assert observed is not None
        assert observed.state == RunState.VALIDATED
        assert [event.to_state for event in reopened.events(run.execution_id)] == [
            RunState.DISCOVERED,
            RunState.VALIDATED,
        ]

    def test_same_task_digest_reuses_one_active_execution(self, tmp_path: Path) -> None:
        store = SQLiteRunStore(tmp_path / "runs.sqlite3")
        first = store.get_or_create(_task(), str(tmp_path / "workspace"))
        second = store.get_or_create(_task(), str(tmp_path / "other-workspace"))
        assert second.execution_id == first.execution_id
        assert second.worktree_path == first.worktree_path
        assert store.count_runs() == 1

    def test_side_effect_metadata_is_durable(self, tmp_path: Path) -> None:
        store = SQLiteRunStore(tmp_path / "runs.sqlite3")
        run = store.get_or_create(_task(), str(tmp_path / "workspace"))
        store.update(
            run.execution_id,
            executor_reference="codex-output:abc",
            commit_sha="1" * 40,
            head_sha="1" * 40,
            pr_number=115,
            failure_classification="SUCCESS",
        )
        observed = store.get(run.execution_id)
        assert observed is not None
        assert observed.executor_reference == "codex-output:abc"
        assert observed.commit_sha == "1" * 40
        assert observed.pr_number == 115

    def test_cancel_is_terminal_and_idempotent(self, tmp_path: Path) -> None:
        store = SQLiteRunStore(tmp_path / "runs.sqlite3")
        run = store.get_or_create(_task(), str(tmp_path / "workspace"))
        store.cancel(run.execution_id)
        store.cancel(run.execution_id)
        assert store.get(run.execution_id).state == RunState.CANCELLED  # type: ignore[union-attr]


class TestExecutionAdapters:
    def test_real_codex_prompt_includes_issue_spec_but_not_git_publication(self, tmp_path: Path) -> None:
        captured: dict[str, object] = {}

        def runner(argv, **kwargs):
            captured["argv"] = argv
            captured["input"] = kwargs["input"]
            captured["encoding"] = kwargs.get("encoding")
            captured["errors"] = kwargs.get("errors")
            return subprocess.CompletedProcess(argv, 0, "completed", "")

        result = CodexExecutorAdapter(
            runner=runner,
            executable_resolver=lambda: ("C:/Windows/System32/cmd.exe", "/d", "/s", "/c", "C:/npm/codex.cmd"),
        ).execute(_task(), tmp_path, 30)
        assert result.exit_code == 0
        assert "# Canary" in str(captured["input"])
        assert "The machine-readable task block is the only authority" in str(captured["input"])
        assert "approval_state: APPROVED" in str(captured["input"])
        assert "approved_by: dddd2024" in str(captured["input"])
        assert "approval_event_or_time: 2026-08-05T03:08:56Z" in str(captured["input"])
        assert "Do not commit or publish" in str(captured["input"])
        assert "--full-auto" in captured["argv"]
        assert captured["argv"][:5] == [
            "C:/Windows/System32/cmd.exe", "/d", "/s", "/c", "C:/npm/codex.cmd",
        ]
        assert captured["encoding"] == "utf-8"
        assert captured["errors"] == "replace"
    def test_fake_codex_success_failure_timeout_and_malformed(self, tmp_path: Path) -> None:
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        success = FakeCodexExecutorAdapter.success()
        assert success.execute(_task(), worktree, 30).exit_code == 0
        assert FakeCodexExecutorAdapter.nonzero(7).execute(_task(), worktree, 30).exit_code == 7
        assert FakeCodexExecutorAdapter.timeout().execute(_task(), worktree, 30).timed_out is True
        assert FakeCodexExecutorAdapter.malformed().execute(_task(), worktree, 30).malformed is True

    def test_secret_redaction_covers_common_token_forms(self) -> None:
        text = "Authorization: Bearer abc123 ghp_abcdefghijklmnopqrstuvwxyz123456 sk-secretvalue"
        redacted = redact_secrets(text)
        assert "abc123" not in redacted
        assert "ghp_" not in redacted
        assert "sk-secretvalue" not in redacted
        assert redacted.count("[REDACTED]") >= 3

    def test_validation_runner_classifies_success_failure_and_timeout(self, tmp_path: Path) -> None:
        success_runner = LocalValidationRunner(
            process_runner=lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "ok", "")
        )
        assert success_runner.run(("check",), tmp_path, 10)[0].classification == "SUCCESS"

        failure_runner = LocalValidationRunner(
            process_runner=lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1, "", "failed")
        )
        assert failure_runner.run(("check",), tmp_path, 10)[0].classification == "PRODUCT_TEST_FAILURE"

        def timeout(*_args, **_kwargs):
            raise subprocess.TimeoutExpired("check", 10, output="partial")

        timeout_runner = LocalValidationRunner(process_runner=timeout)
        result = timeout_runner.run(("check",), tmp_path, 10)[0]
        assert result.classification == "INFRASTRUCTURE_TIMEOUT"
        assert result.semantic_rejection is False

    @pytest.mark.parametrize(
        ("kind", "expected"),
        [
            ("credential_policy", "TERMINAL_POLICY_VIOLATION"),
            ("base_drift", "TERMINAL_POLICY_VIOLATION"),
            ("github_transient", "TRANSIENT_GITHUB_FAILURE"),
            ("product_test", "PRODUCT_TEST_FAILURE"),
            ("state_gate_known_copy_heuristic", "KNOWN_EXTERNAL_GATE_BLOCKER"),
        ],
    )
    def test_failure_classifier(self, kind: str, expected: str) -> None:
        assert FailureClassifier.classify(kind) == expected


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


class TestGitWorktreeManager:
    def test_create_and_reconcile_same_worktree(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.invalid")
        _git(repo, "config", "user.name", "Test")
        (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        _git(repo, "add", "seed.txt")
        _git(repo, "commit", "-m", "seed")
        base = _git(repo, "rev-parse", "HEAD")
        root = tmp_path / "workspaces"
        manager = GitWorktreeManager(repo, root)
        path = manager.prepare("exec-1", "agent/canary", base)
        assert path == root / "exec-1"
        assert manager.prepare("exec-1", "agent/canary", base) == path
        assert _git(path, "branch", "--show-current") == "agent/canary"

    def test_reconcile_rejects_dirty_pre_execution_worktree(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.invalid")
        _git(repo, "config", "user.name", "Test")
        (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        _git(repo, "add", "seed.txt")
        _git(repo, "commit", "-m", "seed")
        base = _git(repo, "rev-parse", "HEAD")
        manager = GitWorktreeManager(repo, tmp_path / "workspaces")
        path = manager.prepare("exec-1", "agent/canary", base)
        (path / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        with pytest.raises(RuntimeError, match="dirty_worktree"):
            manager.prepare("exec-1", "agent/canary", base, require_clean=True)


class _FakeWorkspace:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.calls = 0

    def prepare(self, *_args, **_kwargs) -> Path:
        self.calls += 1
        self.path.mkdir(parents=True, exist_ok=True)
        return self.path

    def has_changes(self, _path: Path) -> bool:
        return True


class _FakeValidator:
    def run(self, *_args, **_kwargs) -> tuple[CommandResult, ...]:
        return (CommandResult.success("check"),)


class _FakePublisher:
    def __init__(self) -> None:
        self.commit_calls = 0
        self.push_calls = 0
        self.pr_calls = 0

    def commit(self, *_args, **_kwargs) -> str:
        self.commit_calls += 1
        return "1" * 40

    def push(self, *_args, **_kwargs) -> str:
        self.push_calls += 1
        return "1" * 40

    def ensure_draft_pr(self, *_args, **_kwargs) -> int:
        self.pr_calls += 1
        return 115


class _FakeObserver:
    def observe(self, *_args, **_kwargs) -> tuple[dict[str, object], ...]:
        return ({"workflow_name": "CI", "classification": "SUCCESS"},)


class TestFakeEndToEnd:
    def test_reaches_ready_and_resume_skips_duplicate_side_effects(self, tmp_path: Path) -> None:
        store = SQLiteRunStore(tmp_path / "runs.sqlite3")
        workspace = _FakeWorkspace(tmp_path / "workspace")
        executor = FakeCodexExecutorAdapter(
            ExecutorResult(exit_code=0, timed_out=False, elapsed_seconds=0.1, output_sha256="a" * 64)
        )
        publisher = _FakePublisher()
        coordinator = PlatformV1Coordinator(
            store=store,
            workspace_manager=workspace,
            executor=executor,
            validator=_FakeValidator(),
            publisher=publisher,
            workflow_observer=_FakeObserver(),
        )

        first = coordinator.run(_task())
        second = coordinator.run(_task())

        assert first.state == RunState.READY_FOR_HUMAN
        assert second.execution_id == first.execution_id
        assert executor.call_count == 1
        assert publisher.commit_calls == 1
        assert publisher.push_calls == 1
        assert publisher.pr_calls == 1
        assert store.count_runs() == 1

    def test_resume_executor_running_with_existing_changes_does_not_call_model_again(self, tmp_path: Path) -> None:
        task = _task()
        store = SQLiteRunStore(tmp_path / "runs.sqlite3")
        run = store.get_or_create(task, str(tmp_path / "workspace"))
        for state in (RunState.VALIDATED, RunState.WORKSPACE_READY, RunState.EXECUTOR_RUNNING):
            store.transition(run.execution_id, state)
        executor = FakeCodexExecutorAdapter.success()
        publisher = _FakePublisher()
        coordinator = PlatformV1Coordinator(
            store=store,
            workspace_manager=_FakeWorkspace(tmp_path / "workspace"),
            executor=executor,
            validator=_FakeValidator(),
            publisher=publisher,
            workflow_observer=_FakeObserver(),
        )
        result = coordinator.run(task)
        assert result.state == RunState.READY_FOR_HUMAN
        assert executor.call_count == 0

    def test_rework_exhaustion_becomes_terminal(self, tmp_path: Path) -> None:
        task = _task()
        store = SQLiteRunStore(tmp_path / "runs.sqlite3")
        run = store.get_or_create(task, str(tmp_path / "workspace"))
        store.update(run.execution_id, attempt=2)
        store.transition(run.execution_id, RunState.REWORK_REQUIRED)
        coordinator = PlatformV1Coordinator(
            store=store,
            workspace_manager=_FakeWorkspace(tmp_path / "workspace"),
            executor=FakeCodexExecutorAdapter.success(),
            validator=_FakeValidator(),
            publisher=_FakePublisher(),
            workflow_observer=_FakeObserver(),
        )
        result = coordinator.run(task)
        assert result.state == RunState.FAILED_TERMINAL
        assert result.failure_classification == "REWORK_LIMIT_EXHAUSTED"

    def test_executor_failure_persists_bounded_diagnostic(self, tmp_path: Path) -> None:
        task = _task()
        store = SQLiteRunStore(tmp_path / "runs.sqlite3")
        coordinator = PlatformV1Coordinator(
            store=store,
            workspace_manager=_FakeWorkspace(tmp_path / "workspace"),
            executor=FakeCodexExecutorAdapter(
                ExecutorResult(
                    exit_code=7,
                    timed_out=False,
                    elapsed_seconds=0.2,
                    output_sha256="a" * 64,
                    summary="bounded failure",
                    executor_reference="fake:failed",
                )
            ),
            validator=_FakeValidator(),
            publisher=_FakePublisher(),
            workflow_observer=_FakeObserver(),
        )
        record = coordinator.run(task)
        assert record.state == RunState.REWORK_REQUIRED
        detail = store.events(record.execution_id)[-1].detail["executor"]
        assert detail == {
            "elapsed_seconds": 0.2,
            "exit_code": 7,
            "malformed": False,
            "output_sha256": "a" * 64,
            "summary": "bounded failure",
            "timed_out": False,
        }
