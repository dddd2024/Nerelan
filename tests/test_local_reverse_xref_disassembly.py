import hashlib
import struct
from pathlib import Path

import reverse_agent.local_reverse_xref_disassembly as xref


def _mapping() -> xref.PEMapping:
    return xref.PEMapping(
        image_base=0x400000,
        sections=[
            xref.Section(".text", rva=0x1000, virtual_size=0x400, raw_offset=0x200, raw_size=0x400, executable=True),
            xref.Section(".rdata", rva=0x2000, virtual_size=0x400, raw_offset=0x600, raw_size=0x400, executable=False),
        ],
    )


def _sample(path: Path, root: Path, *, sample_id: str = "4c69f173f2bd0211") -> dict:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return {
        "sample_id": sample_id,
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
            }
            for sample in samples
        ],
    }


def _compare_site_result(samples: list[dict], *, solved_ids: set[str] | None = None, include_extra: bool = False) -> dict:
    solved_ids = solved_ids or set()
    targets = []
    for sample in samples:
        solved = sample["sample_id"] in solved_ids
        targets.append({
            "sample_id": sample["sample_id"],
            "relative_path": sample["relative_path"],
            "sha256": sample["sha256"],
            "solved": solved,
            "missing_evidence": None if solved else "new_candidates_failed_runtime_validation",
            "strings_summary": {
                "success_strings": [{"value": "Well done!", "encoding": "ascii", "offset": 0x600}],
                "failure_strings": [{"value": "Wrong!", "encoding": "ascii", "offset": 0x610}],
                "prompt_strings": [{"value": "Please input:", "encoding": "ascii", "offset": 0x620}],
                "candidate_constant_strings": [],
            },
            "compare_site_evidence": {
                "compare_keyword_strings": [{"value": "CompareStringA", "encoding": "ascii", "offset": 0x630}],
            },
            "validation_results_preview": [{"candidate": "OldSecret"}],
        })
    if include_extra:
        targets.append({
            "sample_id": "not_in_scope",
            "relative_path": "ignored.exe",
            "sha256": "0" * 64,
            "solved": False,
            "missing_evidence": "new_candidates_failed_runtime_validation",
        })
    return {"schema_version": 1, "targets": targets}


def _string_result(samples: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "targets": [
            {
                "sample_id": sample["sample_id"],
                "relative_path": sample["relative_path"],
                "validation_results_preview": [{"candidate": "StringSolverFailed"}],
            }
            for sample in samples
        ],
    }


def _binary_with_xref(candidate: bytes = b"Secret42\x00") -> bytes:
    data = bytearray(b"\x00" * 0xA00)
    string_va = 0x402000
    code = b"\x68" + struct.pack("<I", string_va) + b"\x83\xf8\x01\x75\x02\xe8\x00\x00\x00\x00"
    data[0x200:0x200 + len(code)] = code
    data[0x600:0x600 + len(candidate)] = candidate
    data[0x610:0x617] = b"Wrong!\x00"
    data[0x620:0x62e] = b"Please input:\x00"
    data[0x630:0x63f] = b"CompareStringA\x00"
    return bytes(data)


def test_pe_mapping_raw_rva_va_roundtrip() -> None:
    mapping = _mapping()

    assert mapping.raw_to_rva(0x600) == 0x2000
    assert mapping.raw_to_va(0x600) == 0x402000
    assert mapping.rva_to_raw(0x2000) == 0x600
    assert mapping.va_to_raw(0x402000) == 0x600


def test_find_xrefs_respects_limit() -> None:
    mapping = _mapping()
    data = bytearray(b"\x00" * 0xA00)
    data[0x200:0x204] = struct.pack("<I", 0x402000)
    data[0x210:0x214] = struct.pack("<I", 0x402000)
    key = {"raw_offset": 0x600, "rva": 0x2000, "va": 0x402000}

    xrefs = xref.find_xrefs(bytes(data), mapping, key, max_xrefs=1)

    assert len(xrefs) == 1
    assert xrefs[0]["reference_kind"] == "va32"


def test_disassembly_window_and_candidate_extraction_are_bounded() -> None:
    mapping = _mapping()
    data = _binary_with_xref()
    key = {"raw_offset": 0x600, "rva": 0x2000, "va": 0x402000}
    xrefs = xref.find_xrefs(data, mapping, key, max_xrefs=20)

    window = xref.disassemble_xref_window(
        data=data,
        mapping=mapping,
        xref=xrefs[0],
        max_instructions=3,
        max_bytes=64,
    )
    candidates = xref.build_xref_candidates(
        windows=[window],
        mapping=mapping,
        strings_by_offset={0x600: "Secret42"},
        previous_failed_candidates=set(),
        max_candidates=20,
    )

    assert window is not None
    assert window["instruction_count"] <= 3
    assert window["branch_hints"]["has_branch_or_compare"] is True
    assert candidates == [{"candidate": "Secret42", "source": "xref_push"}]


