"""Read-only weekly subscription utilization pacing, not a quota authorization.

The provider-observed utilization percentage is not a precise token balance.
A target of 4-5 days denotes when to USE useful work, not an early reset.
"""
from datetime import datetime, timedelta, timezone
from math import isfinite


def _utc(dt):
    if not isinstance(dt, datetime) or dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("aware_datetime_required")
    return dt.astimezone(timezone.utc)


def plan_pace(*, used_percent, window_started_at, next_reset_at, observed_at, now,
              target_days=4.5, target_used_percent=95.0, eligible_work=0,
              short_window_available=None, freshness_seconds=3600, tolerance_percent=5.0):
    """Return advisory only; dispatcher must separately enforce every quota/permission."""
    base = dict(state="UNKNOWN", advice="NONE", reason=None,
                target_used_by_now_percent=None, needed_percent_per_day=None,
                until_reset_hours=None, target_at=None, non_authoritative=True,
                unit="provider_reported_weekly_utilization_percent")

    def unknown(reason):
        return base | {"reason": reason}

    try:
        if None in (used_percent, window_started_at, next_reset_at, observed_at):
            return unknown("missing_evidence")
        start, reset, sample, current = map(
            _utc, (window_started_at, next_reset_at, observed_at, now))
        if any(type(x) not in (int, float) or not isfinite(x) for x in
               (used_percent, target_days, target_used_percent, tolerance_percent)):
            return unknown("invalid_numeric")
        if not (0 <= used_percent <= 100 and 0 < target_days <= 7 and
                0 <= target_used_percent <= 100 and 0 <= tolerance_percent <= 100):
            return unknown("invalid_policy_or_usage")
        if type(eligible_work) is not int or eligible_work < 0:
            return unknown("invalid_work")
        if short_window_available is not None and type(short_window_available) is not bool:
            return unknown("invalid_short_window")
        if type(freshness_seconds) is not int or freshness_seconds <= 0:
            return unknown("invalid_freshness")
    except (ValueError, TypeError, OverflowError):
        return unknown("invalid_observation")

    if reset <= start or current < start or sample < start:
        return unknown("contradictory_window")
    if sample > current + timedelta(seconds=60):
        return unknown("future_sample")
    if (current - sample).total_seconds() > freshness_seconds:
        return unknown("stale_sample")
    if current >= reset:
        return unknown("reset_not_yet_observed")
    target_at = min(start + timedelta(days=target_days), reset)
    window_seconds = (target_at - start).total_seconds()
    if window_seconds <= 0:
        return unknown("bad_target_window")
    fraction = min(1.0, max(0.0, (current - start).total_seconds()/window_seconds))
    target_now = target_used_percent * fraction
    target_remaining = (target_at - current).total_seconds()
    per_day = (round(max(0.0, target_used_percent-used_percent)*86400 / target_remaining, 3)
               if target_remaining > 0 else None)
    if used_percent >= target_used_percent:
        state = "TARGET_REACHED"
    elif used_percent < target_now-tolerance_percent:
        state = "BEHIND"
    elif used_percent > target_now+tolerance_percent:
        state = "AHEAD"
    else:
        state = "ON_PACE"
    if eligible_work == 0:
        advice = "NO_MEANINGFUL_WORK"
    elif short_window_available is not True:
        advice = "WAIT_SHORT_WINDOW" if short_window_available is False else "VERIFY_SHORT_WINDOW"
    elif state == "BEHIND":
        advice = "PRIORITIZE_USEFUL_TASKS"
    elif state == "AHEAD":
        advice = "PREFER_OTHER_ELIGIBLE_RESOURCES"
    elif state == "TARGET_REACHED":
        advice = "PRESERVE_RESERVE"
    else:
        advice = "NORMAL_PRIORITY"
    return base | dict(state=state, advice=advice, reason="advisory_not_admission",
                       target_used_by_now_percent=round(target_now, 3),
                       needed_percent_per_day=per_day,
                       until_reset_hours=round((reset-current).total_seconds()/3600, 3),
                       target_at=target_at.isoformat())