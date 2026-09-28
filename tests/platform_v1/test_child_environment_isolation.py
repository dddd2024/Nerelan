import pytest
from reverse_agent.platform_v1.opencode_executor import build_role_child_env, build_binding_child_env
from collections.abc import Mapping

class GetOnlyParent(Mapping):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __iter__(self):
        raise AssertionError("Iteration not allowed")

    def __len__(self):
        raise AssertionError("Length not allowed")

    def items(self):
        raise AssertionError("Items not allowed")

def test_child_environment_isolation():
    parent = {
        "PATH": "/a path/bin",
        "HOME": "/home/test",
        "GH_TOKEN": "sentinel-gh",
        "UNKNOWN_FUTURE_SECRET": "sentinel-unknown"
    }
    child = build_role_child_env(parent, None, "planner")
    assert child["PATH"] == "/a path/bin"
    assert child["HOME"] == "/home/test"
    assert "GH_TOKEN" not in child
    assert "UNKNOWN_FUTURE_SECRET" not in child

@pytest.mark.parametrize("role", ["executor", "planner", "coder", "reviewer"])
def test_child_environment_isolation_with_all_roles(role):
    parent = GetOnlyParent({
        "PATH": "/a path/bin",
        "HOME": "/home/test",
        "GH_TOKEN": "sentinel-gh",
        "GITHUB_TOKEN": "sentinel-github",
        "AWS_SECRET_ACCESS_KEY": "sentinel-aws",
        "NPM_TOKEN": "sentinel-npm",
        "PASSWORD": "sentinel-password",
        "UNKNOWN_FUTURE_SECRET": "sentinel-unknown"
    })
    child = build_role_child_env(parent, None, role)
    assert child["PATH"] == "/a path/bin"
    assert child["HOME"] == "/home/test"
    assert "GH_TOKEN" not in child
    assert "GITHUB_TOKEN" not in child
    assert "AWS_SECRET_ACCESS_KEY" not in child
    assert "NPM_TOKEN" not in child
    assert "PASSWORD" not in child
    assert "UNKNOWN_FUTURE_SECRET" not in child

@pytest.mark.parametrize("role", ["executor", "planner", "coder", "reviewer"])
def test_child_environment_isolation_with_all_roles_and_safety_flags(role):
    parent = GetOnlyParent({
        "PATH": "/a path/bin",
        "HOME": "/home/test",
        "OPENCODE_DISABLE_AUTOUPDATE": "false",
        "OPENCODE_DISABLE_MODELS_FETCH": "false",
        "OPENCODE_DISABLE_LSP_DOWNLOAD": "false",
        "OPENCODE_DISABLE_DEFAULT_PLUGINS": "false",
        "OPENCODE_DISABLE_CLAUDE_CODE": "false",
        "OPENCODE_CONFIG_CONTENT": '{"MALICIOUS":true}'
    })
    child = build_role_child_env(parent, None, role)
    assert child["OPENCODE_DISABLE_AUTOUPDATE"] == "true"
    assert child["OPENCODE_DISABLE_MODELS_FETCH"] == "true"
    assert child["OPENCODE_DISABLE_LSP_DOWNLOAD"] == "true"
    assert child["OPENCODE_DISABLE_DEFAULT_PLUGINS"] == "true"
    assert child["OPENCODE_DISABLE_CLAUDE_CODE"] == "true"
    assert all("MALICIOUS" not in value for value in child.values())

@pytest.mark.parametrize("path_value", [None, 42, "", "\n", "\x00", "\x7f"])
def test_direct_env_rejects_invalid_path(path_value):
    parent = {"PATH": path_value}
    child = build_role_child_env(parent, None, "executor")
    assert "PATH" not in child

