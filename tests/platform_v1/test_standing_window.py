"""Provider-free standing window renewal and goal adoption (Governance v2.1 D, #1310)."""
from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.platform_v1.run_store import TaskStoreError
from test_goal_window_rebind import _coordinator, _payload, _receipts, _services


def _standing(hours=12, days=10):
    until = datetime.now(timezone.utc) + timedelta(days=days)
    return {"window_hours": hours, "renew_until": until.isoformat()}


def _expire(s, window_id):
    s.store._conn.execute("UPDATE platform_autonomous_windows SET expires_at = '2000-01-01T00:00:00+00:00' WHERE id = ?",
                          (window_id,))
    assert s.control.active_window() is None


def _launched(s, window):
    goal = s.goals.create({"objective": "Keep running across windows", "idempotency_key": "standing",
                           "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    s.goals.plan(goal.id, expected_revision=1, tasks=[{"id": "T001", "title": "queued", "instruction": "run"}])
    s.goals.approve(goal.id, expected_revision=1)
    s.goals.launch(goal.id, expected_revision=1, window_id=window.id)
    return goal


def test_expired_standing_window_renews_with_identical_bounds_and_adopts_goals(tmp_path, monkeypatch):
    s = _services()
    first = s.autonomy.activate(_payload("standing", standing_renewal=_standing()))
    assert s.control.standing_window("standing")["status"] == "ACTIVE"
    goal = _launched(s, first)
    _expire(s, first.id)

    dispatched = []
    coordinator = _coordinator(s, tmp_path, [])
    monkeypatch.setattr(coordinator, "_execute_claimed_batch",
                        lambda **kw: dispatched.append(dict(kw["claimed"])) or len(kw["claimed"]))
    assert coordinator.tick() == 1

    second = s.control.active_window()
    assert second is not None and second.id != first.id
    assert (second.policy_id, second.policy_revision, second.confirmation) == ("standing", 2, "STANDING_RENEWAL")
    for field in ("repositories", "capabilities", "max_concurrent_tasks", "max_tasks", "max_retries",
                  "max_token_units", "max_cost_micro_units"):
        assert getattr(second, field) == getattr(first, field)
    lifetime = (datetime.fromisoformat(second.expires_at.replace("Z", "+00:00"))
                - datetime.fromisoformat(second.starts_at.replace("Z", "+00:00")))
    assert timedelta(hours=11, minutes=59) <= lifetime <= timedelta(hours=12)
    assert s.control.get_goal(goal.id).window_id == second.id
    assert len(_receipts(s, "standing_window_renewal")) == 1
    assert [r["reason"] for r in _receipts(s, "goal_window_rebind")] == ["standing_window_adoption"]
    assert len(dispatched) == 1
    # Renewal is idempotent while the successor is active.
    assert s.control.renew_standing_window() is None


@pytest.mark.parametrize("revocation", ["stop", "revoke"])
def test_revocation_takes_effect_immediately(revocation):
    s = _services()
    first = s.autonomy.activate(_payload("standing", standing_renewal=_standing()))
    if revocation == "stop":
        s.control.stop_window(first.id)
    else:
        assert s.control.revoke_standing_window("standing")
        _expire(s, first.id)
    assert s.control.renew_standing_window() is None
    assert s.control.active_window() is None
    assert s.control.standing_window("standing")["status"] == "REVOKED"


def test_horizon_caps_successor_and_ends_renewal():
    s = _services()
    now = datetime.now(timezone.utc)
    first = s.autonomy.activate(_payload("standing", standing_renewal={
        "window_hours": 24, "renew_until": (now + timedelta(hours=3)).isoformat()}))
    _expire(s, first.id)
    second = s.control.renew_standing_window()
    assert datetime.fromisoformat(second.expires_at.replace("Z", "+00:00")) <= now + timedelta(hours=3, seconds=1)
    _expire(s, second.id)
    assert s.control.renew_standing_window(now=now + timedelta(hours=3)) is None
    assert s.control.standing_window("standing")["status"] == "EXPIRED"


def test_window_without_standing_policy_never_renews():
    s = _services()
    first = s.autonomy.activate(_payload("plain"))
    _expire(s, first.id)
    assert s.control.renew_standing_window() is None
    assert s.control.standing_window("plain") is None


@pytest.mark.parametrize("standing, error", [
    ({"window_hours": 0, "renew_until": "2100-01-01T00:00:00+00:00"}, "standing_renewal_window_hours_invalid"),
    ({"window_hours": 169, "renew_until": "2100-01-01T00:00:00+00:00"}, "standing_renewal_window_hours_invalid"),
    ({"window_hours": 12, "renew_until": "2100-01-01T00:00:00+00:00"}, "standing_renewal_horizon_invalid"),
    ({"window_hours": 12}, "standing_renewal_invalid"),
    ({"window_hours": 12, "renew_until": "2100-01-01T00:00:00+00:00", "max_tasks": 99}, "standing_renewal_invalid"),
])
def test_standing_policy_is_bounded(standing, error):
    s = _services()
    with pytest.raises(TaskStoreError, match=error):
        s.autonomy.activate(_payload("standing", standing_renewal=standing))


def test_renewal_confirmation_cannot_be_used_for_owner_activation():
    s = _services()
    payload = s.autonomy._validate_policy(_payload("standing", standing_renewal=_standing()))
    with pytest.raises(TaskStoreError, match="owner_activation_confirmation_required"):
        s.control.activate_window(payload, confirmation="STANDING_RENEWAL")
    with pytest.raises(TaskStoreError, match="standing_renewal_invalid"):
        s.control.activate_window(s.autonomy._validate_policy(_payload("plain")),
                                  confirmation="STANDING_RENEWAL", _standing_renewal=True)
