"""Every platform-runtime subprocess text read must survive non-UTF-8 bytes.

The captured host environment sets PYTHONUTF8=1 / PYTHONIOENCODING=utf-8. UTF-8
mode also changes the *default* decoding of subprocess pipes, so a child that
emits non-UTF-8 bytes -- native Windows tools such as git, cmd, powershell and
the OpenCode CLI on a CP936 machine -- raises UnicodeDecodeError inside Popen's
reader thread. The thread dies, `stdout` comes back as None, and the output the
platform was about to store as evidence is lost (callers then hit
AttributeError on `result.stdout.strip()`).

Both halves matter: the functional half pins the failure mode, the structural
half keeps new call sites from reintroducing it.
"""
from __future__ import annotations

import re
import subprocess
import sys
import threading
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIRS = (
    ROOT / "reverse_agent" / "platform_v1",
    ROOT / "reverse_agent" / "control_plane",
    ROOT / "reverse_agent" / "model_access",
)
CALL = re.compile(r"subprocess\.(run|Popen|check_output|check_call)\(")

# CP936/GBK bytes for a Chinese word, as a native Windows tool would emit them.
NON_UTF8 = bytes([0xD0, 0xD0, 0xB2, 0xE2])


def _call_body(src: str, start: int) -> str:
    i = src.index("(", start)
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "(":
            depth += 1
        elif src[j] == ")":
            depth -= 1
            if depth == 0:
                return src[i + 1 : j]
    raise AssertionError("unbalanced subprocess call")


def _text_mode_calls() -> list[tuple[Path, int, str]]:
    found: list[tuple[Path, int, str]] = []
    for base in RUNTIME_DIRS:
        for path in sorted(base.rglob("*.py")):
            src = path.read_text(encoding="utf-8", errors="replace")
            for match in CALL.finditer(src):
                body = _call_body(src, match.start())
                if "text=True" in body or "universal_newlines=True" in body:
                    found.append((path, src[: match.start()].count("\n") + 1, body))
    return found


def test_every_text_mode_subprocess_call_declares_an_error_handler() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}:{line}"
        for path, line, body in _text_mode_calls()
        if "errors=" not in body
    ]
    assert offenders == [], (
        "text-mode subprocess calls without errors= will raise UnicodeDecodeError "
        "on non-UTF-8 child output (PYTHONUTF8=1 is set by the host environment): "
        + ", ".join(offenders)
    )


def test_the_scan_actually_sees_the_runtime_call_sites() -> None:
    # Guards against the structural test silently passing because the scan broke.
    assert len(_text_mode_calls()) >= 40


@pytest.mark.skipif(
    sys.platform != "win32", reason="CP936/GBK is the Windows ANSI code page"
)
def test_non_utf8_child_output_is_not_silently_dropped() -> None:
    """A non-UTF-8 child must not be mistaken for a silent success.

    The decode failure happens on Popen's reader thread, so nothing propagates
    to the caller: run() returns normally with returncode 0 (the child *did*
    succeed) and stdout None. The platform therefore records a successful
    execution with no evidence at all -- worse than a crash, because nothing
    raises. This test pins that signature, then pins the fix.
    """
    if not sys.flags.utf8_mode:
        # The defect is created by UTF-8 mode overriding the pipe codec; without
        # it Python decodes 0xD0D0 as GBK and no failure occurs at all.
        pytest.skip("PYTHONUTF8=1 is required to reproduce; the host env sets it")

    child = [
        sys.executable,
        "-c",
        f"import sys; sys.stdout.buffer.write({NON_UTF8!r})",
    ]

    # --- the failure mode being guarded against -------------------------------
    thread_failures: list[BaseException] = []
    previous_hook = threading.excepthook
    threading.excepthook = lambda args: thread_failures.append(args.exc_value)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            broken = subprocess.run(child, capture_output=True, text=True, check=False)
    finally:
        threading.excepthook = previous_hook

    assert any(isinstance(e, UnicodeDecodeError) for e in thread_failures), (
        "the reader thread was expected to fail decoding; the defect did not reproduce"
    )
    assert broken.returncode == 0, "the child itself succeeded -- hence the silence"
    assert broken.stdout is None, (
        "this guard is only meaningful while the unfixed call loses output entirely"
    )

    # --- the platform idiom ---------------------------------------------------
    fixed = subprocess.run(
        child, capture_output=True, text=True, errors="replace", check=False
    )
    assert fixed.stdout is not None, "errors= must keep the reader thread alive"
    assert fixed.stdout != ""
    assert "\ufffd" in fixed.stdout


def test_git_call_sites_decode_as_utf8_not_oem() -> None:
    """The 41 repaired sites are overwhelmingly `git`, which emits UTF-8.

    `encoding="oem"` is the established convention for *native console* tools
    (owner/windows-launcher-oem-decoder-r1-v2, PR #719) and is correct for
    where.exe-style probes. Applying it to git would corrupt UTF-8 commit
    messages and paths, so this test records which convention each repaired
    site needs and fails if the mix silently changes.
    """
    native_console: list[str] = []
    for path, line, body in _text_mode_calls():
        if "where.exe" in body:
            native_console.append(f"{path.name}:{line}")

    assert native_console == [
        "opencode_executor.py:590",
        "opencode_executor.py:606",
        "opencode_executor.py:630",
    ], (
        "native-console probes are the only OEM candidates; if a new one appears "
        "it needs encoding=\"oem\", not just errors=: " + ", ".join(native_console)
    )

    git_sites = sum(1 for _, _, body in _text_mode_calls() if '"git"' in body)
    assert git_sites >= 30, (
        "git call sites dominate the repaired set and must stay UTF-8-decoded; "
        f"only {git_sites} found"
    )
