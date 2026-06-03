import hashlib
import json
from pathlib import Path

from reverse_agent import local_reverse_ida_summary as ida_summary
from reverse_agent.tool_runners import ToolRunArtifact


def _sample(path: Path, root: Path, *, sample_id: str = "4c69f173f2bd0211") -> dict:
    data = path.read_bytes()
    return {
        "sample_id": sample_id,
        "relative_path": path.relative_to(root).as_posix(),
        "extension": ".exe",
        "sha256": hashlib.sha256(data).hexdigest(),
        "artifact_role": "challenge_binary",
    }


def _target(sample: dict, *, solved: bool = False, missing_evidence: str = "needs_symbolic_execution") -> dict:
    return {
        "sample_id": sample["sample_id"],
        "relative_path": sample["relative_path"],
        "sha256": sample["sha256"],
        "solved": solved,
        "missing_evidence": missing_evidence,
    }


def _policy(root: Path) -> dict:
    return {
        "schema_version": 1,
        "root": str(root),
        "default_timeout_seconds": 1,
        "max_timeout_seconds": 2,
    }


def _corpus(root: Path, samples: list[dict]) -> dict:
    return {"schema_version": 1, "root": str(root), "samples": samples}


def _semantic(targets: list[dict]) -> dict:
    return {"schema_version": 1, "targets": targets}


def _fake_success_runner(payload: dict):
    def run(**kwargs):  # noqa: ANN003
        out = Path(kwargs["artifacts_dir"]) / f"{kwargs['file_path'].stem}_ida_evidence.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload), encoding="utf-8")
        return ToolRunArtifact(
            tool_name="IDA",
            enabled=True,
            attempted=True,
            success=True,
            output_path=str(out),
            summary="ok",
        )

    return run


def test_selects_only_in_scope_needs_symbolic_targets(tmp_path: Path) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"MZ")
    selected = _sample(exe, tmp_path, sample_id="4c69f173f2bd0211")
    solved = _sample(exe, tmp_path, sample_id="bcbd9979db015bfd")
    wrong_missing = _sample(exe, tmp_path, sample_id="18019fca52b389fe")
    out_of_scope = _sample(exe, tmp_path, sample_id="not_in_scope")

    result = ida_summary.run_local_reverse_ida_summary(
        corpus_index=_corpus(tmp_path, [selected, solved, wrong_missing, out_of_scope]),
        semantic_result=_semantic([
            _target(selected),
            _target(solved, solved=True),
            _target(wrong_missing, missing_evidence="other"),
            _target(out_of_scope),
        ]),
        policy=_policy(tmp_path),
        artifacts_dir=tmp_path / "artifacts",
        ida_runner=_fake_success_runner({"strings": [], "hexrays_available": False}),
    )

    assert result["target_count"] == 1
    assert result["targets"][0]["sample_id"] == "4c69f173f2bd0211"


def test_path_escape_and_sha_mismatch_block_ida(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside_ida_escape.exe"
    outside.write_bytes(b"outside")
    mismatch = tmp_path / "mismatch.exe"
    mismatch.write_bytes(b"mismatch")
    calls = []
    try:
        escaped_sample = {
            "sample_id": "4c69f173f2bd0211",
            "relative_path": "../outside_ida_escape.exe",
            "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
        }
        mismatch_sample = _sample(mismatch, tmp_path, sample_id="bcbd9979db015bfd")
        mismatch_sample["sha256"] = "0" * 64

        def runner(**kwargs):  # noqa: ANN003
            calls.append(kwargs)
            return ToolRunArtifact("IDA", True, True, True)

        result = ida_summary.run_local_reverse_ida_summary(
            corpus_index=_corpus(tmp_path, [escaped_sample, mismatch_sample]),
            semantic_result=_semantic([_target(escaped_sample), _target(mismatch_sample)]),
            policy=_policy(tmp_path),
            artifacts_dir=tmp_path / "artifacts",
            ida_runner=runner,
        )

        assert result["status"] == "BLOCKED"
        assert calls == []
        reasons = {reason for target in result["targets"] for reason in target["blocked_reasons"]}
        assert {"PATH_OUTSIDE_ROOT", "SHA256_MISMATCH"} <= reasons
    finally:
        outside.unlink(missing_ok=True)


def test_ida_unavailable_outputs_blocked_without_success(tmp_path: Path) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"MZ")
    sample = _sample(exe, tmp_path)

    def runner(**kwargs):  # noqa: ANN003
        return ToolRunArtifact(
            tool_name="IDA",
            enabled=True,
            attempted=False,
            success=False,
            error="未找到 IDA 可执行文件",
            summary="IDA 自动分析未执行。",
        )

    result = ida_summary.run_local_reverse_ida_summary(
        corpus_index=_corpus(tmp_path, [sample]),
        semantic_result=_semantic([_target(sample)]),
        policy=_policy(tmp_path),
        artifacts_dir=tmp_path / "artifacts",
        ida_runner=runner,
    )

    assert result["status"] == "BLOCKED"
    assert result["ida_available"] is False
    assert result["targets"][0]["ida_status"] == "blocked"
    assert result["targets"][0]["blocked_reasons"] == ["BLOCKED_BY_IDA_UNAVAILABLE"]


