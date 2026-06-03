import hashlib
from pathlib import Path

import reverse_agent.local_reverse_semantic_rules as semantic


def _sample(path: Path, root: Path, *, sample_id: str = "4c69f173f2bd0211") -> dict:
    data = path.read_bytes()
    return {
        "sample_id": sample_id,
        "relative_path": path.relative_to(root).as_posix(),
        "extension": ".exe",
        "sha256": hashlib.sha256(data).hexdigest(),
        "artifact_role": "challenge_binary",
    }


def _policy(root: Path, *, runtime_allowed: bool = True) -> dict:
    return {
        "schema_version": 1,
        "root": str(root),
        "runtime_allowed": runtime_allowed,
        "default_timeout_seconds": 1,
        "max_timeout_seconds": 2,
    }


def _instruction(address: int, mnemonic: str, op_str: str) -> dict:
    return {
        "address": hex(address),
        "rva": hex(address - 0x400000),
        "mnemonic": mnemonic,
        "op_str": op_str,
    }


def _semantic_window() -> dict:
    return {
        "xref": {"rva": 0x1234, "section": ".text"},
        "window_raw_start": 0x200,
        "window_raw_end": 0x280,
        "instructions": [
            _instruction(0x401000, "mov", "dword ptr [ebp - 0x450], 0"),
            _instruction(0x401006, "cmp", "dword ptr [ebp - 0x450], 0x10"),
            _instruction(0x40100D, "jge", "0x401040"),
            _instruction(0x401010, "mov", "cl, byte ptr [ebp + eax - 0x44]"),
            _instruction(0x401014, "add", "cl, 1"),
            _instruction(0x401017, "mov", "byte ptr [ebp + edx - 0x44], cl"),
            _instruction(0x40101B, "movsx", "ecx, byte ptr [ebp + eax - 0x44]"),
            _instruction(0x401020, "cmp", "ecx, 0x67"),
            _instruction(0x401023, "jne", "0x401030"),
            _instruction(0x401025, "mov", "byte ptr [ebp + edx - 0x44], 0x61"),
            _instruction(0x401030, "xor", "cl, 0x20"),
            _instruction(0x401034, "sub", "cl, 2"),
        ],
    }


def _target(sample: dict, *, solved: bool = False, missing_evidence: str | None = None) -> dict:
    return {
        "sample_id": sample["sample_id"],
        "relative_path": sample["relative_path"],
        "sha256": sample["sha256"],
        "solved": solved,
        "missing_evidence": missing_evidence or semantic.PREVIOUS_MISSING_EVIDENCE,
        "disassembly_windows": [_semantic_window()],
        "validation_results_preview": [{"candidate": "OldFailed"}],
    }


def _xref_result(targets: list[dict]) -> dict:
    return {"schema_version": 1, "targets": targets}


def _probe(stdout: str, stderr: str = "") -> dict:
    return {
        "probe_name": "semantic",
        "stdin": "",
        "exit_code": 0,
        "timeout": False,
        "stdout_preview": stdout,
        "stderr_preview": stderr,
        "duration_ms": 1,
        "classification": "prints_success_failure",
    }


def test_selects_only_unsolved_in_scope_xref_targets(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"demo")
    selected = _sample(exe, tmp_path, sample_id="4c69f173f2bd0211")
    solved = _sample(exe, tmp_path, sample_id="bcbd9979db015bfd")
    wrong_missing = _sample(exe, tmp_path, sample_id="18019fca52b389fe")
    out_of_scope = _sample(exe, tmp_path, sample_id="not_in_scope")
    monkeypatch.setattr(semantic, "run_probe", lambda **_: _probe("wrong"))

    result = semantic.run_semantic_rule_extraction(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [selected, solved, wrong_missing, out_of_scope]},
        xref_result=_xref_result([
            _target(selected),
            _target(solved, solved=True),
            _target(wrong_missing, missing_evidence="some_other_reason"),
            _target(out_of_scope),
        ]),
        policy=_policy(tmp_path),
    )

    assert result["target_count"] == 1
    assert result["targets"][0]["sample_id"] == "4c69f173f2bd0211"


