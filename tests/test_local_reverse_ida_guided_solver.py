from pathlib import Path

from reverse_agent.local_reverse_ida_guided_solver import run_ida_guided_solver


def _summary() -> dict:
    return {
        "schema_version": 1,
        "status": "SUCCESS",
        "target_count": 3,
        "targets": [
            {
                "sample_id": "sha",
                "relative_path": "course/sha_256.exe",
                "ida_status": "success",
            },
            {
                "sample_id": "cpp2",
                "relative_path": "course/CPP2.exe",
                "ida_status": "success",
            },
            {
                "sample_id": "cpp1",
                "relative_path": "course/Cpp1.exe",
                "ida_status": "success",
            },
        ],
    }


def _index(tmp_path: Path) -> dict:
    return {
        "latest_artifacts": {
            "local_reverse_ida_summary": "project_state/local_reverse_ida_summary.json",
            "local_reverse_ida_evidence_sha": str(tmp_path / "sha.json"),
            "local_reverse_ida_evidence_cpp2": str(tmp_path / "cpp2.json"),
            "local_reverse_ida_evidence_cpp1": str(tmp_path / "cpp1.json"),
        },
        "latest_artifacts_v2": {
            "local_reverse_ida_summary": _artifact_item(tmp_path / "summary.json"),
            "local_reverse_ida_evidence_sha": _artifact_item(tmp_path / "sha.json"),
            "local_reverse_ida_evidence_cpp2": _artifact_item(tmp_path / "cpp2.json"),
            "local_reverse_ida_evidence_cpp1": _artifact_item(tmp_path / "cpp1.json"),
        },
    }


def _policy(tmp_path: Path) -> dict:
    return {
        "schema_version": 1,
        "root": str(tmp_path),
        "runtime_allowed": True,
        "default_timeout_seconds": 1,
        "max_timeout_seconds": 2,
    }


def test_ida_guided_solver_classifies_three_profiles(tmp_path: Path) -> None:
    sample_dir = tmp_path / "course"
    sample_dir.mkdir()
    (sample_dir / "Cpp1.exe").write_text("placeholder", encoding="utf-8")
    _write_json(tmp_path / "summary.json", {"status": "SUCCESS"})
    _write_json(
        tmp_path / "sha.json",
        {
            "compare_contexts": [{"nearby": 'push 40h || push offset "493f877692ea8d507fa98355a054efede85e7c7bbc9ba9890ea99b7b33e281fc"'}],
            "local_check_contexts": [{"ref_strings": "%08x%08x%08x%08x%08x%08x%08x%08x"}],
            "decompiler_snippets": [{"text": "sub_401005(Str1, Source, v4); ++Str1[i];"}],
        },
    )
    _write_json(
        tmp_path / "cpp2.json",
        {
            "compare_contexts": [{"nearby": 'push 40h || push offset "1f2e28649c4g:25:8bb"'}],
            "local_check_contexts": [{"ref_strings": "%08x%08x%08x%08X%08x%08x%08x%08x"}],
            "decompiler_snippets": [
                {"text": "if ( Source[i] < 65 || Source[i] > 122 ) return; for ( j = 0; j < 64; ++j ) ++Str1[j];"}
            ],
        },
    )
    _write_json(
        tmp_path / "cpp1.json",
        {
            "compare_contexts": [{"callee": "__imp_lstrcmpA"}],
            "decompiler_snippets": [
                {"text": 'strcpy((char *)Buffer, "realpwd"); GetProcAddress(hModule, "WriteFile");'},
                {
                    "text": (
                        "Str[0] = 26; Str[1] = 10; Str[2] = 14; Str[3] = 7; "
                        "Str[4] = 17; Str[5] = 7; Str[6] = 13; "
                        'ProcAddress = GetProcAddress(ModuleHandleA, "WriteFile");'
                    )
                },
            ],
        },
    )

    result = run_ida_guided_solver(
        ida_summary=_summary(),
        artifact_index=_index(tmp_path),
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe("Correct!\n"),
    )

    assert result["target_count"] == 3
    assert len(result["targets"]) == 3
    by_id = {target["sample_id"]: target for target in result["targets"]}
    assert by_id["sha"]["selected_solver_profile"] == "hash_hex_compare_static"
    assert by_id["cpp2"]["selected_solver_profile"] == "bounded_char_transform_inversion"
    assert by_id["cpp1"]["selected_solver_profile"] == "direct_or_api_password_extraction"
    assert by_id["cpp1"]["candidate"] == "hookapi"
    assert by_id["cpp1"]["validation_status"] == "validated"


