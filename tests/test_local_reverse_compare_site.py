import hashlib
from pathlib import Path

import reverse_agent.local_reverse_compare_site as compare_site


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


def _benchmark(samples: list[dict], *, readiness: str = "ready_static_string_compare") -> dict:
    return {
        "schema_version": 1,
        "samples": [
            {
                "sample_id": sample["sample_id"],
                "relative_path": sample["relative_path"],
                "sha256": sample["sha256"],
                "solve_readiness": readiness,
                "runtime_results": [],
            }
            for sample in samples
        ],
    }


def _string_result(samples: list[dict], *, solved_ids: set[str] | None = None, include_extra: bool = False) -> dict:
    solved_ids = solved_ids or set()
    targets = []
    for sample in samples:
        solved = sample["sample_id"] in solved_ids
        targets.append({
            "sample_id": sample["sample_id"],
            "relative_path": sample["relative_path"],
            "sha256": sample["sha256"],
            "solved": solved,
            "negative_result": None if solved else "NO_CANDIDATE_VALIDATED",
            "missing_evidence": None if solved else "needs_compare_constant_or_disassembly",
            "validation_results_preview": [{"candidate": "OldCandidate"}],
        })
    if include_extra:
        targets.append({
            "sample_id": "not_in_scope",
            "relative_path": "ignored.exe",
            "sha256": "0" * 64,
            "solved": False,
            "negative_result": "NO_CANDIDATE_VALIDATED",
            "missing_evidence": "needs_compare_constant_or_disassembly",
        })
    return {"schema_version": 1, "targets": targets}


def test_only_three_unsolved_decision_targets_are_selected(tmp_path: Path, monkeypatch) -> None:
    samples = []
    for sample_id in sorted(compare_site.TARGET_SAMPLE_IDS):
        path = tmp_path / f"{sample_id}.exe"
        path.write_bytes(b"MZ\x00please input\x00wrong\x00AlphaBeta\x00")
        samples.append(_sample(path, tmp_path, sample_id=sample_id))
    solved_path = tmp_path / "solved.exe"
    solved_path.write_bytes(b"MZ\x00SolvedCandidate\x00")
    solved = _sample(solved_path, tmp_path, sample_id="4c69f173f2bd0211")

    monkeypatch.setattr(compare_site, "run_probe", lambda **_: _probe("wrong, try again"))
    result = compare_site.run_compare_site_extraction(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": samples + [solved]},
        benchmark=_benchmark(samples + [solved]),
        string_result=_string_result(samples, include_extra=True),
        policy=_policy(tmp_path),
    )

    assert result["target_count"] == 3
    assert {target["sample_id"] for target in result["targets"]} == compare_site.TARGET_SAMPLE_IDS


def test_solved_previous_target_is_not_selected(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "demo.exe"
    path.write_bytes(b"MZ\x00AlphaBeta\x00")
    sample = _sample(path, tmp_path, sample_id="4c69f173f2bd0211")

    monkeypatch.setattr(compare_site, "run_probe", lambda **_: _probe("success"))
    result = compare_site.run_compare_site_extraction(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        benchmark=_benchmark([sample]),
        string_result=_string_result([sample], solved_ids={sample["sample_id"]}),
        policy=_policy(tmp_path),
    )

    assert result["status"] == "BLOCKED"
    assert result["target_count"] == 0


def test_sha_mismatch_path_escape_and_policy_false_block_without_probe(tmp_path: Path, monkeypatch) -> None:
    outside = tmp_path.parent / "outside_compare_site_escape.exe"
    outside.write_bytes(b"MZ\x00AlphaBeta\x00")
    calls = []
    try:
        escaped = {
            "sample_id": "4c69f173f2bd0211",
            "relative_path": "../outside_compare_site_escape.exe",
            "extension": ".exe",
            "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
            "artifact_role": "challenge_binary",
            "triage_tags": ["strcmp"],
        }
        mismatch_path = tmp_path / "mismatch.exe"
        mismatch_path.write_bytes(b"MZ\x00AlphaBeta\x00")
        mismatch = _sample(mismatch_path, tmp_path, sample_id="bcbd9979db015bfd")
        mismatch["sha256"] = "0" * 64
        ok_path = tmp_path / "ok.exe"
        ok_path.write_bytes(b"MZ\x00AlphaBeta\x00")
        ok = _sample(ok_path, tmp_path, sample_id="18019fca52b389fe")

        monkeypatch.setattr(compare_site, "run_probe", lambda **kwargs: calls.append(kwargs) or _probe("success"))
        result = compare_site.run_compare_site_extraction(
            corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [escaped, mismatch, ok]},
            benchmark=_benchmark([escaped, mismatch, ok]),
            string_result=_string_result([escaped, mismatch, ok]),
            policy=_policy(tmp_path, runtime_allowed=False),
        )

        assert result["status"] == "BLOCKED"
        assert calls == []
        reasons = {reason for target in result["targets"] for reason in target["blocked_reasons"]}
        assert {"PATH_OUTSIDE_ROOT", "SHA256_MISMATCH", "RUNTIME_NOT_ALLOWED_BY_POLICY"} <= reasons
    finally:
        outside.unlink(missing_ok=True)


