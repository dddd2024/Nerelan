from __future__ import annotations

import ast
import sys
from pathlib import Path

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
    package_dir = Path(reverse_agent.platform_v1.__file__).parent
    violations: list[str] = []

    for source_file in sorted(package_dir.glob("*.py")):
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
                violations.append(f"{source_file.name}:{node.lineno}")

    assert violations == [], (
        "text-mode subprocess calls missing errors= at " + ", ".join(violations)
    )
