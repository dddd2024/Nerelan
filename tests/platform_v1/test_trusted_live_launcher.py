"""Real-process tests for the isolated trusted live launcher."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def _trees(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    trusted = tmp_path / "trusted"
    candidate = tmp_path / "candidate"
    hostile = tmp_path / "hostile"
    shutil.copytree(REPO_ROOT / "reverse_agent", trusted / "reverse_agent")
    candidate.mkdir()
    hostile.mkdir()
    for root in (trusted, candidate):
        _git(root, "init", "-q")
        _git(root, "config", "user.email", "test@example.invalid")
        _git(root, "config", "user.name", "Test")
    _git(trusted, "add", "reverse_agent")
    _git(trusted, "commit", "-q", "-m", "trusted")
    (candidate / "README").write_text("candidate", encoding="utf-8")
    _git(candidate, "add", "README")
    _git(candidate, "commit", "-q", "-m", "candidate")
    return trusted, candidate, hostile, _git(trusted, "rev-parse", "HEAD")


def _invoke(
    trusted: Path, candidate: Path, revision: str, cwd: Path,
    *, isolated: bool = True, env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    launcher = trusted / "reverse_agent" / "platform_v1" / "trusted_live_launcher.py"
    argv = [sys.executable]
    if isolated:
        argv.extend(["-I", "-P"])
    argv.append(str(launcher.resolve()))
    payload = {
        "trusted_verifier_root": str(trusted.resolve()),
        "candidate_repository_root": str(candidate.resolve()),
        "expected_trusted_revision": revision,
        "launcher_probe_only": True,
    }
    return subprocess.run(
        argv, cwd=cwd, input=json.dumps(payload), text=True,
        capture_output=True, timeout=60, env=env,
    )


def test_isolated_launcher_ignores_hostile_shadow_modules_and_pythonpath(tmp_path: Path) -> None:
    trusted, candidate, hostile, revision = _trees(tmp_path)
    marker = tmp_path / "executed"
    poison = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
    for name in ("sitecustomize.py", "json.py", "typing.py", "pathlib.py"):
        (candidate / name).write_text(poison, encoding="utf-8")
    package = candidate / "reverse_agent"
    package.mkdir()
    (package / "__init__.py").write_text(poison, encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(candidate)
    result = _invoke(trusted, candidate, revision, hostile, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    observed = json.loads(result.stdout)
    assert observed["status"] == "TRUSTED_LAUNCHER_READY"
    assert observed["candidate_absent_from_sys_path"] is True
    trusted_resolved = trusted.resolve()
    assert observed["critical_module_origins"]
    for module_file in observed["critical_module_origins"].values():
        assert trusted_resolved in Path(module_file).resolve().parents
    assert not marker.exists()


def test_candidate_cwd_is_rejected_before_candidate_code_can_run(tmp_path: Path) -> None:
    trusted, candidate, _, revision = _trees(tmp_path)
    result = _invoke(trusted, candidate, revision, candidate)
    assert result.returncode == 60
    assert json.loads(result.stdout)["status"] == "TRUSTED_LAUNCHER_ROOT_ERROR"


def test_non_isolated_launcher_is_rejected(tmp_path: Path) -> None:
    trusted, candidate, hostile, revision = _trees(tmp_path)
    result = _invoke(trusted, candidate, revision, hostile, isolated=False)
    assert result.returncode == 60
    assert json.loads(result.stdout)["status"] == "TRUSTED_LAUNCHER_REQUIRED"


def test_ordinary_module_cli_live_route_is_rejected_before_operations() -> None:
    result = subprocess.run(
        [
            sys.executable, "-m", "reverse_agent.platform_v1.cli",
            "evaluate-live-acceptance",
        ],
        cwd=REPO_ROOT, input="{}", text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 60
    assert json.loads(result.stdout)["status"] == "TRUSTED_LAUNCHER_REQUIRED"


def test_same_trusted_and_candidate_root_is_rejected(tmp_path: Path) -> None:
    trusted, _, hostile, revision = _trees(tmp_path)
    result = _invoke(trusted, trusted, revision, hostile)
    assert result.returncode == 60
    assert "trusted_candidate_equal_or_nested" in result.stdout


def test_nested_candidate_root_is_rejected(tmp_path: Path) -> None:
    trusted, _, hostile, revision = _trees(tmp_path)
    nested = trusted / "candidate"
    nested.mkdir()
    result = _invoke(trusted, nested, revision, hostile)
    assert result.returncode == 60
    assert "trusted_candidate_equal_or_nested" in result.stdout


def test_wrong_trusted_revision_is_rejected(tmp_path: Path) -> None:
    trusted, candidate, hostile, _ = _trees(tmp_path)
    result = _invoke(trusted, candidate, "a" * 40, hostile)
    assert result.returncode == 60
    assert "trusted_revision_mismatch" in result.stdout


def test_dirty_tracked_trusted_verifier_is_rejected(tmp_path: Path) -> None:
    trusted, candidate, hostile, revision = _trees(tmp_path)
    launcher = trusted / "reverse_agent" / "platform_v1" / "trusted_live_launcher.py"
    launcher.write_text(launcher.read_text(encoding="utf-8") + "\n# dirty\n", encoding="utf-8")
    result = _invoke(trusted, candidate, revision, hostile)
    assert result.returncode == 60
    assert "trusted_verifier_tracked_files_dirty" in result.stdout
