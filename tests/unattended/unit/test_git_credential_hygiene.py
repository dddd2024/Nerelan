from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).parents[3]
    / ".github"
    / "scripts"
    / "git_credential_hygiene.py"
)
_SECRET = "ghp_FORBIDDEN_SYNTHETIC_VALUE"


def _run(
    tmp_path: Path,
    *,
    global_config: str | None = None,
    included_config: str | None = None,
    local_entries: tuple[tuple[str, str], ...] = (),
) -> subprocess.CompletedProcess[str]:
    repository = tmp_path / "repo"
    repository.mkdir()
    subprocess.run(
        ("git", "init", "--quiet"),
        cwd=repository,
        check=True,
        capture_output=True,
    )
    system = tmp_path / "missing-system-config"
    global_path = tmp_path / "missing-global-config"
    if global_config is not None:
        global_path.write_text(global_config, encoding="utf-8")
    if included_config is not None:
        included = tmp_path / "included.gitconfig"
        included.write_text(included_config, encoding="utf-8")
        with global_path.open("a", encoding="utf-8") as stream:
            stream.write(f"\n[include]\n\tpath = {included.as_posix()}\n")
    for key, value in local_entries:
        subprocess.run(
            ("git", "config", "--local", key, value),
            cwd=repository,
            check=True,
            capture_output=True,
        )
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_SYSTEM": str(system),
            "GIT_CONFIG_GLOBAL": str(global_path),
            "HOME": str(tmp_path / "home"),
            "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
        }
    )
    return subprocess.run(
        (sys.executable, str(_SCRIPT)),
        cwd=repository,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def _assert_redacted_failure(
    completed: subprocess.CompletedProcess[str], category: str
) -> None:
    assert completed.returncode == 1
    assert category in completed.stdout
    assert _SECRET not in completed.stdout
    assert _SECRET not in completed.stderr


def test_absent_optional_global_and_system_configs_pass(tmp_path: Path) -> None:
    completed = _run(tmp_path)
    assert completed.returncode == 0
    assert completed.stdout.strip() == "credential_hygiene=PASS"


def test_safe_included_config_is_part_of_effective_read(tmp_path: Path) -> None:
    completed = _run(
        tmp_path,
        global_config="[user]\n\tname = synthetic\n",
        included_config="[diff]\n\trenames = true\n",
    )
    assert completed.returncode == 0


def test_included_extra_header_fails_without_value_disclosure(
    tmp_path: Path,
) -> None:
    completed = _run(
        tmp_path,
        global_config="",
        included_config=(
            '[http "https://github.com/"]\n'
            f"\textraHeader = Authorization: Bearer {_SECRET}\n"
        ),
    )
    _assert_redacted_failure(completed, "authorization_extraheader")


@pytest.mark.parametrize(
    ("key", "value", "category"),
    (
        ("credential.helper", "store", "credential_helper"),
        (
            "remote.origin.url",
            f"https://x-access-token:{_SECRET}@github.com/o/r.git",
            "token_bearing_remote",
        ),
        (
            f"url.https://x-access-token:{_SECRET}@github.com/.insteadOf",
            "https://github.com/",
            "credential_bearing_insteadof",
        ),
        ("core.sshCommand", "ssh -i synthetic-key", "ssh_command"),
    ),
)
def test_unsafe_effective_entries_fail_redacted(
    tmp_path: Path, key: str, value: str, category: str
) -> None:
    completed = _run(tmp_path, local_entries=((key, value),))
    _assert_redacted_failure(completed, category)


def test_existing_malformed_global_config_fails_closed(tmp_path: Path) -> None:
    completed = _run(tmp_path, global_config="[broken")
    _assert_redacted_failure(completed, "effective_config_unreadable")
