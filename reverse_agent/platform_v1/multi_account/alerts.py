"""Rule-based alerting for the multi-account orchestration brain.

Domain D (日志与告警). Perception already classifies accounts and the scheduler
already records cooldowns, but neither tells an operator that something changed.
This module turns those observations into a bounded stream of :class:`Alert`
records — one code, one subject, one severity, one piece of evidence — so a
human or an external sink can act on it.

Three properties make it safe for an unattended run:

* **Deduplicated.** The same ``(code, subject)`` inside
  ``alert_quiet_seconds`` is suppressed and only its repeat count grows; an
  account that stays exhausted for six hours produces one alert, not thousands.
* **Bounded.** History is capped by ``alert_max_history`` and persisted in the
  shared atomic document, so a multi-week run cannot grow it without limit.
* **Side-effect free by default.** No network I/O lives here. A sink is
  injected; the only built-in sink is a structured ``logging`` line, enabled by
  ``alert_log_enabled``. A webhook/IM sink is a host-side extension point — it
  is deliberately not implemented so this package stays offline-testable.
"""
from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from .config import MultiAccountConfig
from .status import AccountHealth, AccountStatus

_SEVERITY_ORDER = {"info": 10, "warning": 20, "error": 30, "critical": 40}


class AlertSeverity(str, enum.Enum):
    """Ordered severity; higher values are more urgent."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        return _SEVERITY_ORDER[self.value]


@dataclass(frozen=True)
class Alert:
    """One operator-facing fact, with the evidence that produced it."""

    code: str
    severity: AlertSeverity
    subject: str
    message: str
    at: float
    evidence: dict[str, Any] = field(default_factory=dict)
    repeats: int = 1

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe shape for the API/dashboard and the alert log."""
        return {
            "code": self.code,
            "severity": self.severity.value,
            "subject": self.subject,
            "message": self.message,
            "at": self.at,
            "evidence": dict(self.evidence),
            "repeats": self.repeats,
        }

    @property
    def key(self) -> tuple[str, str]:
        return (self.code, self.subject)


def logging_sink(alert: Alert) -> None:
    """Built-in sink: one structured line per emitted alert.

    Kept in this module so callers do not each invent a log format, and kept
    optional so a library user that collects alerts programmatically is not
    forced into log noise.
    """
    import logging

    logging.getLogger("reverse_agent.multi_account").warning(
        "multi_account_alert code=%s severity=%s subject=%s repeats=%s %s",
        alert.code, alert.severity.value, alert.subject, alert.repeats, alert.message)


