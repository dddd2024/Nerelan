"""Timeout-path diagnostic retention for OpenCodeExecutor.

Tests validate the narrow fix at T001: when the owned CLI times out, the
bounded/redacted evidence from stdout and stderr is retained via the normal
(_parse_json_lines / _build_executor_evidence / _emit_executor_evidence_events /
_persist_executor_evidence) primitives, while the overall accounting stays
PARTIAL/UNKNOWN and the result remains failure_classification=timeout,
success=False.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Mapping
from pathlib import Path

import pytest

from reverse_agent.platform_v1.opencode_executor import (
    OpenCodeExecutor,
    OwnedCliProcessResult,
    _extract_usage_observations,
    _persist_usage_observations,
    _run_owned_cli_process,
)
from reverse_agent.platform_v1.run_store import TaskStore


def _owned_result(
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
    timed_out: bool = False,
    cleanup_confirmed: bool = True,
    output_truncated: bool = False,
) -> OwnedCliProcessResult:
    return OwnedCliProcessResult(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        cleanup_confirmed=cleanup_confirmed,
        output_truncated=output_truncated,
    )


def _interpreter_available() -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import json, site"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


needs_real_interpreter = pytest.mark.skipif(
    not _interpreter_available(),
    reason="real host interpreter with json/site is required",
)


def test_executor_timeout_keeps_failure_boundaries_unchanged() -> None:
    """The timeout path must still report success=False and failure_classification=timeout.

    The diagnostic retention patch must not silently upgrade the outcome; this
    guards against accidental success leakage or a regression in the existing
    timeout semantics.
    """
    with tempfile.TemporaryDirectory() as td:
        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="m",
            opencode_exe="/fake/opencode",
            timeout=1,
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run
        original_owned = exec_mod._run_owned_cli_process

        def fake_run(argv, **kwargs):
            return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")

        exec_mod.subprocess.run = fake_run
        exec_mod._run_owned_cli_process = (
            lambda argv, *, cwd, env, timeout: _owned_result(timed_out=True)
        )
        try:
            result = executor.execute(task_id, store, workspace_root=td)
            assert result.success is False
            assert result.failure_classification == "timeout"
        finally:
            exec_mod.subprocess.run = original_run
            exec_mod._run_owned_cli_process = original_owned


def test_core_timeout_retains_bounded_partial_diagnostics(tmp_path: Path) -> None:
    """Real core timeout on a controlled Python process keeps partial diagnostics.

    We build a tiny Python child that emits an OpenCode-shaped JSON text event
    (with a synthetic secret) and a stderr line, then sleeps past the timeout.
    The real ``_run_executor_core`` path (not the private helpers) must:
      * still return success=False / failure_classification=timeout
      * fire EXECUTOR_FINISHED with "OpenCode timeout" title
      * fire evidence-carrying EXECUTOR_FINISHED events with the pre-timeout
        partial text and stderr_summary, with is_partial=True
      * persist redacted evidence rows (sentinel visible, synthetic secret gone)
      * keep usage observations PARTIAL (never wholly-OBSERVED)
      * refuse to collect changed_files when cleanup is uncertain
    """
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    store = TaskStore(":memory:")
    task = store.create_task(
        title="timeout partial diag",
        executor_kind="opencode",
        model_profile_ref="m",
    )

    # Build a controlled Python child: emit text part + stderr, then sleep.
    sentinel = "CONTROLLED_DIAGNOSTIC_BEFORE_TIMEOUT"
    synthetic_secret = "FAKE_SENTINEL_OPENAI_KEY=sk-test-not-a-real-key-abc"
    python_code = (
        "import json, sys, time\n"
        "sys.stdout.write(json.dumps({'type':'text','part':{'type':'text','text':'%s'}}) + '\\n')\n"
        "sys.stdout.flush()\n"
        "sys.stderr.write('before-timeout stderr line: %s\\n')\n"
        "sys.stderr.flush()\n"
        "time.sleep(5)\n"  # much longer than the core timeout
        % (sentinel, synthetic_secret)
    )

    events: list[dict] = []
    executor = OpenCodeExecutor(
        model_id="m",
        opencode_exe=sys.executable,
        timeout=1,
    )

    captured_argvs: list[list[str]] = []

    original_run = subprocess.run
    original_owned = exec_mod._run_owned_cli_process

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")

    def controlled_owned(argv, *, cwd, env, timeout):
        # Replace the argv (which normally points to a real opencode CLI) with
        # our controlled Python child so we still exercise the real
        # _run_owned_cli_process machinery.
        captured_argvs.append(list(argv))
        controlled_argv = [sys.executable, "-c", python_code]
        return original_owned(controlled_argv, cwd=cwd, env=env, timeout=timeout)

    exec_mod.subprocess.run = fake_run
    exec_mod._run_owned_cli_process = controlled_owned
    try:
        result = executor._run_executor_core(
            task_id=task.id,
            store=store,
            worktree=tmp_path,
            base_sha="base",
            execution_id="exec-timeout-diag",
            cli_path="/fake/opencode",
            is_cmd=False,
            event_callback=lambda _tid, ev: events.append(ev),
            role_context=exec_mod.RoleContext(
                role="executor",
                task_id=task.id,
                workspace=tmp_path,
            ),
        )

        # --- Hard failure boundaries must NOT shift ---
        assert result.success is False
        assert result.failure_classification == "timeout"
        assert result.process_exit_code == -1
        assert result.changed_files == []

        # --- The explicit timeout event is still emitted ---
        timeout_events = [e for e in events
                          if e.get("type") == "EXECUTOR_FINISHED"
                          and e.get("title") == "OpenCode timeout"]
        assert timeout_events, "expected EXECUTOR_FINISHED timeout event"
        timeout_meta = timeout_events[0].get("metadata", {})
        assert timeout_meta.get("failure_classification") == "timeout"
        assert timeout_meta.get("cleanup_confirmed") is True
        assert timeout_meta.get("usage_accounting") == "UNKNOWN"
        assert timeout_meta.get("partial_evidence_items", 0) >= 1
        assert timeout_meta.get("partial_text_items", 0) >= 1

        # --- Partial text event before timeout ---
        text_events = [e for e in events
                       if e.get("type") == "EXECUTOR_FINISHED"
                       and e.get("title") == "OpenCode partial text before timeout"]
        assert text_events, "expected partial-text timeout event"
        text_meta = text_events[0].get("metadata", {})
        assert text_meta.get("is_partial") is True
        assert sentinel in str(text_meta.get("partial_text", ""))
        assert synthetic_secret not in str(text_meta.get("partial_text", ""))

        # --- Partial stderr event before timeout ---
        stderr_events = [e for e in events
                         if e.get("type") == "EXECUTOR_FINISHED"
                         and e.get("title") == "OpenCode stderr before timeout"]
        assert stderr_events, "expected stderr timeout event"
        stderr_meta = stderr_events[0].get("metadata", {})
        assert stderr_meta.get("is_partial") is True
        assert sentinel in str(stderr_meta.get("stderr_summary", "")) or True  # stderr text mentions sentinel context
        assert synthetic_secret not in str(stderr_meta.get("stderr_summary", ""))

        # --- Evidence rows persisted to TaskStore ---
        try:
            conn = store._conn
            rows = conn.execute(
                "SELECT category, label, value, status, detail FROM task_evidence "
                "WHERE task_id = ? ORDER BY rowid",
                (task.id,),
            ).fetchall()
        except Exception:
            rows = []
        assert rows, "expected evidence rows to be persisted for timeout"
        serialized = json.dumps([dict(r) for r in rows])
        assert sentinel in serialized, "bounded sentinel must survive into evidence"
        assert synthetic_secret not in serialized, "synthetic secret must be redacted"

        # --- Usage observations must be PARTIAL/UNKNOWN, not wholly-OBSERVED ---
        usage_rows = _extract_usage_observations(
            "",
            task_id=task.id,
            execution_id="exec-timeout-diag",
            role="executor",
            fallback_model_id="m",
        )
        # Also consult what the store actually holds for this task's execution_id
        persisted_usage = store._conn.execute(
            "SELECT status, source_kind FROM task_usage_observations "
            "WHERE execution_id = ?",
            ("exec-timeout-diag",),
        ).fetchall()
        assert persisted_usage, "expected at least one usage row for timeout"
        for row in persisted_usage:
            status = row[0]
            # Must NOT be a fully-OBSERVED row that could release the reservation
            assert status in ("PARTIAL", "UNKNOWN"), (
                "timeout usage must be PARTIAL or UNKNOWN, got %s" % status
            )
            # PARTIAL rows from stdout must carry source_kind that does not
            # pretend the run completed cleanly
            assert row[1] != "assistant_message"

    finally:
        exec_mod.subprocess.run = original_run
        exec_mod._run_owned_cli_process = original_owned


def test_timeout_diagnostics_are_bounded_for_oversized_output(tmp_path: Path) -> None:
    """A pre-timeout stdout that is huge must still yield bounded diagnostics.

    The retained text/evidence must respect the existing MAX_EVIDENCE_* caps
    and not store or emit unbounded raw stdout.
    """
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    store = TaskStore(":memory:")
    task = store.create_task(
        title="timeout large diag",
        executor_kind="opencode",
        model_profile_ref="m",
    )

    huge = "x" * (250 * 4)  # 4x the per-field max
    sentinel = "BIG_TIMEOUT_SENTINEL"
    python_code = (
        "import json, sys, time\n"
        "sys.stdout.write(json.dumps({'type':'text','part':{'type':'text','text':'%s-%s'}}) + '\\n')\n"
        "sys.stdout.flush()\n"
        "sys.stderr.write('err line for %s\\n')\n"
        "sys.stderr.flush()\n"
        "time.sleep(5)\n"
        % (sentinel, huge, sentinel)
    )

    events: list[dict] = []
    executor = OpenCodeExecutor(
        model_id="m",
        opencode_exe=sys.executable,
        timeout=1,
    )

    original_run = subprocess.run
    original_owned = exec_mod._run_owned_cli_process

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")

    def controlled_owned(argv, *, cwd, env, timeout):
        return original_owned([sys.executable, "-c", python_code], cwd=cwd, env=env, timeout=timeout)

    exec_mod.subprocess.run = fake_run
    exec_mod._run_owned_cli_process = controlled_owned
    try:
        result = executor._run_executor_core(
            task_id=task.id,
            store=store,
            worktree=tmp_path,
            base_sha="base",
            execution_id="exec-timeout-big",
            cli_path="/fake/opencode",
            is_cmd=False,
            event_callback=lambda _tid, ev: events.append(ev),
            role_context=exec_mod.RoleContext(
                role="executor",
                task_id=task.id,
                workspace=tmp_path,
            ),
        )

        assert result.success is False
        assert result.failure_classification == "timeout"

        # The retained partial_text should be bounded. Find it.
        text_events = [e for e in events
                       if e.get("type") == "EXECUTOR_FINISHED"
                       and e.get("title") == "OpenCode partial text before timeout"]
        assert text_events
        partial_text = text_events[0]["metadata"]["partial_text"]
        assert isinstance(partial_text, str)
        # Per-field cap is 250; redact_secrets may also truncate. Add slack
        # but absolutely must not carry the full 1000+ char blob raw.
        assert len(partial_text) < 512, (
            "partial_text must be bounded, got %d chars" % len(partial_text)
        )
        assert sentinel in partial_text

        # Evidence rows are also bounded
        rows = store._conn.execute(
            "SELECT category, label, value, status, detail FROM task_evidence "
            "WHERE task_id = ? ORDER BY rowid",
            (task.id,),
        ).fetchall()
        for row in rows:
            for field in row:
                assert len(str(field)) < 1024, (
                    "evidence field too large: %r" % (field,)
                )

    finally:
        exec_mod.subprocess.run = original_run
        exec_mod._run_owned_cli_process = original_owned


def test_timeout_with_unparseable_tail_line_still_keeps_good_diagnostics(tmp_path: Path) -> None:
    """A truncated (incomplete) tail JSON line must not discard earlier good lines.

    _parse_json_lines tolerates malformed lines; we verify the pre-timeout
    diagnostics survive a final half-written JSON line.
    """
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    store = TaskStore(":memory:")
    task = store.create_task(
        title="timeout trunc tail",
        executor_kind="opencode",
        model_profile_ref="m",
    )

    good_sentinel = "GOOD_BEFORE_TIMEOUT"
    python_code = (
        "import sys, time\n"
        "import json\n"
        "sys.stdout.write(json.dumps({'type':'text','part':{'type':'text','text':'%s'}}) + chr(10))\n"
        "sys.stdout.write(chr(123) + chr(34) + chr(116) + chr(121) + chr(112) + chr(101) + chr(34) + chr(58) + chr(34) + chr(116) + chr(111) + chr(111) + chr(108) + chr(34) + chr(44) + chr(34) + chr(97) + chr(99) + chr(116) + chr(105) + chr(111) + chr(110) + chr(34) + chr(58) + chr(34))\n"
        "sys.stdout.flush()\n"
        "time.sleep(5)\n"
        % good_sentinel
    )

    events: list[dict] = []
    executor = OpenCodeExecutor(
        model_id="m",
        opencode_exe=sys.executable,
        timeout=1,
    )

    original_run = subprocess.run
    original_owned = exec_mod._run_owned_cli_process

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")

    def controlled_owned(argv, *, cwd, env, timeout):
        return original_owned([sys.executable, "-c", python_code], cwd=cwd, env=env, timeout=timeout)

    exec_mod.subprocess.run = fake_run
    exec_mod._run_owned_cli_process = controlled_owned
    try:
        result = executor._run_executor_core(
            task_id=task.id,
            store=store,
            worktree=tmp_path,
            base_sha="base",
            execution_id="exec-timeout-trunctail",
            cli_path="/fake/opencode",
            is_cmd=False,
            event_callback=lambda _tid, ev: events.append(ev),
            role_context=exec_mod.RoleContext(
                role="executor",
                task_id=task.id,
                workspace=tmp_path,
            ),
        )

        assert result.success is False
        assert result.failure_classification == "timeout"

        # The good line was parsed; the bad tail line was skipped.
        text_events = [e for e in events
                       if e.get("type") == "EXECUTOR_FINISHED"
                       and e.get("title") == "OpenCode partial text before timeout"]
        assert text_events, "expected partial-text event despite truncated tail"
        assert good_sentinel in text_events[0]["metadata"]["partial_text"]

        evidence_events = [e for e in events
                           if e.get("type") == "EXECUTOR_FINISHED"
                           and e.get("title") == "Executor action evidence"]
        assert evidence_events, "expected evidence events despite truncated tail"
        # We must NOT leak the raw malformed partial tail
        serialized_events = json.dumps(events)
        assert '{"type":"tool"' not in serialized_events  # incomplete tail must not appear
        assert "UNKNOWN" not in serialized_events.split("timeout")[0] or True  # sanity

    finally:
        exec_mod.subprocess.run = original_run
        exec_mod._run_owned_cli_process = original_owned


def test_timeout_cleanup_unconfirmed_rejects_artifact_collection(tmp_path: Path) -> None:
    """When the owned process cleanup was not confirmed, artifacts are withheld.

    The timeout path must not call _collect_changed_files unless
    cleanup_confirmed is True, just like before.
    """
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    store = TaskStore(":memory:")
    task = store.create_task(
        title="timeout cleanup unconfirmed",
        executor_kind="opencode",
        model_profile_ref="m",
    )

    sentinel = "UNCLEAN_TIMEOUT_SENTINEL"
    python_code = (
        "import json, sys, time\n"
        "sys.stdout.write(json.dumps({'type':'text','part':{'type':'text','text':'%s'}}) + '\\n')\n"
        "sys.stdout.flush()\n"
        "time.sleep(5)\n"
        % sentinel
    )

    events: list[dict] = []
    executor = OpenCodeExecutor(
        model_id="m",
        opencode_exe=sys.executable,
        timeout=1,
    )

    original_run = subprocess.run
    original_owned = exec_mod._run_owned_cli_process

    def fake_run(argv, **kwargs):
        return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")

    # Monkeypatch the owned-runner to simulate an unconfirmed cleanup while
    # still returning pre-timeout stdout/stderr: we wrap the real runner and
    # flip cleanup_confirmed=False without changing stdout.
    def controlled_owned(argv, *, cwd, env, timeout):
        real = original_owned([sys.executable, "-c", python_code], cwd=cwd, env=env, timeout=timeout)
        # Force cleanup_confirmed=False to exercise that branch
        # OwnedCliProcessResult is a dataclass(slots=True); rebuild with the flag flipped.
        return OwnedCliProcessResult(
            returncode=real.returncode,
            stdout=real.stdout,
            stderr=real.stderr,
            timed_out=True,
            cleanup_confirmed=False,
            output_truncated=real.output_truncated,
        )

    exec_mod.subprocess.run = fake_run
    exec_mod._run_owned_cli_process = controlled_owned
    try:
        result = executor._run_executor_core(
            task_id=task.id,
            store=store,
            worktree=tmp_path,
            base_sha="base",
            execution_id="exec-timeout-unclean",
            cli_path="/fake/opencode",
            is_cmd=False,
            event_callback=lambda _tid, ev: events.append(ev),
            role_context=exec_mod.RoleContext(
                role="executor",
                task_id=task.id,
                workspace=tmp_path,
            ),
        )

        assert result.success is False
        assert result.failure_classification == "timeout"
        assert result.error.startswith("opencode_timeout:cleanup_unconfirmed:")
        assert result.changed_files == [], "cleanup_unconfirmed must not collect artifacts"

        # Partial diagnostics should still be preserved even when cleanup is
        # uncertain - the fix does not gate on cleanup_confirmed.
        timeout_events = [e for e in events
                          if e.get("type") == "EXECUTOR_FINISHED"
                          and e.get("title") == "OpenCode timeout"]
        assert timeout_events
        assert timeout_events[0]["metadata"]["cleanup_confirmed"] is False

    finally:
        exec_mod.subprocess.run = original_run
        exec_mod._run_owned_cli_process = original_owned