def test_missing_raw_ida_json_blocks_without_probe(tmp_path: Path) -> None:
    calls = []
    result = run_ida_guided_solver(
        ida_summary=_summary(),
        artifact_index={"latest_artifacts": {"local_reverse_ida_summary": "summary.json"}},
        policy=_policy(tmp_path),
        probe_runner=lambda **kwargs: calls.append(kwargs) or _probe("Correct!\n"),
    )

    assert result["status"] == "BLOCKED"
    assert calls == []
    assert all(target["validation_status"] == "blocked" for target in result["targets"])


def test_stale_v2_blocks_and_does_not_read_legacy_artifact(tmp_path: Path) -> None:
    _write_json(tmp_path / "summary.json", {"status": "SUCCESS"})
    _write_json(
        tmp_path / "legacy_sha.json",
        {
            "compare_contexts": [{"nearby": 'push 40h || push offset "493f877692ea8d507fa98355a054efede85e7c7bbc9ba9890ea99b7b33e281fc"'}],
            "local_check_contexts": [{"ref_strings": "%08x%08x%08x%08x%08x%08x%08x%08x"}],
            "decompiler_snippets": [{"text": "sub_401005(Str1, Source, v4);"}],
        },
    )
    index = _index_with_blank_current_evidence(tmp_path)
    index["latest_artifacts"]["local_reverse_ida_evidence_sha"] = str(tmp_path / "legacy_sha.json")
    index["latest_artifacts_v2"]["local_reverse_ida_evidence_sha"] = {
        "kind": "local_reverse_ida_evidence_sha",
        "path": str(tmp_path / "stale_sha.json"),
        "freshness": "stale",
    }

    result = run_ida_guided_solver(
        ida_summary=_summary(),
        artifact_index=index,
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe("Correct!\n"),
    )

    by_id = {target["sample_id"]: target for target in result["targets"]}
    assert result["status"] == "BLOCKED"
    assert by_id["sha"]["validation_status"] == "blocked"
    assert "ARTIFACT_NOT_CURRENT:local_reverse_ida_evidence_sha:stale" in by_id["sha"]["blocked_reason"]
    assert by_id["sha"]["selected_solver_profile"] == "needs_more_static_evidence"


def test_missing_v2_blocks_even_when_legacy_artifact_exists(tmp_path: Path) -> None:
    _write_json(tmp_path / "summary.json", {"status": "SUCCESS"})
    _write_json(tmp_path / "legacy_sha.json", {"compare_contexts": [{"nearby": "push 40h"}]})
    index = _index_with_blank_current_evidence(tmp_path)
    index["latest_artifacts"]["local_reverse_ida_evidence_sha"] = str(tmp_path / "legacy_sha.json")
    del index["latest_artifacts_v2"]["local_reverse_ida_evidence_sha"]

    result = run_ida_guided_solver(
        ida_summary=_summary(),
        artifact_index=index,
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe("Correct!\n"),
    )

    by_id = {target["sample_id"]: target for target in result["targets"]}
    assert result["status"] == "BLOCKED"
    assert by_id["sha"]["validation_status"] == "blocked"
    assert "ARTIFACT_V2_MISSING:local_reverse_ida_evidence_sha" in by_id["sha"]["blocked_reason"]