def test_fake_ida_output_becomes_bounded_summary(tmp_path: Path) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"MZ")
    sample = _sample(exe, tmp_path)
    payload = {
        "strings": ["flag{"],
        "compare_contexts": [{"call_ea": "0x401000", "callee": "strcmp", "nearby": "push aFlag"}],
        "local_check_contexts": [{"call_ea": "0x401020", "ref_strings": "correct"}],
        "string_xrefs": [{"string": "correct", "xref_ea": "0x401030"}],
        "validation_function_candidates": [{"function": "sub_401000", "score": "12"}],
        "hexrays_available": True,
        "decompiler_snippets": [{"function": "sub_401000", "text": "int check(){return 1;}"}],
        "solver_hints": [{"kind": "direct_strcmp"}],
    }

    result = ida_summary.run_local_reverse_ida_summary(
        corpus_index=_corpus(tmp_path, [sample]),
        semantic_result=_semantic([_target(sample)]),
        policy=_policy(tmp_path),
        artifacts_dir=tmp_path / "artifacts",
        ida_runner=_fake_success_runner(payload),
    )
    target = result["targets"][0]

    assert result["status"] == "SUCCESS"
    assert result["hexrays_available_any"] is True
    assert target["ida_status"] == "success"
    assert target["strings_summary"] == ["flag{"]
    assert target["compare_contexts_summary"][0]["callee"] == "strcmp"
    assert target["validation_function_candidates"][0]["function"] == "sub_401000"
    assert target["next_action"] == "ida_summary_guided_solver_v1"


def test_hexrays_unavailable_keeps_empty_decompiler_snippets(tmp_path: Path) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"MZ")
    sample = _sample(exe, tmp_path)

    result = ida_summary.run_local_reverse_ida_summary(
        corpus_index=_corpus(tmp_path, [sample]),
        semantic_result=_semantic([_target(sample)]),
        policy=_policy(tmp_path),
        artifacts_dir=tmp_path / "artifacts",
        ida_runner=_fake_success_runner({"hexrays_available": False, "decompiler_snippets": []}),
    )
    target = result["targets"][0]

    assert target["hexrays_available"] is False
    assert target["decompiler_snippets"] == []


def test_summary_limits_large_ida_output(tmp_path: Path) -> None:
    exe = tmp_path / "demo.exe"
    exe.write_bytes(b"MZ")
    sample = _sample(exe, tmp_path)
    payload = {
        "strings": [f"s{i}" for i in range(100)],
        "decompiler_snippets": [{"function": "f", "text": "x" * 5000}],
    }

    result = ida_summary.run_local_reverse_ida_summary(
        corpus_index=_corpus(tmp_path, [sample]),
        semantic_result=_semantic([_target(sample)]),
        policy=_policy(tmp_path),
        artifacts_dir=tmp_path / "artifacts",
        ida_runner=_fake_success_runner(payload),
    )
    target = result["targets"][0]

    assert len(target["strings_summary"]) == 20
    assert len(target["decompiler_snippets"][0]["text"]) == 900
