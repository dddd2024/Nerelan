import hashlib
import json
import os
import sys
from pathlib import Path

from reverse_agent.local_reverse_runtime import (
    run_benchmark,
    run_probe,
)


def _write_exe_script(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    if os.name != "nt":
        path.chmod(0o755)


def _sample(path: Path, root: Path, *, role: str = "challenge_binary", extension: str = ".exe") -> dict:
    data = path.read_bytes()
    return {
        "sample_id": hashlib.sha256(data).hexdigest()[:16],
        "relative_path": path.relative_to(root).as_posix(),
        "extension": extension,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "file_kind": "pe32",
        "artifact_role": role,
        "triage_tags": ["strcmp"],
    }


def _policy(root: Path) -> dict:
    return {
        "schema_version": 1,
        "root": str(root),
        "runtime_allowed": True,
        "allowed_extensions": [".exe"],
        "default_timeout_seconds": 1,
        "max_timeout_seconds": 2,
        "stdin_probe_limit": 1,
    }


def test_only_indexed_exe_under_root_executes(tmp_path: Path) -> None:
    exe = tmp_path / "demo.py"
    _write_exe_script(exe, f"#!{sys.executable}\nprint('correct password')\n")
    index = {"schema_version": 1, "root": str(tmp_path), "samples": [_sample(exe, tmp_path)]}

    result = run_benchmark(corpus_index=index, policy=_policy(tmp_path))

    assert result["status"] == "READY"
    assert result["challenge_count"] == 1
    assert result["executed_count"] == 1
    assert result["samples"][0]["solve_readiness"] == "ready_static_string_compare"


def test_solver_script_and_non_exe_are_excluded(tmp_path: Path) -> None:
    exe = tmp_path / "solver.py"
    txt = tmp_path / "note.txt"
    _write_exe_script(exe, f"#!{sys.executable}\nprint('solver')\n")
    txt.write_text("notes", encoding="utf-8")
    index = {
        "schema_version": 1,
        "root": str(tmp_path),
        "samples": [
            _sample(exe, tmp_path, role="solver_script"),
            _sample(txt, tmp_path, role="notes_or_source", extension=".txt"),
        ],
    }

    result = run_benchmark(corpus_index=index, policy=_policy(tmp_path))

    assert result["status"] == "BLOCKED"
    assert result["challenge_count"] == 0
    assert "NO_CHALLENGE_BINARIES" in result["blocked_reasons"]


def test_sha256_mismatch_skips_execution(tmp_path: Path) -> None:
    exe = tmp_path / "demo.exe"
    _write_exe_script(exe, f"#!{sys.executable}\nprint('should not run')\n")
    sample = _sample(exe, tmp_path)
    sample["sha256"] = "0" * 64
    index = {"schema_version": 1, "root": str(tmp_path), "samples": [sample]}

    result = run_benchmark(corpus_index=index, policy=_policy(tmp_path))

    assert result["status"] == "BLOCKED"
    assert result["executed_count"] == 0
    assert result["samples"][0]["runtime_status"] == "blocked"
    assert "SHA256_MISMATCH" in result["samples"][0]["blocked_reasons"]


def test_path_escape_is_blocked(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside_runtime_escape.exe"
    _write_exe_script(outside, f"#!{sys.executable}\nprint('outside')\n")
    try:
        data = outside.read_bytes()
        sample = {
            "sample_id": hashlib.sha256(data).hexdigest()[:16],
            "relative_path": "../outside_runtime_escape.exe",
            "extension": ".exe",
            "sha256": hashlib.sha256(data).hexdigest(),
            "artifact_role": "challenge_binary",
            "triage_tags": ["strcmp"],
        }
        index = {"schema_version": 1, "root": str(tmp_path), "samples": [sample]}

        result = run_benchmark(corpus_index=index, policy=_policy(tmp_path))

        assert result["status"] == "BLOCKED"
        assert "PATH_OUTSIDE_ROOT" in result["samples"][0]["blocked_reasons"]
    finally:
        outside.unlink(missing_ok=True)


def test_timeout_is_recorded(tmp_path: Path) -> None:
    sleeper = tmp_path / "sleepy.py"
    sleeper.write_text("import time\ntime.sleep(2)\n", encoding="utf-8")

    result = run_probe(
        path=sleeper,
        probe_name="timeout",
        stdin_text=None,
        timeout=1,
        preview_limit=100,
    )

    assert result["timeout"] is True
    assert result["classification"] == "timeout"


def test_stdout_stderr_preview_truncates(tmp_path: Path) -> None:
    noisy = tmp_path / "noisy.py"
    noisy.write_text("print('x' * 100)\n", encoding="utf-8")

    result = run_probe(
        path=noisy,
        probe_name="noisy",
        stdin_text=None,
        timeout=2,
        preview_limit=10,
    )

    assert len(result["stdout_preview"]) == 10


def test_missing_root_blocks_without_crashing(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    index = {"schema_version": 1, "root": str(missing), "samples": []}

    result = run_benchmark(corpus_index=index, policy=_policy(missing))

    assert result["status"] == "BLOCKED"
    assert "ROOT_UNAVAILABLE" in result["blocked_reasons"]


def test_runtime_allowed_false_is_preserved_in_sample_result(tmp_path: Path) -> None:
    exe = tmp_path / "demo.py"
    _write_exe_script(exe, f"#!{sys.executable}\nprint('should not run')\n")
    policy = _policy(tmp_path)
    policy["runtime_allowed"] = False
    index = {"schema_version": 1, "root": str(tmp_path), "samples": [_sample(exe, tmp_path)]}

    result = run_benchmark(corpus_index=index, policy=policy)

    assert result["status"] == "BLOCKED"
    assert result["samples"][0]["runtime_allowed"] is False
    assert result["samples"][0]["runtime_status"] == "blocked"
    assert "RUNTIME_NOT_ALLOWED_BY_POLICY" in result["samples"][0]["blocked_reasons"]
