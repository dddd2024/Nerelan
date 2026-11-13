"""Regression tests for ``reverse_agent.update_check`` ancestry observation.

These tests exercise the *real* ``probe_checkout`` against a deterministic,
scripted ``subprocess.run`` so that git exit codes can be controlled without a
network, a provider or a real repository. They pin the corrected semantics:

* ``merge-base --is-ancestor X Y`` exit 0 *proves* X is an ancestor of Y,
* exit 1 *disproves* that relation,
* any other code (git fatal 128, timeout -1, OSError) proves *neither*.

Divergence is therefore only reported when *both* directions return exit 1.
When neither direction proves ancestry and at least one query errored, the
tool reports uncertainty (``REMOTE_CHANGE_UNVERIFIED``) rather than mistaking a
probe error for divergence. No installation is ever authorized.
"""
from __future__ import annotations

import subprocess

import pytest

from reverse_agent import update_check
from reverse_agent.update_check import probe_checkout


_INSTALLED = "0" * 40
_REMOTE = "1" * 40
_ORIGIN = "https://github.com/dddd2024/Nerelan.git"


class _Proc:
    """Minimal stand-in for ``subprocess.CompletedProcess``."""

    def __init__(self, returncode: int = 0, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


def _git_args(cmd) -> list[str]:
    """Subcommand args after ``git -C <root>`` and any command-scoped overrides.

    ``probe_checkout`` always prefixes ``-c core.fsmonitor=false`` and, when
    driver discovery found configured content filters, one ``-c
    filter.<driver>.<key>=<value>`` pair per driver. Every leading ``-c`` pair
    is skipped so the git subcommand stays the head of the returned list.
    """
    args = list(cmd[3:])
    while len(args) >= 2 and args[0] == "-c":
        args = args[2:]
    return args


def _timeout(cmd) -> subprocess.TimeoutExpired:
    return subprocess.TimeoutExpired(cmd=cmd, timeout=update_check._TIMEOUT)


class GitScript:
    """Deterministic scripted responses for the git commands probe issues."""

    def __init__(
        self,
        *,
        origin: str = _ORIGIN,
        installed: str = _INSTALLED,
        remote: str = _REMOTE,
        dirty: str = "",
        cat_file: int = 0,
        merge_base=None,
        ls_remote_code: int = 0,
        ls_remote_line: str | None = None,
        rev_parse_code: int = 0,
        shallow: bool | None = False,
        config_code: int = 0,
        config_names: str = "",
    ) -> None:
        self.origin = origin
        self.installed = installed
        self.remote = remote
        self.dirty = dirty
        self.cat_file = cat_file
        # Each entry is either an int returncode or an exception instance that
        # ``git`` should raise ( OSError / TimeoutExpired ), consumed in order
        # across the forward then reverse ancestry queries.
        self.merge_base = list(merge_base) if merge_base is not None else []
        self.ls_remote_code = ls_remote_code
        self.ls_remote_line = ls_remote_line
        self.rev_parse_code = rev_parse_code
        self.shallow = shallow
        self.config_code = config_code
        self.config_names = config_names
        self.calls: list[list[str]] = []

    def run(self, cmd, **kwargs):
        # probe_checkout always invokes ``git -C <root> -c core.fsmonitor=false <args...>``.
        args = _git_args(cmd)
        self.calls.append(args)
        head = args[0]
        if head == "remote":
            return _Proc(0, self.origin)
        if head == "rev-parse":
            if len(args) > 1 and args[1] == "--is-shallow-repository":
                return (_Proc(128, "") if self.shallow is None
                        else _Proc(0, str(self.shallow).lower()))
            return _Proc(self.rev_parse_code, self.installed)
        if head == "config":
            # Names-only content-filter driver discovery. The baseline fixture
            # configures no filter, so the probe adds no driver overrides.
            return _Proc(self.config_code, self.config_names)
        if head == "status":
            return _Proc(0, self.dirty)
        if head == "ls-remote":
            if self.ls_remote_code != 0:
                return _Proc(self.ls_remote_code, "")
            line = (
                self.ls_remote_line
                if self.ls_remote_line is not None
                else f"{self.remote}\trefs/heads/main"
            )
            return _Proc(0, line)
        if head == "cat-file":
            return _Proc(self.cat_file, "")
        if head == "merge-base":
            if self.merge_base:
                item = self.merge_base.pop(0)
                if isinstance(item, BaseException):
                    raise item
                return _Proc(int(item), "")
            return _Proc(1, "")
        return _Proc(1, "")


def _probe(tmp_path, monkeypatch, script: GitScript) -> dict[str, object]:
    """Run the real probe_checkout against a scripted subprocess.run."""
    monkeypatch.setattr(update_check.subprocess, "run", script.run)
    return probe_checkout(tmp_path)


# ---------------------------------------------------------------------------
# Proven ancestry (exit 0) in a single direction
# ---------------------------------------------------------------------------


def test_forward_zero_proves_remote_descendant(tmp_path, monkeypatch):
    # installed is an ancestor of remote -> remote is a descendant (update).
    script = GitScript(merge_base=[0, 1])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "SOURCE_UPDATE_AVAILABLE"
    assert result["reason"] == "source_only_not_release"
    assert result["installed_sha"] == _INSTALLED
    assert result["remote_main_sha"] == _REMOTE
    assert result["local_modified"] is False
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_reverse_zero_proves_local_descendant(tmp_path, monkeypatch):
    # remote is an ancestor of installed -> local is ahead.
    script = GitScript(merge_base=[1, 0])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "LOCAL_AHEAD"
    assert result["reason"] == "local_commit_ahead_of_main"
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_forward_zero_wins_even_if_reverse_errored(tmp_path, monkeypatch):
    # A proven relation still classifies correctly when the other query errors.
    script = GitScript(merge_base=[0, 128])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "SOURCE_UPDATE_AVAILABLE"
    assert result["install_authorized"] is False


def test_reverse_zero_wins_even_if_forward_errored(tmp_path, monkeypatch):
    script = GitScript(merge_base=[128, 0])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "LOCAL_AHEAD"
    assert result["install_authorized"] is False


# ---------------------------------------------------------------------------
# Both directions disproved (exit 1) -> divergence
# ---------------------------------------------------------------------------


def test_both_one_classifies_diverged(tmp_path, monkeypatch):
    script = GitScript(merge_base=[1, 1])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "DIVERGED"
    assert result["reason"] == "divergent_repository_history"
    assert result["install_authorized"] is False
    assert result["verified_release"] is False
    # Both ancestry queries must actually have been issued.
    merge_calls = [c for c in script.calls if c[0] == "merge-base"]
    assert len(merge_calls) == 2


# ---------------------------------------------------------------------------
# Probe errors must NOT be reported as divergence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forward,reverse",
    [
        (128, 1),   # git fatal on the forward query, reverse disproved
        (1, 128),   # forward disproved, git fatal on the reverse query
        (128, 128), # both queries errored
    ],
    ids=["forward-128-reverse-1", "forward-1-reverse-128", "both-128"],
)
def test_git_fatal_does_not_become_divergence(tmp_path, monkeypatch, forward, reverse):
    script = GitScript(merge_base=[forward, reverse])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED"
    assert result["reason"] == "remote_commit_not_locally_verified"
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_both_internal_negative_one_reports_uncertainty(tmp_path, monkeypatch):
    # -1 is the internal code the probe uses for OSError/timeout. Both queries
    # erroring must not be mistaken for a disproven relation (divergence); the
    # one-sided -1 cases are covered by the parametrized safety test below.
    script = GitScript(merge_base=[-1, -1])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED"
    assert result["reason"] == "remote_commit_not_locally_verified"
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_timeout_on_forward_query_does_not_become_divergence(tmp_path, monkeypatch):
    cmd = ["git", "-C", str(tmp_path), "merge-base", "--is-ancestor",
           _INSTALLED, _REMOTE]
    script = GitScript(merge_base=[_timeout(cmd), 1])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED"
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_timeout_on_reverse_query_does_not_become_divergence(tmp_path, monkeypatch):
    cmd = ["git", "-C", str(tmp_path), "merge-base", "--is-ancestor",
           _REMOTE, _INSTALLED]
    script = GitScript(merge_base=[1, _timeout(cmd)])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED"
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_both_queries_time_out_reports_uncertainty(tmp_path, monkeypatch):
    cmd = ["git", "-C", str(tmp_path), "merge-base", "--is-ancestor"]
    script = GitScript(merge_base=[_timeout(cmd), _timeout(cmd)])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED"
    assert result["reason"] == "remote_commit_not_locally_verified"