class AlertEngine:
    """Evaluates alert rules, suppresses repeats and keeps a bounded history."""

    def __init__(self, config: MultiAccountConfig, *,
                 clock: Callable[[], float] = time.time,
                 sink: Optional[Callable[[Alert], None]] = None,
                 state: Optional[Mapping[str, Any]] = None,
                 persist: Optional[Callable[[dict[str, Any]], None]] = None) -> None:
        self._config = config
        self._clock = clock
        self._sink = sink if sink is not None else (logging_sink if config.alert_log_enabled else None)
        self._persist = persist
        self._history: list[dict[str, Any]] = []
        self._last_at: dict[str, float] = {}
        self._suppressed: dict[str, int] = {}
        self._pending: list[Alert] = []
        self.load(state)

    # --- evaluation -----------------------------------------------------------
    def evaluate(self, statuses: Optional[Iterable[AccountStatus]] = None, *,
                 budget: Optional[Mapping[str, Any]] = None,
                 cooldowns: Optional[Mapping[str, tuple[int, str]]] = None,
                 account_scores: Optional[Mapping[str, Mapping[str, Any]]] = None,
                 events: Iterable[Mapping[str, Any]] = (),
                 run_state: Optional[Mapping[str, Any]] = None,
                 now: Optional[float] = None) -> list[Alert]:
        """Derive alerts from one observation of the whole pool.

        ``cooldowns`` maps ``account_ref -> (streak, kind)`` and ``account_scores``
        is the scoreboard's public view; both are optional so a caller with only
        statuses still gets the account/quota/budget rules. ``events`` carries
        one-shot host facts (dead-letter, feedback failure) that no rule can
        derive from state.

        ``statuses`` is **optional on purpose**: ``None`` means "this call is not
        reporting on the pool at all" (a host event, a policy change) and skips
        the account/pool rules, while an explicit empty list means "observed
        nothing" and does raise ``no_accounts_observed``. Collapsing the two
        would make every host event emit a phantom empty-pool error.
        """
        if not self._config.alerts_enabled:
            return []
        now = self._clock() if now is None else now
        observed = list(statuses) if statuses is not None else None
        candidates: list[Alert] = []
        if observed is not None:
            pool_alerts, suppressed = self._pool_rules(observed, now=now)
            # A pool-wide verdict replaces the per-account notices it covers:
            # one "all accounts abnormal" is actionable, five identical
            # per-account lines are noise an operator learns to ignore.
            candidates.extend(self._account_rules(observed, now=now, suppressed=suppressed))
            candidates.extend(pool_alerts)
        candidates.extend(self._budget_rules(budget, now=now))
        candidates.extend(self._cooldown_rules(cooldowns, now=now))
        candidates.extend(self._reliability_rules(account_scores, now=now))
        candidates.extend(self._event_rules(events, now=now))
        candidates.extend(self._run_rules(run_state, now=now))
        return [alert for alert in (self._emit(c, now=now) for c in candidates) if alert]

    # --- rules ----------------------------------------------------------------
    @staticmethod
    def _account_rules(statuses: Sequence[AccountStatus], *, now: float,
                       suppressed: frozenset[str] = frozenset()) -> list[Alert]:
        alerts: list[Alert] = []
        for status in statuses:
            evidence = {"provider": status.provider, "headroom_pct": status.headroom_pct,
                        "anomaly_flags": list(status.anomaly_flags)}
            if status.health is AccountHealth.ABNORMAL and "account_abnormal" not in suppressed:
                alerts.append(Alert(
                    code="account_abnormal", severity=AlertSeverity.ERROR,
                    subject=status.account_ref, at=now, evidence=evidence,
                    message=f"账户 {status.account_ref} 异常（凭据/限流错误），已隔离"))
            elif status.health is AccountHealth.EXHAUSTED and "account_exhausted" not in suppressed:
                alerts.append(Alert(
                    code="account_exhausted", severity=AlertSeverity.WARNING,
                    subject=status.account_ref, at=now, evidence=evidence,
                    message=f"账户 {status.account_ref} 额度耗尽，切换至池内其他账户"))
        return alerts

    def _pool_rules(self, statuses: Sequence[AccountStatus], *,
                    now: float) -> tuple[list[Alert], frozenset[str]]:
        """Pool-level verdicts plus the per-account codes they supersede."""
        if not statuses:
            return [Alert(code="no_accounts_observed", severity=AlertSeverity.ERROR,
                          subject="pool", at=now, evidence={"observed": 0},
                          message="未观测到任何额度账户，任务将保持等待")], frozenset()
        usable = [s for s in statuses
                  if s.health in (AccountHealth.HEALTHY, AccountHealth.DEGRADED)]
        alerts: list[Alert] = []
        suppressed: set[str] = set()
        unobserved = [s.account_ref for s in statuses
                      if s.health in (AccountHealth.STALE, AccountHealth.UNKNOWN)]
        if usable:
            # A usable pool does not page per unobservable account, but a pool
            # that silently shrinks is a real incident: on a real machine four of
            # eleven accounts were unobservable while the dashboard showed only
            # "healthy". Warn once, at the pool level, when a material share is
            # unobservable — enough to explain capacity that never appears.
            if len(unobserved) >= 2 and len(unobserved) * 4 >= len(statuses):
                alerts.append(Alert(
                    code="perception_partial", severity=AlertSeverity.WARNING,
                    subject="pool", at=now,
                    evidence={"unobserved": unobserved, "total": len(statuses),
                              "usable": len(usable)},
                    message=(f"{len(unobserved)}/{len(statuses)} 个账户不可观测，"
                             f"实际可用容量低于池大小")))
            return alerts, frozenset(suppressed)

        exhausted = [s.account_ref for s in statuses if s.health is AccountHealth.EXHAUSTED]
        abnormal = [s.account_ref for s in statuses if s.health is AccountHealth.ABNORMAL]
        if abnormal and len(abnormal) == len(statuses):
            alerts.append(Alert(
                code="all_accounts_abnormal", severity=AlertSeverity.CRITICAL,
                subject="pool", at=now, evidence={"abnormal": abnormal},
                message="全部账户异常，需要人工修复凭据后解除隔离"))
            suppressed.add("account_abnormal")
        elif exhausted and not abnormal and len(exhausted) + len(unobserved) == len(statuses):
            alerts.append(Alert(
                code="all_accounts_exhausted", severity=AlertSeverity.CRITICAL,
                subject="pool", at=now,
                evidence={"exhausted": exhausted, "unobserved": unobserved},
                message="全部账户额度耗尽，任务保持至最早窗口重置"))
            suppressed.add("account_exhausted")
        elif len(unobserved) == len(statuses):
            alerts.append(Alert(
                code="perception_stale", severity=AlertSeverity.WARNING,
                subject="pool", at=now, evidence={"stale": unobserved},
                message="全部账户观测过期，调度退化为保守模式"))
        return alerts, frozenset(suppressed)

    def _budget_rules(self, budget: Optional[Mapping[str, Any]], *, now: float) -> list[Alert]:
        if not isinstance(budget, Mapping) or not budget.get("enforced"):
            return []
        utilization = budget.get("utilization")
        if not isinstance(utilization, (int, float)):
            return []
        evidence = {"utilization": utilization, "spent_units": budget.get("spent_units"),
                    "cap_units": budget.get("cap_units"),
                    "remaining_units": budget.get("remaining_units")}
        if utilization >= 1.0:
            return [Alert(code="cost_budget_exhausted", severity=AlertSeverity.CRITICAL,
                          subject="budget", at=now, evidence=evidence,
                          message="成本预算已用尽，新任务保持至窗口滚动")]
        soft = self._config.cost_budget_soft_ratio
        if utilization >= soft:
            return [Alert(code="cost_budget_soft_cap", severity=AlertSeverity.WARNING,
                          subject="budget", at=now, evidence=evidence,
                          message=f"成本预算使用率 {utilization:.0%} 达到软阈值 {soft:.0%}，调度转为最低成本账户")]
        return []

    def _cooldown_rules(self, cooldowns: Optional[Mapping[str, tuple[int, str]]], *,
                        now: float) -> list[Alert]:
        if not isinstance(cooldowns, Mapping):
            return []
        alerts: list[Alert] = []
        threshold = self._config.alert_failure_streak_threshold
        for ref, entry in cooldowns.items():
            try:
                streak, kind = entry
            except (TypeError, ValueError):
                continue
            if int(streak) >= threshold:
                alerts.append(Alert(
                    code="account_flapping", severity=AlertSeverity.WARNING,
                    subject=str(ref), at=now,
                    evidence={"streak": int(streak), "failure_kind": str(kind),
                              "threshold": threshold},
                    message=f"账户 {ref} 连续失败 {streak} 次（{kind}），退避已升级"))
        return alerts

    def _reliability_rules(self, scores: Optional[Mapping[str, Mapping[str, Any]]], *,
                           now: float) -> list[Alert]:
        if not isinstance(scores, Mapping):
            return []
        alerts: list[Alert] = []
        for ref, view in scores.items():
            reliability = view.get("reliability")
            attempts = view.get("attempts")
            if not isinstance(reliability, (int, float)) or not isinstance(attempts, int):
                continue
            if attempts >= self._config.alert_min_samples and \
                    reliability < self._config.alert_min_success_rate:
                alerts.append(Alert(
                    code="account_unreliable", severity=AlertSeverity.WARNING,
                    subject=str(ref), at=now,
                    evidence={"reliability": round(float(reliability), 4), "attempts": attempts,
                              "threshold": self._config.alert_min_success_rate},
                    message=f"账户 {ref} 成功率 {float(reliability):.0%} 低于阈值，排名已降权"))
        return alerts

    @staticmethod
    def _event_rules(events: Iterable[Mapping[str, Any]], *, now: float) -> list[Alert]:
        alerts: list[Alert] = []
        for event in events:
            if not isinstance(event, Mapping):
                continue
            code = str(event.get("code") or "host_event")
            try:
                severity = AlertSeverity(str(event.get("severity") or "warning"))
            except ValueError:
                severity = AlertSeverity.WARNING
            alerts.append(Alert(
                code=code, severity=severity,
                subject=str(event.get("subject") or "host"),
                message=str(event.get("message") or code), at=now,
                evidence=dict(event.get("evidence") or {})))
        return alerts

    @staticmethod
    def _run_rules(run_state: Optional[Mapping[str, Any]], *, now: float) -> list[Alert]:
        if not isinstance(run_state, Mapping):
            return []
        action = str(run_state.get("action") or "continue")
        if action == "continue":
            return []
        severity = AlertSeverity.CRITICAL if action == "stop" else AlertSeverity.WARNING
        return [Alert(code=f"run_{action}", severity=severity, subject="run", at=now,
                      evidence={k: v for k, v in run_state.items() if k != "action"},
                      message=f"无人值守运行判定为 {action}：{run_state.get('reason', '')}")]

    # --- emission / suppression ----------------------------------------------
    def _emit(self, alert: Alert, *, now: float) -> Optional[Alert]:
        key = f"{alert.code}|{alert.subject}"
        last = self._last_at.get(key)
        quiet = self._config.alert_quiet_seconds
        if last is not None and now - last < quiet:
            # Suppressed: keep counting so the next emission can report volume.
            self._bump(key, now=now)
            return None
        repeats = self._take_count(key) + 1
        self._last_at[key] = now
        emitted = Alert(code=alert.code, severity=alert.severity, subject=alert.subject,
                        message=alert.message, at=now, evidence=dict(alert.evidence),
                        repeats=repeats)
        self._pending.append(emitted)
        self._history.append(emitted.to_dict())
        overflow = len(self._history) - self._config.alert_max_history
        if overflow > 0:
            del self._history[:overflow]
        self._save()
        if self._sink is not None:
            try:
                self._sink(emitted)
            except Exception:  # noqa: BLE001 - a broken sink must not break the loop
                pass
        return emitted

    def _bump(self, key: str, *, now: float) -> None:
        self._suppressed[key] = self._suppressed.get(key, 0) + 1

    def _take_count(self, key: str) -> int:
        return self._suppressed.pop(key, 0)

    # --- read -----------------------------------------------------------------
    def pending(self) -> list[Alert]:
        """Alerts emitted since the last :meth:`drain` (not yet acknowledged)."""
        return list(self._pending)

    def drain(self) -> list[Alert]:
        """Return and clear the pending queue (the host's delivery point)."""
        pending, self._pending = self._pending, []
        return pending

    def history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def last_seen(self) -> dict[str, float]:
        return dict(self._last_at)

    # --- persistence ----------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        return {"history": list(self._history), "last_at": dict(self._last_at),
                "suppressed": dict(self._suppressed)}

    def load(self, state: Optional[Mapping[str, Any]]) -> None:
        self._history = []
        self._last_at = {}
        self._suppressed = getattr(self, "_suppressed", {})
        self._suppressed = {}
        if not isinstance(state, Mapping):
            return
        history = state.get("history")
        if isinstance(history, (list, tuple)):
            self._history = [dict(row) for row in history if isinstance(row, Mapping)][
                -self._config.alert_max_history:]
        last_at = state.get("last_at")
        if isinstance(last_at, Mapping):
            self._last_at = {str(k): float(v) for k, v in last_at.items()
                             if isinstance(v, (int, float))}
        suppressed = state.get("suppressed")
        if isinstance(suppressed, Mapping):
            self._suppressed = {str(k): int(v) for k, v in suppressed.items()
                                if isinstance(v, int)}

    def _save(self) -> None:
        if self._persist is None:
            return
        try:
            self._persist(self.snapshot())
        except Exception:  # noqa: BLE001 - alert bookkeeping must never break dispatch
            pass
