from pathlib import Path

from reverse_agent.local_reverse_constraint_recovery import run_constraint_recovery


def _summary() -> dict:
    return {
        "schema_version": 1,
        "status": "SUCCESS",
        "targets": [
            {"sample_id": "sha", "relative_path": "course/sha_256.exe"},
            {"sample_id": "cpp2", "relative_path": "course/CPP2.exe"},
            {"sample_id": "cpp1", "relative_path": "course/Cpp1.exe"},
        ],
    }


def _solver_result() -> dict:
    return {
        "schema_version": 1,
        "targets": [
            {
                "sample_id": "sha",
                "relative_path": "course/sha_256.exe",
                "classification": "sha256_hex_compare_with_post_hash_character_adjustment",
            },
            {
                "sample_id": "cpp2",
                "relative_path": "course/CPP2.exe",
                "classification": "bounded_input_range_hash_output_increment_compare",
            },
            {
                "sample_id": "cpp1",
                "relative_path": "course/Cpp1.exe",
                "classification": "api_assisted_password_write_and_compare",
            },
        ],
    }


def _policy(tmp_path: Path) -> dict:
    return {
        "schema_version": 1,
        "root": str(tmp_path),
        "runtime_allowed": True,
        "default_timeout_seconds": 1,
        "max_timeout_seconds": 2,
    }


def _artifact_item(path: Path, freshness: str = "current") -> dict:
    return {
        "kind": path.stem,
        "path": str(path),
        "freshness": freshness,
        "source_run": "test_run",
    }


def _index(tmp_path: Path, *, stale_sha: bool = False) -> dict:
    summary_path = tmp_path / "summary.json"
    sha_path = tmp_path / "sha.json"
    cpp2_path = tmp_path / "cpp2.json"
    cpp1_path = tmp_path / "cpp1.json"
    _write_json(summary_path, {"status": "SUCCESS"})
    _write_json(sha_path, _sha_evidence())
    _write_json(cpp2_path, _cpp2_evidence())
    _write_json(cpp1_path, _cpp1_evidence())

    latest_v2 = {
        "local_reverse_ida_summary": _artifact_item(summary_path),
        "local_reverse_ida_evidence_sha": _artifact_item(sha_path, "stale" if stale_sha else "current"),
        "local_reverse_ida_evidence_cpp2": _artifact_item(cpp2_path),
        "local_reverse_ida_evidence_cpp1": _artifact_item(cpp1_path),
    }
    latest = {
        "local_reverse_ida_summary": str(summary_path),
        "local_reverse_ida_evidence_sha": str(sha_path),
        "local_reverse_ida_evidence_cpp2": str(cpp2_path),
        "local_reverse_ida_evidence_cpp1": str(cpp1_path),
    }
    return {"latest_artifacts": latest, "latest_artifacts_v2": latest_v2}


def _sha_evidence() -> dict:
    target = "493f877692ea8d507fa98355a054efede85e7c7bbc9ba9890ea99b7b33e281fc"
    return {
        "compare_contexts": [{"nearby": f'push 40h || "{target}"'}],
        "local_check_contexts": [{"ref_strings": "%08x%08x%08x%08x%08x%08x%08x%08x"}],
        "decompiler_snippets": [
            {
                "function": "_main_0",
                "text": (
                    "if ( strlen(Source) >= 5 ) { strncpy(&Destination, Source, 4u); "
                    "sub_401005(Str1, (int)&Destination, v4); "
                    "for ( i = 0; i < 64; ++i ) { if ( ++Str1[i] == 103 ) Str1[i] = 97; "
                    "if ( Str1[i] == 58 ) Str1[i] = 48; } "
                    f'if ( !strncmp(Str1, "{target}", 0x40u) ) printf("Well done!"); }}'
                ),
            }
        ],
    }


def _cpp2_evidence() -> dict:
    target = "b" * 64
    return {
        "compare_contexts": [{"nearby": f'push 40h || "{target}"'}],
        "local_check_contexts": [{"ref_strings": "%08x%08x%08x%08X%08x%08x%08x%08x"}],
        "decompiler_snippets": [
            {
                "function": "_main_0",
                "text": (
                    "if ( Source[i] < 65 || Source[i] > 122 ) printf(\"The inputs are out of the scope!\"); "
                    "if ( strlen(Source) >= 5 ) { strncpy(&Destination, Source, 4u); "
                    "sub_401005(Str1, (int)&Destination, v4); "
                    "for ( j = 0; j < 64; ++j ) ++Str1[j]; "
                    f'if ( !strncmp(Str1, "{target}", 0x40u) ) printf("Correct!"); }}'
                ),
            }
        ],
    }