def test_oserror_on_forward_query_reports_uncertainty(tmp_path, monkeypatch):
    script = GitScript(merge_base=[OSError("probe unavailable"), 1])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED"
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_oserror_on_reverse_query_reports_uncertainty(tmp_path, monkeypatch):
    script = GitScript(merge_base=[1, OSError("probe unavailable")])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED"


# ---------------------------------------------------------------------------
# Unavailable local object and cat-file errors
# ---------------------------------------------------------------------------


def test_unavailable_remote_object_reports_uncertainty(tmp_path, monkeypatch):
    # cat-file exit 1: the remote commit is not present locally.
    script = GitScript(cat_file=1)
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED"
    assert result["reason"] == "remote_commit_not_locally_verified"
    # No ancestry query should have been issued without the object present.
    assert not any(c[0] == "merge-base" for c in script.calls)
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_cat_file_git_fatal_reports_uncertainty(tmp_path, monkeypatch):
    # cat-file exit 128: git itself errored, not an absent object.
    script = GitScript(cat_file=128)
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "REMOTE_CHANGE_UNVERIFIED"
    assert not any(c[0] == "merge-base" for c in script.calls)
    assert result["install_authorized"] is False


# ---------------------------------------------------------------------------
# Malformed remote replies
# ---------------------------------------------------------------------------


