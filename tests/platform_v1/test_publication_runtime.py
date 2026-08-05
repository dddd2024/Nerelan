from __future__ import annotations

import io
import json
import subprocess
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from reverse_agent.platform_v1.cli import main
from reverse_agent.platform_v1.execution_adapters import (
    GitHubPublicationAdapter,
    WorkflowObserver,
    build_pr_body,
)
from reverse_agent.platform_v1.github_adapter import FakeGitHubAdapter, WorkflowRun
from reverse_agent.platform_v1.issue_task import IssueTaskLoader
from reverse_agent.platform_v1.run_store import SQLiteRunStore


BASE = "1142dd324fdd4c4bf2a1353d9d5e93bc04b33507"


def _body() -> str:
    return """# Canary

```json
{
  "schema_version": 1,
  "repository": "dddd2024/reverse-agent",
  "base_sha": "1142dd324fdd4c4bf2a1353d9d5e93bc04b33507",
  "goal": "Create one file.",
  "allowed_paths": ["examples/platform_v1_target/e2e_canary_115.txt"],
  "forbidden_operations": ["push_main", "merge", "mark_ready", "auto_merge", "force_push", "release", "deployment", "credential_publication"],
  "required_checks": ["git diff --check"],
  "target_branch": "agent/platform-v1-e2e-canary-115",
  "publication": "draft_pr",
  "risk_tier": "R1",
  "max_rework_attempts": 1
}
```
"""


def _task():
    return IssueTaskLoader.parse(
        issue={
            "number": 115,
            "state": "OPEN",
            "body": _body(),
            "labels": [{"name": "r1-approved"}],
        },
        events=[{
            "id": 91,
            "event": "labeled",
            "label": {"name": "r1-approved"},
            "actor": {"login": "dddd2024"},
            "created_at": "2026-08-05T03:08:56Z",
        }],
        expected_repository="dddd2024/reverse-agent",
        expected_base_sha=BASE,
    )


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "-m", "seed")
    _git(repo, "switch", "-c", "agent/platform-v1-e2e-canary-115")
    return repo


class TestAuthoritySnapshot:
    def test_pr_body_contains_immutable_r1_snapshot(self) -> None:
        body = build_pr_body(_task(), "1" * 40)
        for value in (
            "repository: dddd2024/reverse-agent",
            "issue_number: 115",
            "approval_state: APPROVED",
            "approved_by: dddd2024",
            "approval_event_or_time: 2026-08-05T03:08:56Z",
            f"body_digest_sha256: {_task().issue_body_sha256}",
            f"immutable_observation_ref: {_task().issue_body_sha256}",
            f"work_item_identity: dddd2024/reverse-agent#115@{_task().issue_body_sha256}",
            "target_branch: agent/platform-v1-e2e-canary-115",
            f"exact_base_sha: {BASE}",
            f"exact_head_sha: {'1' * 40}",
            "draft: true",
            "publication_boundary: draft-pr-only",
        ):
            assert value in body


