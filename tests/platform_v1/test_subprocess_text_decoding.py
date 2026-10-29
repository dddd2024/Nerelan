from __future__ import annotations

import ast
import sys
from pathlib import Path

import reverse_agent.control_plane
import reverse_agent.platform_v1
from reverse_agent.platform_v1.repository_preparation import _run_git

REPLACEMENT = "\ufffd"
CHILD_BYTES = "import sys; sys.stdout.buffer.write(b'\\xd0\\xd0\\xb2\\xe2'); sys.stdout.buffer.flush()"


def test_run_git_survives_non_utf8_child_output(tmp_path: Path) -> None:
    completed = _run_git(
        [sys.executable, "-c", CHILD_BYTES],
        cwd=tmp_path,
        timeout=30,
    )

    assert completed.returncode == 0
    assert completed.stdout is not None
    assert REPLACEMENT in completed.stdout
    assert "\u0432" in completed.stdout
    assert completed.stdout == REPLACEMENT + "\u0432" + REPLACEMENT


def test_text_mode_subprocess_calls_declare_decode_errors() -> None:
    package_dirs = [
        Path(reverse_agent.platform_v1.__file__).parent,
        Path(reverse_agent.control_plane.__file__).parent,
    ]
    violations: list[str] = []

    for source_file in sorted(path for package_dir in package_dirs for path in package_dir.glob("*.py")):
        module = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(module):
            if not isinstance(node, ast.Call):
                continue
            keywords = {kw.arg: kw.value for kw in node.keywords if kw.arg is not None}
            text_mode = any(
                isinstance(keywords.get(name), ast.Constant) and keywords[name].value is True
                for name in ("text", "universal_newlines")
            )
            if text_mode and "errors" not in keywords:
                violations.append(f"{source_file.parent.name}/{source_file.name}:{node.lineno}")

    assert violations == [], (
        "text-mode subprocess calls missing errors= at " + ", ".join(violations)
    )


def test_where_exe_paths_use_the_console_code_page(tmp_path: Path, monkeypatch) -> None:
    import subprocess
    from types import SimpleNamespace
    from reverse_agent.platform_v1 import opencode_executor

    install = tmp_path / "测试" / "opencode.exe"
    install.parent.mkdir()
    install.write_bytes(b"")
    seen = []

    def fake_run(argv, **kwargs):
        seen.append(kwargs.get("encoding"))
        missing = str(tmp_path / "missing" / "opencode.exe")
        return SimpleNamespace(returncode=0, stdout=f"{missing}\n{install}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    # A listed path that does not exist is skipped; the real non-ASCII path is returned.
    assert opencode_executor._resolve_windows_exe() == str(install)
    assert seen and set(seen) == {opencode_executor._where_encoding()}


def test_where_exe_follows_the_active_console_code_page(monkeypatch) -> None:
    import ctypes
    import os
    from types import SimpleNamespace
    from reverse_agent.platform_v1 import opencode_executor

    if os.name != "nt":
        assert opencode_executor._where_encoding() == "utf-8"
        return
    kernel = SimpleNamespace(GetConsoleOutputCP=lambda: 65001)
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(kernel32=kernel))
    assert opencode_executor._where_encoding() == "utf-8"  # after chcp 65001
    kernel.GetConsoleOutputCP = lambda: 0  # no console: the system OEM code page
    assert opencode_executor._where_encoding() == "oem"
