"""Derived operational alerts for unattended multi-account runs.

An alert is a *view of current state*, not a stored fact: every evaluation
recomputes the active set from the pool view and the runtime status, so a
restart cannot leave a stale alert behind and there is no alert database to
reconcile. :class:`AlertLedger` only turns consecutive evaluations into
raise/resolve transitions, which are what an operator wants logged once.

Nothing here changes admission, routing, budgets or authority.
"""
from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

from .config import MultiAccountConfig

_logger = logging.getLogger(__name__)

CRITICAL = "critical"
WARNING = "warning"
INFO = "info"
_SEVERITY_ORDER = {CRITICAL: 0, WARNING: 1, INFO: 2}

RECENT_LIMIT = 100
WINDOW_EXPIRY_NOTICE_SECONDS = 3600.0


@dataclass(frozen=True)
class Alert:
    """One active condition. ``(code, subject)`` is its identity."""

    code: str
    severity: str
    subject: str
    detail: str

    @property
    def key(self) -> tuple[str, str]:
        return self.code, self.subject


def _epoch(value: Any) -> Optional[float]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _pool_alerts(pool: Mapping[str, Any], config: MultiAccountConfig) -> Iterable[Alert]:
    source = pool.get("source")
    if source == "unavailable":
        yield Alert("perception_unavailable", WARNING, "pool", "账户状态暂时无法读取")
        return
    if source == "none":
        return
    accounts = pool.get("accounts") or ()
    usable = sum(1 for account in accounts if account.get("dispatchable"))
    if accounts and usable == 0:
        yield Alert("pool_no_usable_account", CRITICAL, "pool", "没有可派发账户，任务将等待额度恢复")
    elif accounts and usable < config.alert_min_usable_accounts:
        yield Alert("pool_capacity_low", WARNING, "pool",
                    f"可派发账户仅 {usable} 个，低于阈值 {config.alert_min_usable_accounts}")
    for account in accounts:
        ref = str(account.get("account_ref") or "")
        name = account.get("provider") or ref
        cooldown = account.get("cooldown") or {}
        if cooldown.get("tier") == "quarantine":
            yield Alert("account_quarantined", WARNING, ref,
                        f"{name} 已隔离：{cooldown.get('kind') or 'unknown'}")
        if account.get("health") == "ABNORMAL":
            yield Alert("account_abnormal", WARNING, ref, f"{name} 状态异常")
        elif account.get("health") == "EXHAUSTED":
            yield Alert("account_exhausted", INFO, ref, f"{name} 额度已用尽")


def _budget_alerts(budget: Mapping[str, Any], config: MultiAccountConfig) -> Iterable[Alert]:
    for label, name, unit in (("成本", "cost", "cost_micro_units"), ("Token", "token", "token_units")):
        limit = budget.get(f"max_{unit}")
        remaining = budget.get(f"remaining_{unit}")
        if not isinstance(limit, (int, float)) or limit <= 0 or not isinstance(remaining, (int, float)):
            continue
        if remaining <= 0:
            yield Alert("window_budget_exhausted", CRITICAL, name, f"{label}预算已耗尽，不再派发新任务")
        elif remaining / limit < config.alert_budget_warn_ratio:
            yield Alert("window_budget_low", WARNING, name,
                        f"{label}预算剩余 {remaining / limit:.0%}")