def test_strings_summary_candidate_limit_and_failed_runtime_validation(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "demo.exe"
    payload = b"MZ\x00please input your flag\x00wrong, try again\x00correct\x00"
    payload += b"\x00".join(f"Candidate{i:02d}".encode("ascii") for i in range(40))
    path.write_bytes(payload)
    sample = _sample(path, tmp_path, sample_id="4c69f173f2bd0211")

    monkeypatch.setattr(compare_site, "run_probe", lambda **_: _probe("correct but wrong"))
    result = compare_site.run_compare_site_extraction(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        benchmark=_benchmark([sample]),
        string_result=_string_result([sample]),
        policy=_policy(tmp_path),
    )

    target = result["targets"][0]
    assert target["strings_summary"]["prompt_strings"]
    assert target["strings_summary"]["failure_strings"]
    assert target["strings_summary"]["success_strings"]
    assert target["new_candidate_count"] == 30
    assert target["validated_candidate_count"] == 30
    assert target["solved"] is False
    assert target["missing_evidence"] == "new_candidates_failed_runtime_validation"


def test_successful_new_candidate_records_runtime_evidence(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "demo.exe"
    path.write_bytes(b"MZ\x00please input\x00success\x00AlphaBeta\x00")
    sample = _sample(path, tmp_path, sample_id="4c69f173f2bd0211")

    monkeypatch.setattr(compare_site, "run_probe", lambda **_: _probe("success"))
    result = compare_site.run_compare_site_extraction(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        benchmark=_benchmark([sample]),
        string_result=_string_result([sample]),
        policy=_policy(tmp_path),
    )

    target = result["targets"][0]
    assert result["status"] == "SUCCESS"
    assert target["solved"] is True
    assert target["solution"] == "AlphaBeta"
    assert target["runtime_evidence"]["success"] is True


def test_result_schema_when_compare_site_not_found(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "demo.exe"
    path.write_bytes(b"MZ\x00AlphaBeta\x00")
    sample = _sample(path, tmp_path, sample_id="4c69f173f2bd0211")

    monkeypatch.setattr(compare_site, "run_probe", lambda **_: _probe("wrong"))
    result = compare_site.run_compare_site_extraction(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        benchmark=_benchmark([sample]),
        string_result=_string_result([sample]),
        policy=_policy(tmp_path),
    )

    target = result["targets"][0]
    assert result["schema_version"] == 1
    assert result["stage"] == "bounded_compare_site_static_extraction"
    assert target["compare_site_status"] == "not_found"
    assert target["missing_evidence"] == "compare_site_not_found"


def test_readme_no_longer_recommends_old_local_samples_flow() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "python -m reverse_agent.local_samples add" not in text
    assert "python -m reverse_agent.local_samples solve" not in text
    assert "local_reverse_samples\\<case_id>\\" not in text


def _probe(stdout: str) -> dict:
    return {
        "probe_name": "compare_site_candidate_1",
        "exit_code": 0,
        "timeout": False,
        "stdout_preview": stdout,
        "stderr_preview": "",
        "duration_ms": 1,
        "classification": "prints_success_failure",
    }
