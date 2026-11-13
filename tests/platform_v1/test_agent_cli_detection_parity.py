"""The host's CLI detector and dev-up.ps1's Find-Executable are one rule (#1458)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from reverse_agent.agent_cli_detection import AGENT_CLI_COMMANDS, detect_agent_clis

ROOT = Path(__file__).resolve().parents[2]
DEV_UP = ROOT / "dev-up.ps1"

requires_windows_powershell = pytest.mark.skipif(
    sys.platform != "win32" or shutil.which("powershell") is None,
    reason="requires Windows powershell",
)


def _launcher_lookup(path: str, pathext: str, cwd: Path) -> dict[str, str]:
    """Run only dev-up.ps1's Find-Executable, with an isolated PATH, PATHEXT and cwd."""
    source = str(DEV_UP).replace("'", "''")
    commands = ",".join("'%s'" % command for command in AGENT_CLI_COMMANDS.values())
    script = rf"""
$ErrorActionPreference = 'Stop'
$errors = $null; $tokens = $null
$tree = [System.Management.Automation.Language.Parser]::ParseFile('{source}', [ref]$tokens, [ref]$errors)
if ($errors.Count) {{ throw 'launcher parse failed' }}
$function = @($tree.FindAll({{ param($n)
  $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Find-Executable'
}}, $true))
if ($function.Count -ne 1) {{ throw 'expected one Find-Executable' }}
. ([scriptblock]::Create($function[0].Extent.Text))
# Keep the Get-Command fallback out of the comparison: it would see the real machine.
function Get-Command {{ return $null }}
$env:PATH = '{path.replace("'", "''")}'
$env:PATHEXT = '{pathext}'
Set-Location -LiteralPath '{str(cwd).replace("'", "''")}'
$found = [ordered]@{{}}
foreach ($command in @({commands})) {{
  $hit = Find-Executable $command
  if ($hit) {{ $found[$command] = $hit }}
}}
ConvertTo-Json -Compress $found
"""
    result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                            capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    raw = json.loads(result.stdout.strip() or "{}")
    by_command = {command: executor for executor, command in AGENT_CLI_COMMANDS.items()}
    return {by_command[command]: value for command, value in raw.items()}


@requires_windows_powershell
@pytest.mark.parametrize("layout", [
    {},
    {"first": ["codex.cmd"]},
    {"first": ["opencode.CMD", "opencode"], "second": ["opencode.exe"]},
    {"first": ["claude.ps1"], "second": ["claude.exe", "codex.exe"], "cwd": ["opencode.bat"]},
    {"second": ["codex.com"], "cwd": ["codex.cmd", "claude"]},
])
def test_host_detector_matches_launcher_find_executable(tmp_path, layout):
    dirs = {name: tmp_path / name for name in ("first", "second", "cwd")}
    for name, directory in dirs.items():
        directory.mkdir()
        for file_name in layout.get(name, ()):
            (directory / file_name).write_text("", encoding="utf-8")
    path = f"{dirs['first']};{dirs['second']}"
    pathext = ".COM;.EXE;.BAT;.CMD"
    launcher = _launcher_lookup(path, pathext, dirs["cwd"])
    host = detect_agent_clis(path=path, pathext=pathext, windows=True, cwd=dirs["cwd"])
    assert {k: Path(v).resolve() for k, v in host.items()} == {k: Path(v).resolve() for k, v in launcher.items()}