class TestGitPublication:
    def test_commit_stages_only_approved_path_and_is_idempotent(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        target = repo / "examples/platform_v1_target/e2e_canary_115.txt"
        target.parent.mkdir(parents=True)
        target.write_text("canary\n", encoding="utf-8")
        adapter = GitHubPublicationAdapter("dddd2024/reverse-agent", task_refresher=lambda task: task)
        first = adapter.commit(repo, _task())
        second = adapter.commit(repo, _task())
        assert first == second
        assert _git(repo, "show", "--pretty=", "--name-only", "HEAD") == "examples/platform_v1_target/e2e_canary_115.txt"

    def test_commit_rejects_unapproved_path(self, tmp_path: Path) -> None:
        repo = _repo(tmp_path)
        (repo / "outside.txt").write_text("no\n", encoding="utf-8")
        adapter = GitHubPublicationAdapter("dddd2024/reverse-agent", task_refresher=lambda task: task)
        with pytest.raises(RuntimeError, match="changed_path_outside_scope"):
            adapter.commit(repo, _task())

    def test_existing_draft_pr_is_reused_without_creation(self) -> None:
        calls: list[list[str]] = []

        def runner(argv, **kwargs):
            calls.append(list(argv))
            if argv[:3] == ["gh", "pr", "list"]:
                return subprocess.CompletedProcess(argv, 0, json.dumps([{
                    "number": 115, "state": "OPEN", "isDraft": True,
                    "headRefName": "agent/platform-v1-e2e-canary-115", "baseRefName": "main",
                }]), "")
            if argv[:3] == ["gh", "pr", "edit"]:
                return subprocess.CompletedProcess(argv, 0, "", "")
            raise AssertionError(argv)

        adapter = GitHubPublicationAdapter(
            "dddd2024/reverse-agent", runner=runner, task_refresher=lambda task: task
        )
        assert adapter.ensure_draft_pr(_task(), "1" * 40) == 115
        assert not any(argv[:3] == ["gh", "api", "--method"] for argv in calls)
        assert sum(argv[:3] == ["gh", "pr", "edit"] for argv in calls) == 1


class TestWorkflowObserver:
    def test_classifies_exact_head_success_and_pending(self) -> None:
        head = "1" * 40
        adapter = FakeGitHubAdapter([
            WorkflowRun(workflow_name="CI", event="pull_request", run_id="1", head_sha=head, status="completed", conclusion="success"),
            WorkflowRun(workflow_name="Decision Preflight", event="pull_request", run_id="2", head_sha=head, status="in_progress", conclusion=""),
        ])
        observations = WorkflowObserver(adapter=adapter, max_wait_seconds=0).observe("dddd2024/reverse-agent", head)
        by_name = {item["workflow_name"]: item for item in observations}
        assert by_name["CI"]["classification"] == "SUCCESS"
        assert by_name["Decision Preflight"]["classification"] == "PENDING"

    def test_known_state_gate_blocker_requires_matching_failed_log(self) -> None:
        head = "1" * 40
        adapter = FakeGitHubAdapter([
            WorkflowRun(workflow_name="State Gate", event="pull_request", run_id="9", head_sha=head, status="completed", conclusion="failure"),
        ])
        observer = WorkflowObserver(
            adapter=adapter,
            max_wait_seconds=0,
            failed_log_loader=lambda *_args: "canonical changed-path inventory differs because rename/copy similarity was applied",
        )
        observations = observer.observe("dddd2024/reverse-agent", head)
        assert observations[0]["classification"] == "KNOWN_EXTERNAL_GATE_BLOCKER"

    def test_unmatched_state_gate_failure_stays_policy_failure(self) -> None:
        head = "1" * 40
        adapter = FakeGitHubAdapter([
            WorkflowRun(workflow_name="State Gate", event="pull_request", run_id="9", head_sha=head, status="completed", conclusion="failure"),
        ])
        observer = WorkflowObserver(
            adapter=adapter,
            max_wait_seconds=0,
            failed_log_loader=lambda *_args: "different policy failure",
        )
        assert observer.observe("dddd2024/reverse-agent", head)[0]["classification"] == "POLICY_GATE_FAILURE"


def _run_cli(args: list[str]) -> tuple[int, dict]:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(args)
    return code, json.loads(output.getvalue())


class TestRuntimeCLI:
    def test_status_and_cancel_are_local_machine_readable(self, tmp_path: Path) -> None:
        runtime = tmp_path / ".platform_v1_runtime"
        store = SQLiteRunStore(runtime / "runs.sqlite3")
        run = store.get_or_create(_task(), str(tmp_path / "workspace"))
        store.close()
        common = [
            "--repo-dir", str(tmp_path),
            "--repository", "dddd2024/reverse-agent",
            "--issue-number", "115",
            "--workspace-root", str(tmp_path / "workspaces"),
        ]
        code, status = _run_cli(["status", *common])
        assert code == 0
        assert status["execution_id"] == run.execution_id
        assert status["state"] == "DISCOVERED"
        code, cancelled = _run_cli(["cancel", *common])
        assert code == 0
        assert cancelled["state"] == "CANCELLED"