def test_filename_only_sha_classification_needs_more_static_evidence(tmp_path: Path) -> None:
    index = _index_with_blank_current_evidence(tmp_path)

    result = run_ida_guided_solver(
        ida_summary=_summary(),
        artifact_index=index,
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe("Correct!\n"),
    )

    by_id = {target["sample_id"]: target for target in result["targets"]}
    assert by_id["sha"]["relative_path"].endswith("sha_256.exe")
    assert by_id["sha"]["selected_solver_profile"] == "needs_more_static_evidence"
    assert by_id["sha"]["classification"] == "needs_more_static_evidence"


def test_hash_evidence_without_input_domain_has_no_candidate(tmp_path: Path) -> None:
    index = _index_with_blank_current_evidence(tmp_path)
    _write_json(
        tmp_path / "sha.json",
        {
            "compare_contexts": [{"nearby": 'push 40h || push offset "493f877692ea8d507fa98355a054efede85e7c7bbc9ba9890ea99b7b33e281fc"'}],
            "local_check_contexts": [{"ref_strings": "%08x%08x%08x%08x%08x%08x%08x%08x"}],
            "decompiler_snippets": [{"text": "sub_401005(Str1, Source, v4);"}],
        },
    )

    result = run_ida_guided_solver(
        ida_summary=_summary(),
        artifact_index=index,
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe("Correct!\n"),
    )

    by_id = {target["sample_id"]: target for target in result["targets"]}
    assert by_id["sha"]["selected_solver_profile"] == "hash_hex_compare_static"
    assert by_id["sha"]["candidate"] == ""
    assert by_id["sha"]["validation_status"] == "unverified"


def test_success_and_failure_output_is_rejected_and_not_solved(tmp_path: Path) -> None:
    sample_dir = tmp_path / "course"
    sample_dir.mkdir()
    (sample_dir / "Cpp1.exe").write_text("placeholder", encoding="utf-8")
    _write_json(tmp_path / "summary.json", {"status": "SUCCESS"})
    _write_json(tmp_path / "sha.json", {})
    _write_json(tmp_path / "cpp2.json", {})
    _write_json(
        tmp_path / "cpp1.json",
        {
            "compare_contexts": [{"callee": "__imp_lstrcmpA"}],
            "decompiler_snippets": [
                {"text": 'strcpy((char *)Buffer, "realpwd"); GetProcAddress(hModule, "WriteFile");'},
                {
                    "text": (
                        "Str[0] = 26; Str[1] = 10; Str[2] = 14; Str[3] = 7; "
                        "Str[4] = 17; Str[5] = 7; Str[6] = 13; "
                        'ProcAddress = GetProcAddress(ModuleHandleA, "WriteFile");'
                    )
                },
            ],
        },
    )

    result = run_ida_guided_solver(
        ida_summary=_summary(),
        artifact_index=_index(tmp_path),
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe("Correct!\ntry again!\n"),
    )

    by_id = {target["sample_id"]: target for target in result["targets"]}
    assert by_id["cpp1"]["candidate"] == "hookapi"
    assert by_id["cpp1"]["validation_status"] == "rejected"
    assert result["solved_count"] == 0
    assert result["validated_count"] == 0


def _probe(stdout: str) -> dict:
    return {
        "probe_name": "candidate_static_1",
        "exit_code": 0,
        "timeout": False,
        "stdout_preview": stdout,
        "stderr_preview": "",
        "duration_ms": 1,
        "classification": "prints_success_failure",
    }


def _artifact_item(path: Path, freshness: str = "current") -> dict:
    return {
        "kind": path.stem,
        "path": str(path),
        "freshness": freshness,
        "source_run": "test_run",
    }


def _index_with_blank_current_evidence(tmp_path: Path) -> dict:
    _write_json(tmp_path / "summary.json", {"status": "SUCCESS"})
    _write_json(tmp_path / "sha.json", {})
    _write_json(tmp_path / "cpp2.json", {})
    _write_json(tmp_path / "cpp1.json", {})
    return _index(tmp_path)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")
