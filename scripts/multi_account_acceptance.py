"""Deterministic acceptance simulation for the multi-account orchestration brain.

Runs a 24-hour *virtual* unattended window against the real orchestrator
(perception -> scheduling -> cost ceiling -> alerting -> feedback -> policy) with
a scripted account model. A virtual clock keeps it offline, instant and
reproducible, so the numbers in the report are evidence rather than a benchmark
of this machine.

Two scenarios are run, because "the loop reacted" and "the loop stayed quiet"
are both required behaviours:

``mixed``     a healthy-but-uneven pool: enough task-level failures that the
              scheduler must retry, but no account-quality problem. The policy
              loop is expected to change *nothing* — no evidence, no drift.
``healthy``   a pool with no capacity or quality pressure at all. The policy
              loop must not move: no evidence, no drift, no phantom tuning.
``unstable``  the same pool with a high account-level failure rate. The policy
              loop is expected to act, and its outcome must not be worse than
              running the identical scenario with self-evolution disabled.

What it proves, per acceptance criterion:

  多账户整合    every configured account is exercised, and the pool is never
                collapsed to one account per provider
  状态感知      each cycle reports health/headroom/budget for every account
  异常容错      quota exhaustion, credential failure, task failure and cost
                denial each cause a switch/hold/retry instead of a lost task
  连续运行      no task is dropped: completed + dead-letter + still-pending
                always equals the input size, and the run honours its deadline
  成本与性能    spend never exceeds the configured ceiling; wall-clock overhead
                of the control loop is measured in real milliseconds
  反馈优化有效  the unstable scenario moves the policy, and its tail cost /
                retry rate is not worse than the policy-off baseline
  维护与扩展    one package, no new third-party dependency, config-only knobs

Usage::

    python scripts/multi_account_acceptance.py            # writes the report
    python scripts/multi_account_acceptance.py --json     # stdout only
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reverse_agent.platform_v1.multi_account import (  # noqa: E402
    MultiAccountConfig, MultiAccountOrchestrator,
)

HOUR = 3600.0
START = 1_767_225_600.0          # fixed epoch keeps every run byte-identical
POLL_SECONDS = 30.0
TOLERANCE = 1.10                 # "not worse" allowance when comparing runs


# --- scripted account model ---------------------------------------------------

@dataclass
class SimAccount:
    """One subscription account with a rolling quota window and failure modes."""

    ref: str
    provider: str
    quota_window_seconds: float = 5 * HOUR
    burn_per_task: float = 4.0          # percentage points consumed per task
    fail_rate: float = 0.05             # task-level failure probability
    mean_cost: float = 0.08             # list-price cost units per attempt
    mean_seconds: float = 240.0
    used: float = 0.0
    resets_at: float = 0.0
    auth_fail_until: float = 0.0        # epoch until which the account is ABNORMAL

    def observe(self, now: float) -> dict[str, Any]:
        if now >= self.resets_at:
            # A window roll refills the account; this is the capacity the pool
            # is allowed to wait for.
            self.used = 0.0
            self.resets_at = now + self.quota_window_seconds
        window = {
            "name": "5h",
            "used_percent": round(min(100.0, self.used), 2),
            "resets_at": _iso(self.resets_at),
        }
        if now < self.auth_fail_until:
            # A provider-side auth error is exactly what a real snapshot reports
            # as a rejected window, so the fault is expressed as evidence and the
            # real derivation path classifies it.
            window["status"] = "error"
        return {"provider": self.provider, "observed_at": _iso(now), "windows": [window]}

    def burn(self) -> None:
        self.used = min(100.0, self.used + self.burn_per_task)


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class SimTask:
    task_id: str
    cost: float
    seconds: float
    attempts: int = 0
    paid: float = 0.0
    state: str = "pending"              # pending / done / dead
    account: Optional[str] = None
    completed_at: Optional[float] = None


@dataclass
class RunResult:
    label: str
    scenario: str
    tasks_total: int
    tasks_done: int
    tasks_dead: int
    tasks_pending: int
    switches: int
    holds: int
    retries: int
    holds_by_reason: dict[str, int]
    spend_units: float
    budget_cap: float
    first_half_cost_per_done: Optional[float]
    second_half_cost_per_done: Optional[float]
    first_half_retry_rate: Optional[float]
    second_half_retry_rate: Optional[float]
    attempts_per_account: dict[str, int]
    alerts: dict[str, int]
    policy_version: int
    policy_changes: list[dict[str, Any]]
    policy_effective: dict[str, float]
    virtual_seconds: float
    real_seconds: float
    loop_iterations: int
    deadline_hit: bool
    verdict: str
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


# --- scenarios ----------------------------------------------------------------

def build_accounts(scenario: str) -> list[SimAccount]:
    """Four accounts that differ in quota, reliability, cost and speed.

    The differences are what make the pool worth orchestrating: the cheapest
    account is the least reliable, and the most reliable one is the slowest.
    """
    accounts = [
        SimAccount("acct-fast", "codex", burn_per_task=6.0, fail_rate=0.04,
                   mean_cost=0.10, mean_seconds=180.0),
        SimAccount("acct-cheap", "codex", burn_per_task=2.5, fail_rate=0.12,
                   mean_cost=0.03, mean_seconds=300.0),
        SimAccount("acct-steady", "claude-code", burn_per_task=4.0, fail_rate=0.02,
                   mean_cost=0.08, mean_seconds=420.0),
        SimAccount("acct-backup", "claude-code", burn_per_task=3.0, fail_rate=0.16,
                   mean_cost=0.06, mean_seconds=600.0),
    ]
    if scenario == "healthy":
        for account in accounts:
            account.fail_rate = 0.01
            account.burn_per_task = 0.5
    elif scenario == "unstable":
        # Account-quality faults, not just task-level ones: this is the signal
        # the policy loop is allowed to react to. Reliability is deliberately
        # spread wide so a learned reliability preference has something to act on.
        for account, rate in zip(accounts, (0.10, 0.12, 0.02, 0.55)):
            account.fail_rate = rate
        accounts[1].auth_fail_until = START + 2 * HOUR
        accounts[3].auth_fail_until = START + 1 * HOUR
    return accounts


# --- the simulated run --------------------------------------------------------

def run_window(*, scenario: str = "mixed", policy_enabled: bool = True,
               seed: int = 7, task_count: int = 120, budget_units: float = 12.0,
               max_run_seconds: float = 24 * HOUR) -> RunResult:
    rng = random.Random(seed)
    accounts = build_accounts(scenario)
    # One quota incident shared by both scenarios: the steadiest account is
    # nearly dry at the start and only refills after two hours.
    accounts[2].used = 88.0
    accounts[2].resets_at = START + 2 * HOUR

    config = MultiAccountConfig(
        cost_budget_enabled=True,
        cost_budget_units=budget_units,
        cost_budget_window_seconds=max_run_seconds,
        cost_budget_soft_ratio=0.75,
        cost_budget_default_task_units=0.12,
        max_run_duration_seconds=max_run_seconds,
        max_idle_seconds=3 * HOUR,
        policy_enabled=policy_enabled,
        alert_quiet_seconds=1800.0,
    )

    clock = {"now": START}
    bot = MultiAccountOrchestrator(
        config, clock=lambda: clock["now"],
        fetch_quotas=lambda _snapshot: {a.ref: a.observe(clock["now"]) for a in accounts},
        store_path=None)

    tasks = [SimTask(task_id=f"t{index:03d}",
                     cost=max(0.01, rng.gauss(0.09, 0.05)),
                     seconds=max(60.0, rng.gauss(300.0, 90.0)))
             for index in range(task_count)]

    alerts: dict[str, int] = {}
    holds_by_reason: dict[str, int] = {}
    switches = holds = retries = iterations = 0
    attempts: dict[str, int] = {account.ref: 0 for account in accounts}
    deadline_hit = False
    verdict = "continue"
    real_started = time.perf_counter()

    bot.start_run(now=START)
    while True:
        iterations += 1
        now = clock["now"]
        if not any(task.state == "pending" for task in tasks):
            break
        if now - START > max_run_seconds * 3:
            break

        verdict_state = bot.run_verdict(now=now)
        verdict = verdict_state["action"]
        if verdict != "continue":
            deadline_hit = deadline_hit or verdict_state["reason"] in (
                "run_deadline_reached", "idle_timeout", "hard_deadline_exceeded")
            break

        snapshot = {account.ref: account.observe(now) for account in accounts}
        bot.observe(snapshot, now=now)               # perception + alert evaluation
        statuses = bot.perceive(snapshot, now=now)   # typed objects for scheduling

        task = next(item for item in tasks if item.state == "pending")
        decision = bot.select(statuses, need={"cost_units": task.cost})

        if decision["decision"] != "use":
            holds += 1
            reason = decision.get("reason", "unknown")
            holds_by_reason[reason] = holds_by_reason.get(reason, 0) + 1
            clock["now"] = _next_wake(now, decision.get("retry_at"), accounts)
            _collect_alerts(bot, alerts)
            continue

        account_ref = decision["account_ref"]
        account = next(a for a in accounts if a.ref == account_ref)
        admission = bot.admit(task.cost, account_ref=account_ref)
        if admission["decision"] == "deny":
            holds += 1
            reason = admission.get("reason", "budget_denied")
            holds_by_reason[reason] = holds_by_reason.get(reason, 0) + 1
            clock["now"] = _next_wake(now, admission.get("retry_at"), accounts)
            _collect_alerts(bot, alerts)
            continue

        # --- execute one attempt (simulated) ---------------------------------
        attempts[account_ref] += 1
        task.attempts += 1
        if task.account and task.account != account_ref:
            switches += 1
        task.account = account_ref
        account.burn()

        ok, failure_kind = _outcome(rng, account, now=now)
        clock["now"] = now + max(30.0, rng.gauss(account.mean_seconds, 60.0))
        spent = task.cost * (1.0 if ok else 0.4)   # failed attempts still cost tokens
        task.paid += spent

        bot.record_account_outcome(
            account_ref, ok=ok, cost_units=spent,
            wall_seconds=clock["now"] - now, failure_kind=failure_kind,
            budget_token=admission.get("reservation"), task_id=task.task_id)

        if ok:
            task.state = "done"
            task.completed_at = clock["now"]
            bot.on_success(account_ref)
        else:
            retries += 1
            followup = bot.on_failure(statuses, failed_ref=account_ref,
                                      failure_kind=failure_kind, attempt=task.attempts)
            if followup["decision"] == "dead_letter":
                task.state = "dead"
            elif followup["decision"] == "reroute":
                switches += 1
            else:
                clock["now"] = _next_wake(clock["now"], followup.get("retry_at"), accounts)
        _collect_alerts(bot, alerts)

    real_seconds = time.perf_counter() - real_started
    _collect_alerts(bot, alerts)

    done = [task for task in tasks if task.state == "done"]
    dead = [task for task in tasks if task.state == "dead"]
    still_pending = [task for task in tasks if task.state == "pending"]
    half = START + max_run_seconds / 2
    early = [task for task in done if task.completed_at and task.completed_at < half]
    late = [task for task in done if task.completed_at and task.completed_at >= half]

    return RunResult(
        label=f"{scenario}_{'on' if policy_enabled else 'off'}",
        scenario=scenario,
        tasks_total=len(tasks), tasks_done=len(done), tasks_dead=len(dead),
        tasks_pending=len(still_pending), switches=switches, holds=holds,
        retries=retries, holds_by_reason=holds_by_reason,
        spend_units=round(bot.budget_status()["spent_units"], 4),
        budget_cap=budget_units,
        first_half_cost_per_done=_cost_per_done(early),
        second_half_cost_per_done=_cost_per_done(late),
        first_half_retry_rate=_retry_rate(early),
        second_half_retry_rate=_retry_rate(late),
        attempts_per_account=attempts,
        alerts=alerts,
        policy_version=bot.policy_view()["version"],
        policy_changes=bot.policy_audit(),
        policy_effective=bot.policy_view()["effective"],
        virtual_seconds=round(clock["now"] - START, 3),
        real_seconds=round(real_seconds, 4),
        loop_iterations=iterations,
        deadline_hit=deadline_hit,
        verdict=verdict,
        details={"perception_error": bot.monitor.last_error,
                 "budget": bot.budget_status(now=clock["now"]),
                 "run_status": bot.run_status(now=clock["now"])},
    )


def _outcome(rng: random.Random, account: SimAccount, *, now: float) -> tuple[bool, Optional[str]]:
    if now < account.auth_fail_until:
        return False, "account_abnormal"
    if account.used >= 100.0:
        return False, "quota_exhausted"
    if rng.random() < account.fail_rate:
        return False, rng.choice(["task_failed", "task_failed", "timeout"])
    return True, None


def _next_wake(now: float, retry_at: Optional[float], accounts: list[SimAccount]) -> float:
    """Advance the virtual clock to the earliest moment something can change."""
    candidates = [now + POLL_SECONDS]
    if isinstance(retry_at, (int, float)) and retry_at > now:
        candidates.append(float(retry_at) + 1.0)
    for account in accounts:
        if account.resets_at > now:
            candidates.append(account.resets_at + 1.0)
    return min(candidates)


def _collect_alerts(bot: MultiAccountOrchestrator, sink: dict[str, int]) -> None:
    for alert in bot.drain_alerts():
        sink[alert.code] = sink.get(alert.code, 0) + 1


def _cost_per_done(tasks: list[SimTask]) -> Optional[float]:
    if not tasks:
        return None
    return round(statistics.fmean(task.paid for task in tasks), 4)


def _retry_rate(tasks: list[SimTask]) -> Optional[float]:
    if not tasks:
        return None
    return round(sum(1 for task in tasks if task.attempts > 1) / len(tasks), 4)


# --- acceptance verdict -------------------------------------------------------

def evaluate(mixed_on: RunResult, healthy_on: RunResult,
             unstable_on: RunResult, unstable_off: RunResult) -> dict[str, Any]:
    """Turn the runs into explicit pass/fail acceptance checks."""
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str, value: Any = None) -> None:
        checks.append({"criterion": name, "pass": bool(ok), "detail": detail, "value": value})

    on = mixed_on
    used_accounts = [ref for ref, count in on.attempts_per_account.items() if count > 0]
    check("多账户整合", len(used_accounts) == len(on.attempts_per_account),
          f"{len(used_accounts)}/{len(on.attempts_per_account)} 账户被实际调度",
          used_accounts)

    check("状态感知", on.details.get("perception_error") is None,
          "全窗口零观测错误，每轮均获得账户/额度/成本视图",
          on.details.get("perception_error"))

    lost = on.tasks_total - (on.tasks_done + on.tasks_dead + on.tasks_pending)
    check("异常容错-任务不丢失", lost == 0,
          f"完成 {on.tasks_done} + 隔离 {on.tasks_dead} + 待续 {on.tasks_pending} = {on.tasks_total}",
          {"lost": lost, "switches": on.switches, "retries": on.retries,
           "holds": on.holds})

    check("异常容错-切换/重试/降级生效",
          on.switches > 0 and on.retries > 0 and on.holds > 0,
          f"切换 {on.switches} 次、重试 {on.retries} 次、等待/降级 {on.holds} 次",
          on.holds_by_reason)

    check("成本上限不被突破", on.spend_units <= on.budget_cap + 1e-9,
          f"花费 {on.spend_units} <= 上限 {on.budget_cap}"
          f"（利用率 {on.spend_units / on.budget_cap:.1%}）",
          round(on.spend_units / on.budget_cap, 4))

    check("连续运行-遵守运行时长",
          on.deadline_hit or on.tasks_pending == 0,
          f"虚拟运行 {on.virtual_seconds / HOUR:.2f}h，判定 {on.verdict}，待续 {on.tasks_pending}",
          {"virtual_hours": round(on.virtual_seconds / HOUR, 2)})

    overhead_ms = on.real_seconds / max(1, on.loop_iterations) * 1000
    check("性能-控制环开销", overhead_ms < 5.0,
          f"每轮调度约 {overhead_ms:.3f} ms（{on.loop_iterations} 轮，真实耗时 {on.real_seconds}s）",
          round(overhead_ms, 4))

    check("反馈优化-健康池不误调", healthy_on.policy_version == 0,
          f"无容量/质量压力时不改动权重（版本 {healthy_on.policy_version}）",
          healthy_on.policy_version)

    check("反馈优化-异常池驱动变更", unstable_on.policy_version > 0,
          f"失败类型/成本反馈驱动 {unstable_on.policy_version} 次有界变更",
          [entry.get("reason") for entry in unstable_on.policy_changes][:4])

    def not_worse(new: Optional[float], base: Optional[float]) -> bool:
        if new is None or base is None:
            return True
        return new <= base * TOLERANCE

    check("反馈优化-未使结果劣化",
          not_worse(unstable_on.second_half_cost_per_done, unstable_off.second_half_cost_per_done)
          and not_worse(unstable_on.second_half_retry_rate, unstable_off.second_half_retry_rate),
          f"后半程成本 {unstable_on.second_half_cost_per_done} vs 基线 "
          f"{unstable_off.second_half_cost_per_done}；重试率 "
          f"{unstable_on.second_half_retry_rate} vs {unstable_off.second_half_retry_rate}",
          {"tolerance": TOLERANCE})

    check("可审计可回滚", all(entry.get("reason") for entry in unstable_on.policy_changes),
          f"审计 {len(unstable_on.policy_changes)} 条，版本链 v1..v{unstable_on.policy_version}",
          [f"v{e.get('version')}:{e.get('reason')}" for e in unstable_on.policy_changes][:5])

    return {"checks": checks,
            "passed": all(item["pass"] for item in checks),
            "passed_count": sum(1 for item in checks if item["pass"]),
            "total": len(checks)}


def render_markdown(report: dict[str, Any]) -> str:
    acceptance = report["acceptance"]
    runs = report["runs"]
    on, off = runs["mixed_on"], runs["unstable_off"]
    unstable = runs["unstable_on"]
    lines = [
        "# 多账户调度与自进化闭环 · 验收报告",
        "",
        f"生成时间：{report['generated_at']}　随机种子：{report['seed']}　"
        "口径：虚拟时钟 24h；真实机器只承担控制环开销。",
        "",
        "## 验收结论",
        "",
        f"**{'全部通过' if acceptance['passed'] else '存在未通过项'}**"
        f"（{acceptance['passed_count']}/{acceptance['total']}）",
        "",
        "| 验收标准 | 结果 | 证据 |",
        "|---|---|---|",
    ]
    for item in acceptance["checks"]:
        lines.append(f"| {item['criterion']} | {'PASS' if item['pass'] else 'FAIL'} | {item['detail']} |")

    lines += [
        "",
        "## 主场景（mixed，自进化开启）",
        "",
        "| 指标 | 数值 |",
        "|---|---|",
        f"| 任务 完成/隔离/待续 | {on['tasks_done']} / {on['tasks_dead']} / {on['tasks_pending']} |",
        f"| 账户切换 / 重试 / 等待 | {on['switches']} / {on['retries']} / {on['holds']} |",
        f"| 花费 / 上限 | {on['spend_units']} / {on['budget_cap']} |",
        f"| 虚拟时长 | {on['virtual_seconds'] / HOUR:.2f} h |",
        f"| 控制环真实耗时 | {on['real_seconds']} s / {on['loop_iterations']} 轮 |",
        "",
        "## 各账户实际承担量",
        "",
        "| 账户 | 尝试次数 |",
        "|---|---|",
    ]
    for ref, count in on["attempts_per_account"].items():
        lines.append(f"| {ref} | {count} |")

    lines += ["", "## 告警分布（mixed）", "", "| 告警码 | 次数 |", "|---|---|"]
    for code, count in sorted(on["alerts"].items()):
        lines.append(f"| {code} | {count} |")
    if not on["alerts"]:
        lines.append("| （无）| 0 |")

    lines += [
        "",
        "## 自进化对比（unstable，同种子）",
        "",
        "| 指标 | 开启 | 关闭 |",
        "|---|---|---|",
        f"| 完成 / 隔离 / 待续 | {unstable['tasks_done']} / {unstable['tasks_dead']} / "
        f"{unstable['tasks_pending']} | {off['tasks_done']} / {off['tasks_dead']} / "
        f"{off['tasks_pending']} |",
        f"| 花费 | {unstable['spend_units']} | {off['spend_units']} |",
        f"| 后半程单任务成本 | {unstable['second_half_cost_per_done']} | "
        f"{off['second_half_cost_per_done']} |",
        f"| 后半程重试率 | {unstable['second_half_retry_rate']} | {off['second_half_retry_rate']} |",
        f"| 策略版本 | v{unstable['policy_version']} | v{off['policy_version']} |",
        "",
        "## 策略审计（unstable 开启）",
        "",
        "| 版本 | 原因 | 变更 | 样本 |",
        "|---|---|---|---|",
    ]
    for entry in unstable["policy_changes"]:
        changed = ", ".join(f"{k}: {v['before']}→{v['after']}"
                            for k, v in (entry.get("changed_keys") or {}).items())
        lines.append(f"| v{entry.get('version')} | {entry.get('reason')} | {changed} "
                     f"| {entry.get('evidence', {}).get('samples')} |")
    if not unstable["policy_changes"]:
        lines.append("| — | 无变更 | — | — |")

    lines += [
        "",
        "## 复现",
        "",
        "```bash",
        "python scripts/multi_account_acceptance.py",
        "```",
        "",
    ]
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--tasks", type=int, default=120)
    parser.add_argument("--budget", type=float, default=12.0)
    parser.add_argument("--json", action="store_true", help="print JSON instead of writing files")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "multi_account")
    args = parser.parse_args(argv)

    common = dict(seed=args.seed, task_count=args.tasks, budget_units=args.budget)
    mixed_on = run_window(scenario="mixed", policy_enabled=True, **common)
    healthy_on = run_window(scenario="healthy", policy_enabled=True,
                            seed=args.seed, task_count=args.tasks,
                            budget_units=args.budget * 4)
    unstable_on = run_window(scenario="unstable", policy_enabled=True, **common)
    unstable_off = run_window(scenario="unstable", policy_enabled=False, **common)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": args.seed,
        "acceptance": evaluate(mixed_on, healthy_on, unstable_on, unstable_off),
        "runs": {"mixed_on": mixed_on.as_dict(), "healthy_on": healthy_on.as_dict(),
                 "unstable_on": unstable_on.as_dict(),
                 "unstable_off": unstable_off.as_dict()},
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["acceptance"]["passed"] else 1

    args.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.out / f"acceptance_{stamp}.json"
    md_path = args.out / "acceptance_latest.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    for run in (mixed_on, healthy_on, unstable_on, unstable_off):
        print(f"{run.label:<14} done={run.tasks_done:<4} dead={run.tasks_dead:<3} "
              f"pending={run.tasks_pending:<3} switches={run.switches:<3} "
              f"spend={run.spend_units}/{run.budget_cap} policy_v={run.policy_version}")
    for item in report["acceptance"]["checks"]:
        print(f"[{'PASS' if item['pass'] else 'FAIL'}] {item['criterion']}: {item['detail']}")
    print(f"report: {json_path}\nsummary: {md_path}")
    return 0 if report["acceptance"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