def test_malformed_remote_sha_reports_unexpected_reply(tmp_path, monkeypatch):
    script = GitScript(ls_remote_line="not-a-sha\trefs/heads/main")
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "unexpected_remote_reply"
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_malformed_remote_ref_reports_unexpected_reply(tmp_path, monkeypatch):
    script = GitScript(ls_remote_line=f"{_REMOTE}\trefs/heads/develop")
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "unexpected_remote_reply"


def test_remote_unavailable_reports_remote_unavailable(tmp_path, monkeypatch):
    script = GitScript(ls_remote_code=2)
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "REMOTE_UNAVAILABLE"
    assert result["reason"] == "network_or_remote_unavailable"
    assert result["installed_sha"] == _INSTALLED
    assert result["local_modified"] is False
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


# ---------------------------------------------------------------------------
# Non-ancestry branches and safety invariants
# ---------------------------------------------------------------------------


def test_same_commit_is_up_to_date_without_ancestry_query(tmp_path, monkeypatch):
    script = GitScript(installed=_REMOTE, remote=_REMOTE)
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "UP_TO_DATE"
    assert result["reason"] == "same_source_commit"
    assert not any(c[0] in ("cat-file", "merge-base") for c in script.calls)
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_local_modified_preserves_even_when_ancestry_would_diverge(tmp_path, monkeypatch):
    # The working tree is dirty, so the classifier preserves local changes even
    # though the ancestry queries (both exit 1) would otherwise indicate
    # divergence. Preservation takes priority over divergence at classification
    # time; the probe still observes ancestry but never acts on it.
    script = GitScript(dirty=" M local_change.txt\n", merge_base=[1, 1])
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "LOCAL_CHANGES_PRESERVE"
    assert result["reason"] == "source_has_uncommitted_changes"
    assert result["local_modified"] is True
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_untrusted_origin_short_circuits_without_local_disclosure(tmp_path, monkeypatch):
    script = GitScript(origin="https://example.invalid/other.git")
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "UNTRUSTED_ORIGIN"
    assert result["reason"] == "canonical_origin_required"
    # No rev-parse / status / ls-remote issued against an untrusted remote.
    assert not any(c[0] in ("rev-parse", "status", "ls-remote") for c in script.calls)
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


def test_missing_installed_revision_reports_unknown(tmp_path, monkeypatch):
    script = GitScript(rev_parse_code=1)
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "missing_installed_revision"
    assert not any(c[0] in ("status", "ls-remote") for c in script.calls)
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


@pytest.mark.parametrize(
    "shallow,expected_status",
    [
        (False, "DIVERGED"),
        (True, "REMOTE_CHANGE_UNVERIFIED"),
        (None, "REMOTE_CHANGE_UNVERIFIED"),
    ],
)
def test_two_negative_ancestry_results_require_complete_history(
    tmp_path, monkeypatch, shallow, expected_status
):
    script = GitScript(merge_base=[1, 1], shallow=shallow)
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == expected_status
    assert ["rev-parse", "--is-shallow-repository"] in script.calls
    assert result["install_authorized"] is False


def test_missing_checkout_reports_missing(tmp_path, monkeypatch):
    result = probe_checkout(tmp_path / "does_not_exist")
    assert result["status"] == "UNKNOWN"
    assert result["reason"] == "missing_checkout"
    assert result["install_authorized"] is False
    assert result["verified_release"] is False


@pytest.mark.parametrize(
    "merge_base,expected_status",
    [
        ([0, 1], "SOURCE_UPDATE_AVAILABLE"),
        ([1, 0], "LOCAL_AHEAD"),
        ([1, 1], "DIVERGED"),
        ([128, 1], "REMOTE_CHANGE_UNVERIFIED"),
        ([1, 128], "REMOTE_CHANGE_UNVERIFIED"),
        ([128, 128], "REMOTE_CHANGE_UNVERIFIED"),
        ([-1, 1], "REMOTE_CHANGE_UNVERIFIED"),
        ([1, -1], "REMOTE_CHANGE_UNVERIFIED"),
    ],
    ids=[
        "forward-0", "reverse-0", "both-1-diverged",
        "forward-128", "reverse-128", "both-128",
        "forward-neg1", "reverse-neg1",
    ],
)
def test_safety_fields_never_authorized(tmp_path, monkeypatch, merge_base, expected_status):
    # Across every ancestry outcome the module never authorizes an install or
    # claims a verified release.
    script = GitScript(merge_base=merge_base)
    result = _probe(tmp_path, monkeypatch, script)
    assert result["status"] == expected_status
    assert result["install_authorized"] is False
    assert result["verified_release"] is False
