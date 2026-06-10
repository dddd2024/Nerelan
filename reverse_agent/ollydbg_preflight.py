"""OllyDbg backend preflight check — non-invasive configuration probe.

Does NOT start OllyDbg, attach to any process, or execute the sample.
Only checks whether the OllyDbg backend is configured and reachable.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path


def _olly_script_dir() -> Path:
    return Path(__file__).resolve().parent / "olly_scripts"


def _sample_path() -> Path | None:
    """Return the expected sample path from environment or default location."""
    env = os.environ.get("REVERSE_AGENT_SAMPLE_PATH", "")
    if env:
        p = Path(env)
        if p.exists():
            return p
    # Default location used by harness
    default = Path(__file__).resolve().parents[1] / "samples" / "samplereverse.exe"
    return default if default.exists() else None


def _resolve_ollydbg_exe(p: Path) -> Path | None:
    """Resolve a path to the OllyDbg executable.

    If p is a file, return it only if it exists and its name looks like an
    executable (ends with .exe on Windows). If p is a directory, look for
    ollydbg.exe inside it. Otherwise return None.
    """
    if not p.exists():
        return None
    if p.is_file():
        if p.suffix.lower() == ".exe":
            return p
        return None
    if p.is_dir():
        candidate = p / "ollydbg.exe"
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _ollydbg_exe_path() -> Path | None:
    """Return OllyDbg executable path from environment or common locations."""
    env = os.environ.get("REVERSE_AGENT_OLLYDBG_PATH", "")
    if env:
        p = _resolve_ollydbg_exe(Path(env))
        if p is not None:
            return p
    # Common Windows locations
    candidates = [
        Path(r"C:\Program Files\OllyDbg\ollydbg.exe"),
        Path(r"C:\Program Files (x86)\OllyDbg\ollydbg.exe"),
        Path(r"C:\Tools\OllyDbg\ollydbg.exe"),
        Path.home() / "Tools" / "OllyDbg" / "ollydbg.exe",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return None


def _olly_script_module_available() -> bool:
    """Check if olly.ollyscript (or equivalent) Python module is importable."""
    try:
        spec = importlib.util.find_spec("olly.ollyscript")
        if spec is not None:
            return True
    except (ModuleNotFoundError, ImportError):
        pass
    # Also check for alternative module names used by OllyDbg Python scripting
    for name in ("ollyscript", "OllyScript", "olly"):
        try:
            if importlib.util.find_spec(name) is not None:
                return True
        except (ModuleNotFoundError, ImportError):
            pass
    return False


def _step_audit_script_exists() -> bool:
    """Check if the compare_handoff_post_entry_step_audit.py script exists."""
    script = _olly_script_dir() / "compare_handoff_post_entry_step_audit.py"
    return script.exists()


def run_ollydbg_preflight(
    *,
    sample_path: Path | None = None,
    ollydbg_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, object]:
    """Run non-invasive OllyDbg backend preflight check.

    Returns a compact JSON-serializable dict with configuration status.
    Separates backend readiness (OllyDbg tooling) from runtime readiness
    (sample available for actual probing).
    """
    sample = sample_path or _sample_path()
    ollydbg = ollydbg_path or _ollydbg_exe_path()
    script_dir = _olly_script_dir()

    checks = {
        "ollydbg_executable_found": ollydbg is not None,
        "ollydbg_executable_path": str(ollydbg) if ollydbg else None,
        "olly_script_module_importable": _olly_script_module_available(),
        "olly_scripts_directory_exists": script_dir.exists(),
        "step_audit_script_exists": _step_audit_script_exists(),
        "sample_path_resolvable": sample is not None,
        "sample_path": str(sample) if sample else None,
    }

    # Backend readiness: OllyDbg tooling must be complete
    backend_ready = (
        checks["ollydbg_executable_found"]
        and checks["olly_script_module_importable"]
        and checks["olly_scripts_directory_exists"]
        and checks["step_audit_script_exists"]
    )

    # Runtime readiness: backend + sample must both be available
    runtime_ready = backend_ready and checks["sample_path_resolvable"]

    # Overall ready flag: requires runtime readiness for any actual probing
    ready = runtime_ready

    if backend_ready and not checks["sample_path_resolvable"]:
        recommendation = "preflight_not_configured_user_env_needed"
    elif ready:
        recommendation = "preflight_ready_for_bounded_ollydbg_runtime_decision"
    else:
        recommendation = "preflight_not_configured_user_env_needed"

    result = {
        "preflight_name": "ollydbg_backend_preflight",
        "preflight_version": 2,
        "ready": ready,
        "backend_ready": backend_ready,
        "runtime_ready": runtime_ready,
        "checks": checks,
        "recommendation": recommendation,
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    return result


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OllyDbg backend preflight check")
    parser.add_argument("--sample-path", type=Path, default=None)
    parser.add_argument("--ollydbg-path", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    result = run_ollydbg_preflight(
        sample_path=args.sample_path,
        ollydbg_path=args.ollydbg_path,
        output_path=args.out,
    )

    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
