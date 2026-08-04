"""Absolute isolated launcher for credential-bearing Platform V1 acceptance.

This file intentionally imports only standard-library modules until the
trusted source tree, exact revision, candidate separation, environment, and
import path have been validated.
"""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


_SHA1 = re.compile(r"[0-9a-f]{40}")
_DANGEROUS_EXACT = {
    "PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP", "PYTHONUSERBASE",
    "PYTHONINSPECT", "PYTHONBREAKPOINT", "GIT_DIR", "GIT_WORK_TREE",
    "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_REPLACE_REF_BASE", "GIT_EXTERNAL_DIFF", "GIT_DIFF_OPTS",
    "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES", "GIT_CONFIG",
}
_DANGEROUS_PREFIXES = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
_CRITICAL_MODULES = (
    "reverse_agent",
    "reverse_agent.platform_v1.cli",
    "reverse_agent.platform_v1.authority_adapter",
    "reverse_agent.platform_v1.evidence_adapter",
    "reverse_agent.platform_v1.github_adapter",
    "reverse_agent.platform_v1.contracts",
    "reverse_agent.platform_v1.acceptance",
    "reverse_agent.github_remote_verifier",
    "reverse_agent.github_workflow_identity",
)


def _fail(code: str, detail: str = "") -> int:
    print(json.dumps({"status": code, "detail": detail}, sort_keys=True))
    return 60


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _sanitized_environment() -> dict[str, str]:
    clean = {
        key: value for key, value in os.environ.items()
        if key not in _DANGEROUS_EXACT
        and not any(key.startswith(prefix) for prefix in _DANGEROUS_PREFIXES)
    }
    clean["GIT_NO_REPLACE_OBJECTS"] = "1"
    clean["GIT_CONFIG_NOSYSTEM"] = "1"
    clean["GIT_CONFIG_GLOBAL"] = os.devnull
    clean["GIT_CONFIG_SYSTEM"] = os.devnull
    clean["PYTHONNOUSERSITE"] = "1"
    return clean


def _git(root: Path, *args: str, env: dict[str, str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True,
        timeout=30, env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git_{args[0]}_failed:exit={result.returncode}")
    return result.stdout.strip()


def _resolve_entry(value: str) -> Path | None:
    if not value:
        return None
    try:
        return Path(value).resolve(strict=False)
    except (OSError, RuntimeError):
        return None


def main() -> int:
    if not sys.flags.isolated or not sys.flags.safe_path:
        return _fail("TRUSTED_LAUNCHER_REQUIRED", "python_-I_-P_required")
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError) as exc:
        return _fail("TRUSTED_LAUNCHER_INPUT_ERROR", str(exc))
    if not isinstance(payload, dict):
        return _fail("TRUSTED_LAUNCHER_INPUT_ERROR", "object_required")

    candidate_value = payload.get("candidate_repository_root")
    revision = payload.get("expected_trusted_revision")
    if not isinstance(candidate_value, str) or not candidate_value:
        return _fail("TRUSTED_LAUNCHER_INPUT_ERROR", "candidate_root_required")
    if not isinstance(revision, str) or not _SHA1.fullmatch(revision):
        return _fail("TRUSTED_LAUNCHER_INPUT_ERROR", "trusted_revision_required")
    try:
        launcher = Path(__file__).resolve(strict=True)
        trusted = launcher.parents[2]
        candidate = Path(candidate_value).resolve(strict=True)
        cwd = Path.cwd().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        return _fail("TRUSTED_LAUNCHER_ROOT_ERROR", str(exc))
    if not trusted.is_dir() or not candidate.is_dir():
        return _fail("TRUSTED_LAUNCHER_ROOT_ERROR", "directory_required")
    if trusted == candidate or _inside(trusted, candidate) or _inside(candidate, trusted):
        return _fail("TRUSTED_LAUNCHER_ROOT_ERROR", "trusted_candidate_equal_or_nested")
    if _inside(cwd, candidate):
        return _fail("TRUSTED_LAUNCHER_ROOT_ERROR", "cwd_inside_candidate")
    for entry in sys.path:
        resolved = _resolve_entry(entry)
        if resolved is not None and _inside(resolved, candidate):
            return _fail("TRUSTED_LAUNCHER_PATH_ERROR", f"candidate_sys_path:{resolved}")

    clean_env = _sanitized_environment()
    try:
        if Path(_git(trusted, "rev-parse", "--show-toplevel", env=clean_env)).resolve() != trusted:
            raise RuntimeError("trusted_git_root_mismatch")
        if _git(trusted, "rev-parse", "HEAD", env=clean_env) != revision:
            raise RuntimeError("trusted_revision_mismatch")
        dirty = _git(
            trusted, "status", "--porcelain=v1", "--untracked-files=no", "--",
            "reverse_agent", env=clean_env,
        )
        if dirty:
            raise RuntimeError("trusted_verifier_tracked_files_dirty")
        if Path(_git(candidate, "rev-parse", "--show-toplevel", env=clean_env)).resolve() != candidate:
            raise RuntimeError("candidate_git_root_mismatch")
    except RuntimeError as exc:
        return _fail("TRUSTED_LAUNCHER_GIT_ERROR", str(exc))

    for key in list(os.environ):
        if key in _DANGEROUS_EXACT or any(
            key.startswith(prefix) for prefix in _DANGEROUS_PREFIXES
        ):
            os.environ.pop(key, None)
    os.environ.update({
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "PYTHONNOUSERSITE": "1",
    })
    sys.path.insert(0, str(trusted))

    runtime = importlib.import_module("reverse_agent.platform_v1.trusted_runtime")
    runtime.activate_from_isolated_launcher(
        trusted_verifier_root=str(trusted),
        candidate_repository_root=str(candidate),
        trusted_revision=revision,
    )
    module_origins: dict[str, str] = {}
    for name in _CRITICAL_MODULES:
        module = importlib.import_module(name)
        module_file = getattr(module, "__file__", None)
        if not isinstance(module_file, str):
            return _fail("TRUSTED_LAUNCHER_MODULE_ERROR", f"missing_file:{name}")
        resolved = Path(module_file).resolve(strict=True)
        if not _inside(resolved, trusted):
            return _fail("TRUSTED_LAUNCHER_MODULE_ERROR", f"outside_trusted:{name}")
        module_origins[name] = str(resolved)
    for entry in sys.path:
        resolved = _resolve_entry(entry)
        if resolved is not None and _inside(resolved, candidate):
            return _fail("TRUSTED_LAUNCHER_PATH_ERROR", f"candidate_sys_path:{resolved}")

    if payload.get("launcher_probe_only") is True:
        print(json.dumps({
            "status": "TRUSTED_LAUNCHER_READY",
            "candidate_absent_from_sys_path": True,
            "critical_module_origins": module_origins,
        }, sort_keys=True))
        return 0
    import io
    cli = sys.modules["reverse_agent.platform_v1.cli"]
    payload["trusted_verifier_root"] = str(trusted)
    payload["candidate_repository_root"] = str(candidate)
    payload["expected_trusted_revision"] = revision
    sys.stdin = io.StringIO(json.dumps(payload))
    return int(cli.main(["evaluate-live-acceptance"]))


if __name__ == "__main__":
    raise SystemExit(main())