def test_extracts_semantic_rule_types_from_synthetic_window() -> None:
    rules = semantic.extract_semantic_rules(
        {"disassembly_windows": [_semantic_window()]},
        max_rules=20,
    )
    rule_types = {rule["rule_type"] for rule in rules}

    assert {
        "loop_bound",
        "stack_buffer",
        "byte_load",
        "byte_store",
        "byte_add_const",
        "byte_sub_const",
        "byte_xor_const",
        "byte_cmp_const",
        "replacement_rule",
    } <= rule_types
    assert all("source_window" in rule for rule in rules)
    assert all("source_instructions" in rule for rule in rules)


def test_rule_and_candidate_generation_are_bounded(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"demo")
    sample = _sample(exe, tmp_path)
    many_windows = [_semantic_window() for _ in range(8)]
    target = _target(sample)
    target["disassembly_windows"] = many_windows
    monkeypatch.setattr(semantic, "run_probe", lambda **_: _probe("wrong"))

    result = semantic.run_semantic_rule_extraction(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        xref_result=_xref_result([target]),
        policy=_policy(tmp_path),
        max_rules_per_sample=5,
        max_candidates_per_sample=3,
        max_runtime_validations_per_sample=3,
    )
    actual = result["targets"][0]

    assert actual["semantic_rule_count"] == 5
    assert actual["generated_candidate_count"] <= 3
    assert actual["validated_candidate_count"] <= 3


def test_old_failed_candidate_is_revalidated_only_with_semantic_reason() -> None:
    rules = [{
        "rule_id": "rule_001",
        "rule_type": "byte_cmp_const",
        "candidate_generation_enabled": True,
        "inferred_constraint": {"constant": ord("A")},
        "source_window": {},
        "source_instructions": [],
    }]

    candidates = semantic.build_semantic_candidates(
        rules=rules,
        previous_failed_candidates={"AAAA"},
        max_candidates=20,
    )

    assert candidates[0]["candidate"] == "AAAA"
    assert candidates[0]["revalidated_reason"] == "semantic_rule_derived"


def test_runtime_policy_block_prevents_probe(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"demo")
    sample = _sample(exe, tmp_path)
    calls = []
    monkeypatch.setattr(semantic, "run_probe", lambda **kwargs: calls.append(kwargs) or _probe("correct"))

    result = semantic.run_semantic_rule_extraction(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        xref_result=_xref_result([_target(sample)]),
        policy=_policy(tmp_path, runtime_allowed=False),
    )

    assert result["status"] == "BLOCKED"
    assert calls == []
    assert "RUNTIME_NOT_ALLOWED_BY_POLICY" in result["targets"][0]["blocked_reasons"]


def test_path_escape_and_sha_mismatch_prevent_probe(tmp_path: Path, monkeypatch) -> None:
    outside = tmp_path.parent / "outside_semantic_escape.exe"
    outside.write_bytes(b"outside")
    mismatch = tmp_path / "mismatch.exe"
    mismatch.write_bytes(b"mismatch")
    calls = []
    try:
        escaped_sample = {
            "sample_id": "4c69f173f2bd0211",
            "relative_path": "../outside_semantic_escape.exe",
            "extension": ".exe",
            "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
            "artifact_role": "challenge_binary",
        }
        mismatch_sample = _sample(mismatch, tmp_path, sample_id="bcbd9979db015bfd")
        mismatch_sample["sha256"] = "0" * 64
        monkeypatch.setattr(semantic, "run_probe", lambda **kwargs: calls.append(kwargs) or _probe("correct"))

        result = semantic.run_semantic_rule_extraction(
            corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [escaped_sample, mismatch_sample]},
            xref_result=_xref_result([_target(escaped_sample), _target(mismatch_sample)]),
            policy=_policy(tmp_path),
        )

        assert result["status"] == "BLOCKED"
        assert calls == []
        reasons = {reason for target in result["targets"] for reason in target["blocked_reasons"]}
        assert {"PATH_OUTSIDE_ROOT", "SHA256_MISMATCH"} <= reasons
    finally:
        outside.unlink(missing_ok=True)


def test_success_failure_conflict_does_not_solve(tmp_path: Path, monkeypatch) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"demo")
    sample = _sample(exe, tmp_path)
    monkeypatch.setattr(semantic, "run_probe", lambda **_: _probe("correct but wrong"))

    result = semantic.run_semantic_rule_extraction(
        corpus_index={"schema_version": 1, "root": str(tmp_path), "samples": [sample]},
        xref_result=_xref_result([_target(sample)]),
        policy=_policy(tmp_path),
    )

    target = result["targets"][0]
    assert target["validated_candidate_count"] > 0
    assert target["solved"] is False
    assert target["solution"] is None
