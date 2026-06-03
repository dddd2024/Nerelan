import hashlib
from pathlib import Path

import reverse_agent.local_reverse_string_solver as solver


def _sample(path: Path, root: Path, *, sample_id: str | None = None) -> dict:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return {
        "sample_id": sample_id or digest[:16],
        "relative_path": path.relative_to(root).as_posix(),
        "extension": ".exe",
        "sha256": digest,
        "artifact_role": "challenge_binary",
        "triage_tags": ["strcmp"],
    }


def _policy(root: Path, *, runtime_allowed: bool = True) -> dict:
    return {
        "schema_version": 1,
        "root": str(root),
        "runtime_allowed": runtime_allowed,
        "default_timeout_seconds": 1,
        "max_timeout_seconds": 2,
    }


def _benchmark(samples: list[dict], recommended_ids: list[str] | None = None) -> dict:
    recommended_ids = recommended_ids or [sample["sample_id"] for sample in samples]
    return {
        "schema_version": 1,
        "samples": [
            {
                "sample_id": sample["sample_id"],
                "relative_path": sample["relative_path"],
                "sha256": sample["sha256"],
                "solve_readiness": "ready_static_string_compare",
                "runtime_results": [
                    {
                        "stdout_preview": "please input your flag\nwrong, try again\n",
                        "stderr_preview": "",
                    }
                ],
            }
            for sample in samples
        ],
        "recommended_next_challenges": [
            {
                "sample_id": sample["sample_id"],
                "relative_path": sample["relative_path"],
                "solve_readiness": "ready_static_string_compare",
            }
            for sample in samples
            if sample["sample_id"] in recommended_ids
        ],
    }


def test_only_recommended_ready_static_targets_are_selected(tmp_path: Path, monkeypatch) -> None:
    one = tmp_path / "one.exe"
    two = tmp_path / "two.exe"
    ignored = tmp_path / "ignored.exe"
    one.write_bytes(b"MZ\x00secret_one\x00")
    two.write_bytes(b"MZ\x00secret_two\x00")
    ignored.write_bytes(b"MZ\x00ignored_secret\x00")
    samples = [_sample(one, tmp_path, sample_id="one"), _sample(two, tmp_path, sample_id="two")]
    ignored_sample = _sample(ignored, tmp_path, sample_id="ignored")
    index = {"schema_version": 1, "root": str(tmp_path), "samples": samples + [ignored_sample]}

    monkeypatch.setattr(solver, "run_probe", lambda **_: _probe("wrong"))
    result = solver.run_string_solver(
        corpus_index=index,
        benchmark=_benchmark(samples + [ignored_sample], recommended_ids=["one", "two"]),
        policy=_policy(tmp_path),
    )

    assert result["target_count"] == 2
    assert {target["sample_id"] for target in result["targets"]} == {"one", "two"}


def test_path_escape_and_sha_mismatch_block_without_probe(tmp_path: Path, monkeypatch) -> None:
    outside = tmp_path.parent / "outside_string_solver_escape.exe"
    outside.write_bytes(b"MZ\x00secret\x00")
    calls = []
    try:
        escaped = {
            "sample_id": "escape",
            "relative_path": "../outside_string_solver_escape.exe",
            "extension": ".exe",
            "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
            "artifact_role": "challenge_binary",
            "triage_tags": ["strcmp"],
        }
        mismatch = tmp_path / "mismatch.exe"
        mismatch.write_bytes(b"MZ\x00secret\x00")
        mismatch_sample = _sample(mismatch, tmp_path, sample_id="mismatch")
        mismatch_sample["sha256"] = "0" * 64
        index = {"schema_version": 1, "root": str(tmp_path), "samples": [escaped, mismatch_sample]}
        benchmark = _benchmark([escaped, mismatch_sample])

        monkeypatch.setattr(solver, "run_probe", lambda **kwargs: calls.append(kwargs) or _probe("correct"))
        result = solver.run_string_solver(corpus_index=index, benchmark=benchmark, policy=_policy(tmp_path))

        assert result["status"] == "BLOCKED"
        assert calls == []
        reasons = {reason for target in result["targets"] for reason in target["blocked_reasons"]}
        assert {"PATH_OUTSIDE_ROOT", "SHA256_MISMATCH"} <= reasons
    finally:
        outside.unlink(missing_ok=True)


def test_candidate_filtering_and_limit() -> None:
    data = (
        b"please input your flag\x00wrong\x00"
        b"flag{real_candidate}\x00"
        b"KERNEL32.dll\x00"
        b"AlphaBeta\x00"
        b"success\x00"
        b"another_token\x00"
    )

    candidates = solver.build_candidates(
        data=data,
        relative_path="course/CPP2.exe",
        benchmark_sample={"runtime_results": [{"stdout_preview": "sorry\nplease input\n", "stderr_preview": ""}]},
        max_candidates=3,
    )

    values = [candidate["candidate"] for candidate in candidates]
    assert "flag{real_candidate}" in values
    assert "AlphaBeta" in values
    assert len(candidates) == 3
    assert "wrong" not in values
    assert all("please" not in value.lower() for value in values)


def test_success_marker_without_failure_is_required() -> None:
    assert solver.validation_succeeded(_probe("correct")) is True
    assert solver.validation_succeeded(_probe("correct but wrong")) is False
    assert solver.validation_succeeded(_probe("wrong, try again")) is False
    timeout_probe = _probe("correct")
    timeout_probe["timeout"] = True
    assert solver.validation_succeeded(timeout_probe) is False


def test_negative_result_schema_when_no_candidate_validates(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"MZ\x00AlphaBeta\x00")
    sample = _sample(exe, tmp_path, sample_id="demo")

    monkeypatch.setattr(solver, "run_probe", lambda **_: _probe("wrong, try again"))
    result = solver.run_string_solver(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        benchmark=_benchmark([sample]),
        policy=_policy(tmp_path),
    )

    target = result["targets"][0]
    assert result["schema_version"] == 1
    assert result["solver_family"] == "string_compare_static_solver_v1"
    assert result["status"] == "PARTIAL"
    assert target["solved"] is False
    assert target["negative_result"] == "NO_CANDIDATE_VALIDATED"
    assert target["missing_evidence"] == "needs_compare_constant_or_disassembly"
    assert target["candidate_count"] <= 50
    assert target["validated_candidate_count"] == target["candidate_count"]


def test_successful_probe_records_solution_evidence(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"MZ\x00AlphaBeta\x00")
    sample = _sample(exe, tmp_path, sample_id="demo")

    monkeypatch.setattr(solver, "run_probe", lambda **_: _probe("success"))
    result = solver.run_string_solver(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        benchmark=_benchmark([sample]),
        policy=_policy(tmp_path),
    )

    target = result["targets"][0]
    assert result["status"] == "SUCCESS"
    assert target["solved"] is True
    assert target["solution"] == "AlphaBeta"
    assert target["stdout_success_preview"] == "success"


def _probe(stdout: str) -> dict:
    return {
        "probe_name": "candidate_1",
        "exit_code": 0,
        "timeout": False,
        "stdout_preview": stdout,
        "stderr_preview": "",
        "duration_ms": 1,
        "classification": "prints_success_failure",
    }