@pytest.mark.parametrize("parent,drive,ext,mode", [
    ({"SystemDrive": "D:", "SystemRoot": "C:\\Windows", "PATHEXT": ".EXE;.CMD"}, "D:", ".EXE;.CMD", "direct"),
    ({"SystemRoot": "C:\\Windows", "PATHEXT": ".EXE;.CMD"}, "C:", ".EXE;.CMD", "direct"),
    ({"SystemDrive": "BAD", "SystemRoot": "C:\\Windows", "PATHEXT": ".EXE"}, "C:", ".EXE", "direct"),
    ({"SystemRoot": "C:Windows", "PATHEXT": ".EXE"}, None, ".EXE", "direct"),
    ({"SystemRoot": "\\\\server\\share", "PATHEXT": ".EXE"}, None, ".EXE", "direct"),
    ({"SystemRoot": "C:\\Win" + chr(10) + "bad", "PATHEXT": ".EXE"}, None, ".EXE", "direct"),
    ({"SystemRoot": "C:\\Windows", "PATHEXT": None}, "C:", ".COM;.EXE;.BAT;.CMD", "direct"),
    ({"SystemRoot": "C:\\Windows", "PATHEXT": "../bad"}, "C:", ".COM;.EXE;.BAT;.CMD", "direct"),
    ({"SystemDrive": "d:", "PATHEXT": ".EXE" + chr(10) + ""}, "d:", ".COM;.EXE;.BAT;.CMD", "direct"),
    ({"SystemDrive": "D:", "SystemRoot": "C:\\Windows", "PATHEXT": ".EXE;.CMD"}, "D:", ".EXE;.CMD", "binding"),
    ({"SystemRoot": "C:\\Windows", "PATHEXT": ".EXE;.CMD"}, "C:", ".EXE;.CMD", "binding"),
    ({"SystemDrive": "BAD", "SystemRoot": "C:\\Windows", "PATHEXT": ".EXE"}, "C:", ".EXE", "binding"),
    ({"SystemRoot": "C:Windows", "PATHEXT": ".EXE"}, None, ".EXE", "binding"),
    ({"SystemRoot": "\\\\server\\share", "PATHEXT": ".EXE"}, None, ".EXE", "binding"),
    ({"SystemRoot": "C:\\Win" + chr(10) + "bad", "PATHEXT": ".EXE"}, None, ".EXE", "binding"),
    ({"SystemRoot": "C:\\Windows", "PATHEXT": None}, "C:", ".COM;.EXE;.BAT;.CMD", "binding"),
    ({"SystemRoot": "C:\\Windows", "PATHEXT": "../bad"}, "C:", ".COM;.EXE;.BAT;.CMD", "binding"),
    ({"SystemDrive": "d:", "PATHEXT": ".EXE" + chr(10) + ""}, "d:", ".COM;.EXE;.BAT;.CMD", "binding")
])
def test_child_environment_isolation_with_windows_platform(parent, drive, ext, mode, monkeypatch):
    import reverse_agent.platform_v1.opencode_executor as module
    monkeypatch.setattr(module.platform, "system", lambda: "Windows")
    if mode == "direct":
        child = module.build_role_child_env(parent, None, "executor")
    else:
        child = module.build_binding_child_env(parent, "{}")
    assert child["PATHEXT"] == ext
    if drive is None:
        assert "SystemDrive" not in child
    else:
        assert child["SystemDrive"] == drive


def test_real_windows_environment(tmp_path):
    import os, sys, subprocess, shutil
    if sys.platform != "win32":
        pytest.skip("Windows only")
    parent = {
        "PATH": os.environ.get("PATH"),
        "SystemRoot": os.environ.get("SystemRoot"),
        "PATHEXT": os.environ.get("PATHEXT")
    }
    child = build_role_child_env(parent, None, "executor")
    git = shutil.which("git")
    cmd = os.path.join(parent["SystemRoot"], "System32", "cmd.exe")
    assert git is not None and cmd is not None
    git_result = subprocess.run([git, "--version"], env=child, cwd=tmp_path, capture_output=True, text=True, timeout=10)
    cmd_result = subprocess.run([cmd, "/d", "/c", "echo %SystemDrive%"], env=child, cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert git_result.returncode == 0 and "git version" in git_result.stdout
    assert cmd_result.returncode == 0 and cmd_result.stdout.strip() == child["SystemDrive"] and "%SystemDrive%" not in cmd_result.stdout