def _runtime_alerts(runtime: Mapping[str, Any], config: MultiAccountConfig,
                    now: float, stalled_seconds: Optional[float]) -> Iterable[Alert]:
    coordinator = runtime.get("coordinator") or {}
    window = runtime.get("window") or None
    if window and coordinator.get("lifecycle") == "STOPPED":
        yield Alert("coordinator_stopped", CRITICAL, "coordinator", "自治窗口有效，但协调器未运行")
    if stalled_seconds is not None and stalled_seconds >= config.alert_stall_seconds:
        yield Alert("coordinator_stalled", CRITICAL, "coordinator",
                    f"协调器已 {int(stalled_seconds)} 秒没有完成一轮调度")
    if coordinator.get("last_error"):
        yield Alert("coordinator_error", WARNING, "coordinator", str(coordinator["last_error"])[:200])
    for reason in coordinator.get("admission_holds") or ():
        yield Alert("admission_hold", WARNING, str(reason), f"任务准入被搁置：{reason}")
    if coordinator.get("stranded_goals"):
        yield Alert("goals_stranded", WARNING, "goals",
                    f"{len(coordinator['stranded_goals'])} 个目标的窗口已无法派发")
    if window and not window.get("standing_renewal"):
        expires = _epoch(window.get("expires_at"))
        if expires is not None and 0 <= expires - now < WINDOW_EXPIRY_NOTICE_SECONDS:
            yield Alert("window_expiring", INFO, str(window.get("id") or "window"),
                        "自治窗口将在一小时内到期，且未配置续期")


def evaluate_alerts(pool: Mapping[str, Any], runtime: Mapping[str, Any],
                    config: MultiAccountConfig, *, now: float,
                    stalled_seconds: Optional[float] = None) -> list[Alert]:
    """Pure rule evaluation: the same inputs always yield the same alerts."""
    alerts = list(_pool_alerts(pool, config))
    alerts.extend(_budget_alerts(runtime.get("budget") or {}, config))
    alerts.extend(_runtime_alerts(runtime, config, now, stalled_seconds))
    unique = {alert.key: alert for alert in alerts}
    return sorted(unique.values(), key=lambda a: (_SEVERITY_ORDER[a.severity], a.code, a.subject))


def jsonl_sink(path: Path, *, max_bytes: int, backups: int) -> Callable[[Mapping[str, Any]], None]:
    """Bounded JSONL transition log, rotated by the standard library handler."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=max_bytes, backupCount=backups,
                                  encoding="utf-8", delay=True)
    handler.setFormatter(logging.Formatter("%(message)s"))
    sink = logging.Logger(f"nerelan.multi_account.alerts.{path}", level=logging.INFO)
    sink.addHandler(handler)

    def write(event: Mapping[str, Any]) -> None:
        sink.info(json.dumps(event, ensure_ascii=False, sort_keys=True))

    write.close = handler.close  # type: ignore[attr-defined]
    return write


class AlertLedger:
    """Turns consecutive evaluations into raise/resolve events, once each."""

    def __init__(self, sink: Optional[Callable[[Mapping[str, Any]], None]] = None) -> None:
        self._sink = sink
        self._active: dict[tuple[str, str], dict[str, Any]] = {}
        self._recent: deque[dict[str, Any]] = deque(maxlen=RECENT_LIMIT)

    def observe(self, alerts: Iterable[Alert], *, now: float) -> list[dict[str, Any]]:
        current = {alert.key: alert for alert in alerts}
        events: list[dict[str, Any]] = []
        for key, record in list(self._active.items()):
            if key not in current:
                del self._active[key]
                events.append({**record, "event": "resolved", "at": now})
        for key, alert in current.items():
            existing = self._active.get(key)
            record = {**asdict(alert), "since": existing["since"] if existing else now}
            self._active[key] = record
            if existing is None or existing["severity"] != alert.severity:
                events.append({**record, "event": "raised", "at": now})
        for event in events:
            self._recent.appendleft(event)
            self._emit(event)
        return events

    def _emit(self, event: Mapping[str, Any]) -> None:
        # Delivery is best-effort: a full disk must not end an unattended run.
        level = logging.INFO if event["event"] == "resolved" else logging.WARNING
        try:
            _logger.log(level, "multi_account_alert event=%s code=%s subject=%s",
                        event["event"], event["code"], event["subject"])
            if self._sink is not None:
                self._sink(event)
        except Exception:  # noqa: BLE001
            pass

    def close(self) -> None:
        close = getattr(self._sink, "close", None)
        if close is not None:
            close()

    def active(self) -> list[dict[str, Any]]:
        return sorted(self._active.values(),
                      key=lambda a: (_SEVERITY_ORDER[a["severity"]], a["code"], a["subject"]))

    def recent(self) -> list[dict[str, Any]]:
        return list(self._recent)