def _cpp1_evidence() -> dict:
    return {
        "compare_contexts": [{"callee": "__imp_lstrcmpA"}],
        "local_check_contexts": [{"ref_strings": "realpwd | pwd.txt | WriteFile | kernel32.dll"}],
        "decompiler_snippets": [
            {
                "function": "_main_0",
                "text": (
                    'strcpy((char *)Buffer, "realpwd"); '
                    'CreateFileA("pwd.txt", 0x10000000u, 0, 0, 2u, 0x80u, 0); '
                    "WriteFile(hFile, Buffer, v3, (LPDWORD)&Buffer[2], 0); "
                    "lstrcmpA(Buffer, String2);"
                ),
            },
            {
                "function": "sub_401100",
                "text": (
                    "Str[0] = 26; Str[1] = 10; Str[2] = 14; Str[3] = 7; "
                    "Str[4] = 17; Str[5] = 7; Str[6] = 13; "
                    "printf(\"Please input your flag \\n\"); scanf(\"%s\", v11); "
                    "for ( i = 0; i < 7; ++i ) Str[i] ^= v11[i];"
                ),
            },
        ],
    }


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


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")


def test_cpp1_generates_alternate_candidates_and_rejects_mixed_output(tmp_path: Path) -> None:
    sample_dir = tmp_path / "course"
    sample_dir.mkdir()
    (sample_dir / "sha_256.exe").write_text("placeholder", encoding="utf-8")
    (sample_dir / "CPP2.exe").write_text("placeholder", encoding="utf-8")
    (sample_dir / "Cpp1.exe").write_text("placeholder", encoding="utf-8")

    result = run_constraint_recovery(
        ida_summary=_summary(),
        artifact_index=_index(tmp_path),
        solver_result=_solver_result(),
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe("Correct!\ntry again!\n"),
    )

    by_id = {target["sample_id"]: target for target in result["targets"]}
    cpp1 = by_id["cpp1"]
    candidates = [item["candidate"] for item in cpp1["candidates"]]
    assert "hookapi" in candidates
    assert len(candidates) >= 2
    assert cpp1["validated_candidate"] == ""
    assert any(item["validation_status"] == "rejected" for item in cpp1["validation_results"])


def test_cpp2_target_before_increment_is_decremented(tmp_path: Path) -> None:
    result = run_constraint_recovery(
        ida_summary=_summary(),
        artifact_index=_index(tmp_path),
        solver_result=_solver_result(),
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe(""),
    )

    cpp2 = next(target for target in result["targets"] if target["sample_id"] == "cpp2")
    constraint_map = {item["kind"]: item.get("value") for item in cpp2["recovered_constraints"]}
    assert constraint_map["target_before_increment"] == "a" * 64


def test_sha_without_bounded_domain_generates_no_candidates(tmp_path: Path) -> None:
    result = run_constraint_recovery(
        ida_summary=_summary(),
        artifact_index=_index(tmp_path),
        solver_result=_solver_result(),
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe(""),
    )

    sha = next(target for target in result["targets"] if target["sample_id"] == "sha")
    assert sha["candidate_generation"]["count"] == 0
    assert sha["blocked_reason"] == "NO_BOUNDED_HASH_PREIMAGE_DOMAIN"


def test_candidate_limits_and_target_shape(tmp_path: Path) -> None:
    result = run_constraint_recovery(
        ida_summary=_summary(),
        artifact_index=_index(tmp_path),
        solver_result=_solver_result(),
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe(""),
    )

    assert result["target_count"] == 3
    assert len(result["targets"]) == 3
    for target in result["targets"]:
        assert target["constraint_status"]
        assert target["next_action"]
        assert target["candidate_generation"]["count"] <= 64


def test_stale_artifact_blocks_and_ignores_legacy(tmp_path: Path) -> None:
    result = run_constraint_recovery(
        ida_summary=_summary(),
        artifact_index=_index(tmp_path, stale_sha=True),
        solver_result=_solver_result(),
        policy=_policy(tmp_path),
        probe_runner=lambda **_: _probe(""),
    )

    sha = next(target for target in result["targets"] if target["sample_id"] == "sha")
    assert sha["constraint_status"] == "blocked"
    assert "ARTIFACT_NOT_CURRENT" in sha["blocked_reason"]
