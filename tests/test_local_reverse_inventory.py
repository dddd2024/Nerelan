import hashlib
import json
from pathlib import Path

import pytest

from reverse_agent.harness import load_harness_cases
from reverse_agent.local_reverse_inventory import (
    EXCLUDE_DIRS,
    EXCLUDE_EXTENSIONS,
    LOCAL_REVERSE_ROOT_HINT,
    SAMPLE_EXTENSIONS,
    InventoryError,
    _build_case_payload,
    _build_entry,
    _build_github_entry,
    _build_tags,
    _guess_category,
    _guess_file_type,
    _make_sample_id,
    _should_include_file,
    _walk_files,
    main,
    scan_samples,
)


def _fake_sample(tmp_path: Path, name: str = "sha_256.exe", content: bytes = b"fake-pe") -> Path:
    sample = tmp_path / name
    sample.write_bytes(content)
    return sample


def test_scan_samples_creates_inventory_and_cases(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()
    _fake_sample(root, "sha_256.exe", b"aaa")
    _fake_sample(root, "CPP2.exe", b"bbb")
    (root / "notes.txt").write_text("notes")

    out = tmp_path / "inventory.json"
    github_out = tmp_path / "github_inventory.json"
    cases_dir = tmp_path / "cases"

    result = scan_samples(
        samples_root=root,
        out_path=out,
        github_out_path=github_out,
        cases_dir=cases_dir,
    )

    # All 3 files should be included (.exe, .exe, .txt)
    assert result["scanned"] == 3
    assert out.exists()
    assert github_out.exists()

    inv = json.loads(out.read_text(encoding="utf-8"))
    assert inv["schema_version"] == 1
    assert inv["samples_root_hint"] == LOCAL_REVERSE_ROOT_HINT
    assert "source_root_label" in inv
    assert len(inv["entries"]) == 3

    ginv = json.loads(github_out.read_text(encoding="utf-8"))
    assert ginv["schema_version"] == 1
    assert ginv["samples_root_hint"] == LOCAL_REVERSE_ROOT_HINT
    assert len(ginv["entries"]) == 3

    case_files = list(cases_dir.glob("*.json"))
    assert len(case_files) == 3


def test_scan_samples_excludes_ide_configs(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()
    _fake_sample(root, "valid.exe", b"valid")

    # Create IDE config files that should be excluded
    idea_dir = root / ".idea"
    idea_dir.mkdir()
    (idea_dir / "misc.xml").write_text("<xml/>")
    (idea_dir / ".gitignore").write_text("*.pyc")

    vscode_dir = root / ".vscode"
    vscode_dir.mkdir()
    (vscode_dir / "settings.json").write_text("{}")

    out = tmp_path / "inventory.json"
    result = scan_samples(samples_root=root, out_path=out)

    # Only valid.exe should be included
    assert result["scanned"] == 1
    entry = result["entries"][0]
    assert entry["display_name"] == "valid.exe"


def test_scan_samples_excludes_by_extension(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()
    _fake_sample(root, "valid.exe", b"valid")
    (root / "config.xml").write_text("<xml/>")
    (root / "debug.log").write_text("log")
    (root / "module.iml").write_text("iml")
    (root / "cache.tmp").write_text("tmp")

    out = tmp_path / "inventory.json"
    result = scan_samples(samples_root=root, out_path=out)

    # Only valid.exe should be included
    assert result["scanned"] == 1
    assert result["entries"][0]["display_name"] == "valid.exe"


def test_scan_samples_rejects_missing_root(tmp_path: Path) -> None:
    with pytest.raises(InventoryError, match="does not exist"):
        scan_samples(samples_root=tmp_path / "missing", out_path=tmp_path / "out.json")


def test_entry_fields_correct(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()
    sample = _fake_sample(root, "sha_256.exe", b"content")
    rel = sample.relative_to(root)
    entry = _build_entry(sample, rel, root)

    assert entry["sample_id"].startswith("sha_256_")
    assert entry["display_name"] == "sha_256.exe"
    assert entry["relative_path"] == "sha_256.exe"
    assert entry["sha256"] == hashlib.sha256(b"content").hexdigest()
    assert entry["size_bytes"] == 7
    assert entry["extension"] == ".exe"
    assert entry["guessed_file_type"] == "pe"
    assert entry["category"] == "crypto/hash"
    assert "local" in entry["tags"]
    assert entry["status"] == "indexed"
    assert entry["github_upload_policy"] == "metadata_only"


def test_github_entry_has_no_absolute_path(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()
    sample = _fake_sample(root, "test.exe")
    entry = _build_entry(sample, sample.relative_to(root), root)
    gentry = _build_github_entry(entry)

    assert "samples_root" not in gentry
    assert gentry["relative_path"] == "test.exe"
    assert gentry["sha256"] == entry["sha256"]


def test_sample_id_is_stable(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()
    sample = _fake_sample(root, "my_sample.exe", b"xyz")
    digest = hashlib.sha256(b"xyz").hexdigest()
    rel = sample.relative_to(root)
    sid = _make_sample_id(rel, digest)
    assert sid == f"my_sample_{digest[:8]}"


def test_guess_category_heuristics() -> None:
    assert _guess_category("sha_256.exe") == "crypto/hash"
    assert _guess_category("rc4_crackme.exe") == "crypto/cipher"
    assert _guess_category("CPP2.exe") == "cpp"
    assert _guess_category("mystery.bin") == "unknown"


def test_guess_file_type() -> None:
    assert _guess_file_type("a.exe", ".exe") == "pe"
    assert _guess_file_type("a.bin", ".bin") == "raw"
    assert _guess_file_type("a.unknown", ".unknown") == "unknown"


def test_build_tags() -> None:
    tags = _build_tags("crypto/hash", "pe")
    assert "local" in tags
    assert "reverse" in tags
    assert "crypto_hash" in tags
    assert "pe" in tags


def test_walk_files_recursive(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()
    (root / "a.exe").write_bytes(b"a")
    sub = root / "sub"
    sub.mkdir()
    (sub / "b.dll").write_bytes(b"b")

    files = _walk_files(root)
    assert len(files) == 2
    names = {f.name for f in files}
    assert names == {"a.exe", "b.dll"}


def test_should_include_file_filters_ide_dirs(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()

    valid_file = root / "valid.exe"
    valid_file.write_bytes(b"v")

    idea_file = root / ".idea" / "misc.xml"
    idea_file.parent.mkdir()
    idea_file.write_text("<xml/>")

    assert _should_include_file(valid_file, root) is True
    assert _should_include_file(idea_file, root) is False


def test_should_include_file_filters_excluded_extensions(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()

    valid_file = root / "valid.exe"
    valid_file.write_bytes(b"v")

    xml_file = root / "config.xml"
    xml_file.write_text("<xml/>")

    assert _should_include_file(valid_file, root) is True
    assert _should_include_file(xml_file, root) is False


def test_case_payload_uses_local_reverse_root_placeholder(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()
    sample = _fake_sample(root, "demo.exe", b"demo")
    entry = _build_entry(sample, sample.relative_to(root), root)
    payload = _build_case_payload(entry)

    case_path = tmp_path / "case.json"
    case_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    cases = load_harness_cases(case_path)
    assert len(cases) == 1
    assert cases[0].case_id == entry["sample_id"]
    assert cases[0].category == entry["category"]
    assert cases[0].tags == entry["tags"]
    # Check input_value uses placeholder
    expected_input = f"${{LOCAL_REVERSE_ROOT}}/{entry['relative_path']}"
    assert cases[0].input_value == expected_input


def test_case_payload_input_value_format() -> None:
    entry = {
        "sample_id": "test_12345678",
        "relative_path": "subdir/sample.exe",
        "category": "test",
        "tags": ["local", "reverse"],
    }
    payload = _build_case_payload(entry)

    assert payload["cases"][0]["input_value"] == "${LOCAL_REVERSE_ROOT}/subdir/sample.exe"


def test_main_cli_scan(tmp_path: Path) -> None:
    root = tmp_path / "samples"
    root.mkdir()
    _fake_sample(root, "test.exe", b"t")
    out = tmp_path / "inv.json"
    github_out = tmp_path / "gh.json"
    cases_dir = tmp_path / "cases"

    assert main([
        "scan",
        "--samples-root", str(root),
        "--out", str(out),
        "--github-out", str(github_out),
        "--cases-dir", str(cases_dir),
    ]) == 0

    assert out.exists()
    assert github_out.exists()
    assert list(cases_dir.glob("*.json"))


def test_exclude_constants_defined() -> None:
    # Verify exclusion constants are properly defined
    assert ".idea" in EXCLUDE_DIRS
    assert ".vscode" in EXCLUDE_DIRS
    assert ".git" in EXCLUDE_DIRS
    assert ".xml" in EXCLUDE_EXTENSIONS
    assert ".iml" in EXCLUDE_EXTENSIONS
    assert ".log" in EXCLUDE_EXTENSIONS
    assert ".exe" in SAMPLE_EXTENSIONS
    assert ".dll" in SAMPLE_EXTENSIONS
    assert ".bin" in SAMPLE_EXTENSIONS