def test_run_selects_only_unsolved_targets_and_records_success(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(_binary_with_xref())
    sample = _sample(exe, tmp_path)

    monkeypatch.setattr(xref, "parse_pe_mapping", lambda _: _mapping())
    monkeypatch.setattr(xref, "run_probe", lambda **_: _probe("success"))
    result = xref.run_xref_disassembly(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        benchmark=_benchmark([sample]),
        string_result=_string_result([sample]),
        compare_site_result=_compare_site_result([sample], include_extra=True),
        policy=_policy(tmp_path),
    )

    target = result["targets"][0]
    assert result["status"] == "SUCCESS"
    assert result["target_count"] == 1
    assert target["solution"] == "Secret42"
    assert target["pe_mapping_status"] == "ok"
    assert target["capstone_status"] == "available_used"
    assert target["xref_summary"][0]["xref_candidates"]


def test_solved_compare_site_target_is_not_selected(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(_binary_with_xref())
    sample = _sample(exe, tmp_path)

    monkeypatch.setattr(xref, "parse_pe_mapping", lambda _: _mapping())
    result = xref.run_xref_disassembly(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        benchmark=_benchmark([sample]),
        string_result=_string_result([sample]),
        compare_site_result=_compare_site_result([sample], solved_ids={sample["sample_id"]}),
        policy=_policy(tmp_path),
    )

    assert result["status"] == "BLOCKED"
    assert result["target_count"] == 0


def test_sha_mismatch_path_escape_and_runtime_policy_block_without_probe(tmp_path: Path, monkeypatch) -> None:
    outside = tmp_path.parent / "outside_xref_escape.exe"
    outside.write_bytes(_binary_with_xref())
    calls = []
    try:
        escaped = {
            "sample_id": "4c69f173f2bd0211",
            "relative_path": "../outside_xref_escape.exe",
            "extension": ".exe",
            "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
            "artifact_role": "challenge_binary",
            "triage_tags": ["strcmp"],
        }
        mismatch_path = tmp_path / "mismatch.exe"
        mismatch_path.write_bytes(_binary_with_xref())
        mismatch = _sample(mismatch_path, tmp_path, sample_id="bcbd9979db015bfd")
        mismatch["sha256"] = "0" * 64

        monkeypatch.setattr(xref, "parse_pe_mapping", lambda _: _mapping())
        monkeypatch.setattr(xref, "run_probe", lambda **kwargs: calls.append(kwargs) or _probe("success"))
        result = xref.run_xref_disassembly(
            corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [escaped, mismatch]},
            benchmark=_benchmark([escaped, mismatch]),
            string_result=_string_result([escaped, mismatch]),
            compare_site_result=_compare_site_result([escaped, mismatch]),
            policy=_policy(tmp_path, runtime_allowed=False),
        )

        assert result["status"] == "BLOCKED"
        assert calls == []
        reasons = {reason for target in result["targets"] for reason in target["blocked_reasons"]}
        assert {"PATH_OUTSIDE_ROOT", "SHA256_MISMATCH", "RUNTIME_NOT_ALLOWED_BY_POLICY"} <= reasons
    finally:
        outside.unlink(missing_ok=True)


def test_old_failed_candidate_is_not_revalidated(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(_binary_with_xref(candidate=b"OldSecret\x00"))
    sample = _sample(exe, tmp_path)

    monkeypatch.setattr(xref, "parse_pe_mapping", lambda _: _mapping())
    monkeypatch.setattr(xref, "run_probe", lambda **_: _probe("success"))
    result = xref.run_xref_disassembly(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        benchmark=_benchmark([sample]),
        string_result=_string_result([sample]),
        compare_site_result=_compare_site_result([sample]),
        policy=_policy(tmp_path),
    )

    target = result["targets"][0]
    assert target["new_candidate_count"] == 0
    assert target["validated_candidate_count"] == 0
    assert target["solved"] is False


def test_wrong_output_cannot_solve_and_schema_is_specific(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(_binary_with_xref())
    sample = _sample(exe, tmp_path)

    monkeypatch.setattr(xref, "parse_pe_mapping", lambda _: _mapping())
    monkeypatch.setattr(xref, "run_probe", lambda **_: _probe("correct but wrong"))
    result = xref.run_xref_disassembly(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        benchmark=_benchmark([sample]),
        string_result=_string_result([sample]),
        compare_site_result=_compare_site_result([sample]),
        policy=_policy(tmp_path),
    )

    target = result["targets"][0]
    assert result["schema_version"] == 1
    assert result["stage"] == "bounded_xref_disassembly_extraction"
    assert target["solved"] is False
    assert target["missing_evidence"] == "new_xref_candidates_failed_runtime_validation"


def _probe(stdout: str) -> dict:
    return {
        "probe_name": "xref_candidate_1",
        "exit_code": 0,
        "timeout": False,
        "stdout_preview": stdout,
        "stderr_preview": "",
        "duration_ms": 1,
        "classification": "prints_success_failure",
    }
