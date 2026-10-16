"""Offline tests for safe, read-only update discovery."""
import subprocess
from reverse_agent.update_check import classify_revisions, probe_checkout

OLDER="a"*40
NEWER="b"*40


def test_newer_source_does_not_permit_install():
    result=classify_revisions(installed=OLDER,remote=NEWER,
                              ancestry="remote_descendant",local_modified=False)
    assert result["status"]=="SOURCE_UPDATE_AVAILABLE"
    assert result["verified_release"] is False
    assert result["install_authorized"] is False


def test_exact_commit_is_up_to_date_even_with_modifications():
    result=classify_revisions(installed=OLDER,remote=OLDER,
                              ancestry="unknown",local_modified=True)
    assert result["status"]=="UP_TO_DATE"
    assert result["local_modified"]


def test_working_changes_preserved_not_overwritten():
    result=classify_revisions(installed=OLDER,remote=NEWER,
                              ancestry="remote_descendant",local_modified=True)
    assert result["status"]=="LOCAL_CHANGES_PRESERVE"


def test_history_drift_separate_from_update_offer():
    for relation,expected in (
        ("local_descendant","LOCAL_AHEAD"),("diverged","DIVERGED"),
        ("unknown","REMOTE_CHANGE_UNVERIFIED"),
    ):
        assert classify_revisions(installed=OLDER,remote=NEWER,
                   ancestry=relation,local_modified=False)["status"]==expected


def test_malformed_sha_unknown():
    assert classify_revisions(installed=OLDER,remote="not-a-sha",
            ancestry="remote_descendant",local_modified=False)["status"]=="UNKNOWN"


def test_missing_checkout_unknown(tmp_path):
    assert probe_checkout(tmp_path/"missing")["reason"]=="missing_checkout"


def test_untrusted_origin_rejected_without_network(tmp_path,monkeypatch):
    repo=tmp_path/"repo"
    subprocess.run(["git","init",str(repo)],check=True,capture_output=True)
    subprocess.run(["git","-C",str(repo),"remote","add","origin",
                    "https://example.com/user/Nerelan.git"],check=True)
    r=probe_checkout(repo)
    assert r["status"]=="UNTRUSTED_ORIGIN"
    assert r["install_authorized"] is False


def test_canonical_origin_offline_never_blesses_stale_rev(tmp_path):
    repo=tmp_path/"repo"
    subprocess.run(["git","init",str(repo)],check=True,capture_output=True)
    subprocess.run(["git","-C",str(repo),"remote","add","origin",
                    "https://github.com/dddd2024/Nerelan.git"],check=True)
    r=probe_checkout(repo)
    assert r["status"]=="UNKNOWN"
    assert r["reason"]=="missing_installed_revision"