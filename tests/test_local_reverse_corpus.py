import hashlib
import json
from pathlib import Path

from reverse_agent.local_reverse_corpus import (
    build_training_state,
    main,
    scan_corpus,
)


def test_missing_root_writes_blocked_state(tmp_path: Path) -> None:
    out_path = tmp_path / "index.json"
    state_path = tmp_path / "state.json"

    exit_code = main([
        "--root", str(tmp_path / "missing"),
        "--out", str(out_path),
        "--training-state", str(state_path),
    ])

    assert exit_code == 2
    index = json.loads(out_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert index["root_exists"] is False
    assert state["status"] == "BLOCKED"
    assert state["blocked_reason"] == "BLOCKED_BY_LOCAL_PATH_UNAVAILABLE"


def test_empty_root_is_partial_without_crashing(tmp_path: Path) -> None:
    index = scan_corpus(tmp_path)
    state = build_training_state(index)

    assert index["schema_version"] == 1
    assert index["sample_count"] == 0
    assert state["status"] == "PARTIAL"


def test_mz_exe_is_pe_candidate_with_stable_metadata(tmp_path: Path) -> None:
    sample = tmp_path / "mock.exe"
    content = b"MZ" + b"\0" * 126
    sample.write_bytes(content)

    index = scan_corpus(tmp_path)
    record = index["samples"][0]

    assert record["file_kind"] == "pe_candidate"
    assert record["relative_path"] == "mock.exe"
    assert record["extension"] == ".exe"
    assert record["size_bytes"] == len(content)
    assert record["sha256"] == hashlib.sha256(content).hexdigest()
    assert record["sample_id"] == record["sha256"][:16]
    assert record["safe_to_run"] is False
    assert "static_pe_or_executable_candidate" in record["notes"]


def test_filename_and_content_hints_add_triage_tags(tmp_path: Path) -> None:
    (tmp_path / "xor_shift_base64.txt").write_text(
        "try xor then shift, decode base64 and compare password",
        encoding="utf-8",
    )
    (tmp_path / "DES" ).mkdir()
    (tmp_path / "DES" / "rc4_strcmp.c").write_text(
        "int main(){ return strcmp(input, key); } // rc4 des",
        encoding="utf-8",
    )

    index = scan_corpus(tmp_path)
    all_tags = {tag for sample in index["samples"] for tag in sample["triage_tags"]}

    assert {"xor", "shift", "base64", "des", "rc4", "strcmp"} <= all_tags


def test_output_schema_contains_required_fields(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text("print('correct flag input')", encoding="utf-8")

    index = scan_corpus(tmp_path)
    state = build_training_state(index)

    assert {"schema_version", "generated_at", "sample_count", "samples"} <= set(index)
    assert {"schema_version", "generated_at", "training_profile", "status"} <= set(state)
    assert state["status"] == "READY"
    assert state["recommended_next_samples"]


def test_large_file_uses_bounded_probe_for_triage(tmp_path: Path) -> None:
    sample = tmp_path / "large_xor.bin"
    sample.write_bytes(b"x" * 4096 + b"late_base64_marker" + b"y" * 4096)

    index = scan_corpus(tmp_path, max_file_size=1024, max_probe_bytes=32)
    record = index["samples"][0]

    assert record["sha256"] == hashlib.sha256(sample.read_bytes()).hexdigest()
    assert "over_max_file_size_no_full_static_triage" in record["notes"]
    assert "triage_probe_only_large_file" in record["notes"]
    assert "base64" not in record["triage_tags"]
    assert "xor" in record["triage_tags"]
