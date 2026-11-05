"""Run watchdog: bounded duration and idle detection.

"长时间不间断" needs an end condition, otherwise an unattended run only stops
when someone kills it. ``conclude`` means "stop starting work, let in-flight
attempts land"; ``stop`` is the hard post-deadline verdict.
"""
from reverse_agent.platform_v1.multi_account.config import MultiAccountConfig
from reverse_agent.platform_v1.multi_account.watchdog import RunWatchdog

START = 1_700_000_000.0


def watchdog(**overrides):
    config = MultiAccountConfig(**overrides)
    clock = lambda: START  # noqa: E731
    return RunWatchdog(config, clock=clock)


def test_default_configuration_never_concludes():
    dog = watchdog()
    dog.start(now=START)
    verdict = dog.check(now=START + 10 * 365 * 24 * 3600)
    assert verdict["action"] == "continue"
    assert verdict["reason"] == "within_budget"


def test_deadline_concludes_then_hard_stops():
    dog = watchdog(max_run_duration_seconds=100.0, watchdog_hard_stop_ratio=1.5)
    dog.start(now=START)
    assert dog.check(now=START + 99)["action"] == "continue"
    assert dog.check(now=START + 100)["reason"] == "run_deadline_reached"
    assert dog.check(now=START + 100)["action"] == "conclude"
    assert dog.check(now=START + 150)["action"] == "stop"


def test_idle_timeout_concludes_without_a_deadline():
    dog = watchdog(max_idle_seconds=60.0)
    dog.start(now=START)
    dog.heartbeat(now=START + 30)
    assert dog.check(now=START + 60)["action"] == "continue"
    verdict = dog.check(now=START + 91)
    assert verdict["action"] == "conclude"
    assert verdict["reason"] == "idle_timeout"


def test_a_failed_attempt_still_counts_as_progress():
    dog = watchdog(max_idle_seconds=60.0)
    dog.start(now=START)
    dog.heartbeat(now=START + 50)
    assert dog.check(now=START + 100)["action"] == "continue"


def test_conclude_is_sticky_and_idempotent():
    dog = watchdog()
    dog.start(now=START)
    dog.conclude(now=START + 5)
    assert dog.check(now=START + 6)["reason"] == "already_concluded"
    assert dog.should_dispatch(now=START + 6) is False


def test_disabled_watchdog_ignores_limits():
    dog = watchdog(watchdog_enabled=False, max_run_duration_seconds=10.0)
    dog.start(now=START)
    verdict = dog.check(now=START + 1000)
    assert verdict["action"] == "continue"
    assert verdict["reason"] == "watchdog_disabled"


def test_remaining_seconds_is_bounded_by_the_deadline():
    dog = watchdog(max_run_duration_seconds=100.0)
    assert dog.remaining_seconds(now=START) == 100.0
    dog.start(now=START)
    assert dog.remaining_seconds(now=START + 40) == 60.0
    assert dog.remaining_seconds(now=START + 500) == 0.0


def test_unlimited_run_reports_no_remaining_seconds():
    assert watchdog().remaining_seconds(now=START) is None


def test_state_survives_a_restart(tmp_path):
    import json

    path = tmp_path / "watchdog.json"
    config = MultiAccountConfig(max_run_duration_seconds=100.0)
    first = RunWatchdog(config, clock=lambda: START,
                        persist=lambda snap: path.write_text(json.dumps(snap), encoding="utf-8"))
    first.start(now=START)
    first.heartbeat(now=START + 50)

    restored = RunWatchdog(config, clock=lambda: START,
                           state=json.loads(path.read_text(encoding="utf-8")))
    assert restored.check(now=START + 100)["action"] == "conclude"
    assert restored.status(now=START)["attempts"] == 1


def test_start_resets_a_finished_window():
    dog = watchdog()
    dog.start(now=START)
    dog.heartbeat(now=START + 10)
    dog.conclude(now=START + 20)
    dog.start(now=START + 30)
    assert dog.check(now=START + 40)["action"] == "continue"
    assert dog.status(now=START + 40)["attempts"] == 0
