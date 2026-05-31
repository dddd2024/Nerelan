import hashlib
import json
from pathlib import Path

import pytest

from reverse_agent.harness import load_harness_cases
from reverse_agent.local_samples import add_sample, main, sanitize_case_id, solve_sample


def _fake_sample(tmp_path: Path, name: str = "Crack Me!.EXE", content: bytes = b"fake-pe") -> Path:
    sample = tmp_path / name
    sample.write_bytes(content)
    return sample


def test_add_sample_writes_case_metadata_and_notes(tmp_path: Path) -> None:
    sample = _fake_sample(tmp_path)
    samples_dir = tmp_path / "samples"

    result = add_sample(sample, samples_dir=samples_dir)

    case_dir = samples_dir / result["case_id"]
    assert (case_dir / "sample.exe").read_bytes() == b"fake-pe"
    assert (case_dir / "case.json").exists()
    assert (case_dir / "metadata.json").exists()
    assert (case_dir / "notes.md").exists()

    case_payload = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    assert case_payload["cases"][0]["case_id"] == result["case_id"]
    assert case_payload["cases"][0]["tags"] == ["local", "reverse", "auto_imported"]
    assert case_payload["cases"][0]["input_value"].endswith("/sample.exe")


def test_generated_case_id_is_stable_and_safe(tmp_path: Path) -> None:
    sample = _fake_sample(tmp_path, content=b"same")
    digest = hashlib.sha256(b"same").hexdigest()

    result = add_sample(sample, samples_dir=tmp_path / "samples")

    assert result["case_id"] == f"crack_me_{digest[:8]}"


def test_explicit_case_id_is_sanitized(tmp_path: Path) -> None:
    sample = _fake_sample(tmp_path)

    result = add_sample(sample, samples_dir=tmp_path / "samples", case_id=" RC4 Crackme 001 ")

    assert result["case_id"] == "rc4_crackme_001"
    assert sanitize_case_id(" RC4 Crackme 001 ") == "rc4_crackme_001"


def test_add_sample_rejects_existing_case_id(tmp_path: Path) -> None:
    sample = _fake_sample(tmp_path)
    samples_dir = tmp_path / "samples"

    add_sample(sample, samples_dir=samples_dir, case_id="demo")

    with pytest.raises(ValueError, match="case_id already exists"):
        add_sample(sample, samples_dir=samples_dir, case_id="demo")


def test_generated_case_json_loads_with_harness(tmp_path: Path) -> None:
    sample = _fake_sample(tmp_path)
    samples_dir = tmp_path / "samples"
    result = add_sample(sample, samples_dir=samples_dir, case_id="demo")

    cases = load_harness_cases(Path(result["case_json"]))

    assert len(cases) == 1
    assert cases[0].case_id == "demo"
    assert cases[0].category == "unknown"


def test_metadata_contains_file_facts(tmp_path: Path) -> None:
    sample = _fake_sample(tmp_path, content=b"abc")
    samples_dir = tmp_path / "samples"
    result = add_sample(sample, samples_dir=samples_dir, case_id="demo")

    metadata = json.loads(Path(result["metadata_json"]).read_text(encoding="utf-8"))

    assert metadata["case_id"] == "demo"
    assert metadata["sha256"] == hashlib.sha256(b"abc").hexdigest()
    assert metadata["size_bytes"] == 3
    assert metadata["original_path"] == str(sample.resolve())
    assert metadata["stored_sample_path"].endswith("/demo/sample.exe")


def test_solve_sample_writes_codex_task(tmp_path: Path) -> None:
    sample = _fake_sample(tmp_path)
    samples_dir = tmp_path / "samples"
    add_sample(sample, samples_dir=samples_dir, case_id="demo")

    result = solve_sample("demo", samples_dir=samples_dir)

    task = Path(result["codex_task"]).read_text(encoding="utf-8")
    assert "Local Reverse Sample Task: demo" in task
    assert "solver.py" in task
    assert "Do not run IDA, OllyDbg, Frida" in task
    assert "Do not commit `local_reverse_samples/` contents" in task


def test_solve_sample_rejects_missing_case(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="case_id not found"):
        solve_sample("missing", samples_dir=tmp_path / "samples")


def test_run_static_harness_uses_monkeypatched_entry(tmp_path: Path, monkeypatch) -> None:
    sample = _fake_sample(tmp_path)
    samples_dir = tmp_path / "samples"
    add_sample(sample, samples_dir=samples_dir, case_id="demo")
    calls = []

    def fake_harness_main(argv):  # noqa: ANN001
        calls.append(argv)
        return 0

    monkeypatch.setattr("reverse_agent.harness.main", fake_harness_main)

    result = solve_sample("demo", samples_dir=samples_dir, run_static_harness=True)

    assert Path(result["codex_task"]).exists()
    assert calls
    assert "--analysis-mode" in calls[0]
    assert "Static Analysis" in calls[0]
    assert "--tool-enabled" not in calls[0]
    assert "--ida-enabled" not in calls[0]
    assert "--olly-enabled" not in calls[0]
    assert "--runtime-validation-enabled" not in calls[0]


def test_main_returns_success_for_add_and_solve(tmp_path: Path) -> None:
    sample = _fake_sample(tmp_path)
    samples_dir = tmp_path / "samples"

    assert main(["add", str(sample), "--case-id", "demo", "--samples-dir", str(samples_dir)]) == 0
    assert main(["solve", "demo", "--samples-dir", str(samples_dir)]) == 0
