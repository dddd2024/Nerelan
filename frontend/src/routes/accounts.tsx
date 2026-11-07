import { AlertTriangle, CheckCircle2, Info, Users } from "lucide-react";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { PageHeader } from "@/components/page-header";
import { useAccountPool } from "@/hooks/use-platform";
import type { AccountHealth, AccountPool, PoolAccount, PoolAlert, PoolBudget, PoolPolicy } from "@/lib/platform-client";
import { cn } from "@/lib/cn";

const HEALTH: Record<AccountHealth, { label: string; dot: string; text: string }> = {
  HEALTHY: { label: "健康", dot: "bg-ra-status-success", text: "text-ra-status-success" },
  DEGRADED: { label: "余量紧张", dot: "bg-ra-status-warning", text: "text-ra-status-warning" },
  EXHAUSTED: { label: "已耗尽", dot: "bg-ra-status-error", text: "text-ra-status-error" },
  ABNORMAL: { label: "异常", dot: "bg-ra-status-error", text: "text-ra-status-error" },
  STALE: { label: "数据过期", dot: "bg-ra-text-tertiary", text: "text-ra-text-tertiary" },
  UNKNOWN: { label: "未知", dot: "bg-ra-text-tertiary", text: "text-ra-text-tertiary" },
};

const SOURCE_LABEL: Record<string, string> = {
  magpie: "数据来自 Magpie",
  observations: "数据来自本地额度观测",
  unavailable: "账户状态暂时无法读取",
  none: "尚未接入账户",
};

function sourceLabel(pool: AccountPool) {
  if (pool.source === "unavailable" && pool.accounts.length > 0) {
    return "账户状态暂时无法读取，显示最近一次结果";
  }
  return SOURCE_LABEL[pool.source] ?? pool.source;
}

function signedPercent(value: number) {
  const rounded = Math.round(value * 100);
  return `${rounded > 0 ? "+" : rounded < 0 ? "−" : "±"}${Math.abs(rounded)}%`;
}

function untilLabel(epochSeconds: number | null | undefined, now: number) {
  if (!epochSeconds) return "—";
  const minutes = Math.round((epochSeconds * 1000 - now) / 60_000);
  if (minutes <= 0) return "即将";
  if (minutes < 60) return `${minutes} 分钟后`;
  if (minutes < 1440) return `${Math.round(minutes / 60)} 小时后`;
  return `${Math.round(minutes / 1440)} 天后`;
}

function Stat({ label, value, hint, testId }: { label: string; value: string; hint?: string; testId: string }) {
  return (
    <div className="min-w-0 rounded-lg border border-ra-border bg-ra-light px-3.5 py-3">
      <p className="text-xs text-ra-text-tertiary">{label}</p>
      <p data-testid={testId} className="mt-1 text-xl font-medium tabular-nums text-ra-text">{value}</p>
      {hint ? <p className="mt-0.5 truncate text-[11px] text-ra-text-tertiary">{hint}</p> : null}
    </div>
  );
}

function AlertRow({ alert }: { alert: PoolAlert }) {
  const Icon = alert.severity === "info" ? Info : AlertTriangle;
  return (
    <li
      data-testid={`pool-alert-${alert.code}`}
      data-severity={alert.severity}
      className="flex items-start gap-2.5 px-3.5 py-2.5 text-sm"
    >
      <Icon
        aria-hidden="true"
        className={cn(
          "mt-0.5 h-4 w-4 shrink-0",
          alert.severity === "critical" && "text-ra-status-error",
          alert.severity === "warning" && "text-ra-status-warning",
          alert.severity === "info" && "text-ra-text-tertiary",
        )}
      />
      <span className="min-w-0 flex-1 text-ra-text">{alert.detail}</span>
      <span className="shrink-0 text-[11px] text-ra-text-tertiary">{alert.code}</span>
    </li>
  );
}

function Headroom({ value }: { value: number | null }) {
  if (value === null) return <span className="text-ra-text-tertiary">未知</span>;
  return (
    <span className="flex items-center gap-2">
      <span aria-hidden="true" className="h-1 w-16 overflow-hidden rounded-full bg-ra-tertiary">
        <span
          className={cn("block h-full", value <= 10 ? "bg-ra-status-error" : "bg-ra-accent")}
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </span>
      <span className="tabular-nums">{Math.round(value)}%</span>
    </span>
  );
}

function feedbackLabel(account: PoolAccount) {
  const score = account.score;
  if (!score || score.attempts === 0) return "暂无反馈";
  const latency = score.mean_wall_seconds === null ? "" : ` · ${score.mean_wall_seconds.toFixed(1)} 秒`;
  return `${Math.round((score.successes / score.attempts) * 100)}% 成功 · ${score.attempts} 次${latency}`;
}

function AccountRow({ account, now }: { account: PoolAccount; now: number }) {
  const health = HEALTH[account.health];
  return (
    <tr data-testid={`pool-account-${account.provider ?? account.account_ref}`} className="border-t border-ra-border">
      <td className="px-3.5 py-2.5">
        <span className="block font-medium text-ra-text">{account.provider ?? "未识别服务"}</span>
        {!account.admission_evidence ? (
          <span className="text-[11px] text-ra-text-tertiary" title="本平台没有路由认领该服务，它的额度不参与准入">
            仅观测
          </span>
        ) : null}
      </td>
      <td className="px-3.5 py-2.5">
        <span className={cn("inline-flex items-center gap-1.5", health.text)}>
          <span aria-hidden="true" className={cn("h-1.5 w-1.5 rounded-full", health.dot)} />
          {health.label}
        </span>
        {account.weekly_pace ? (
          <span
            data-testid={`pool-pace-${account.provider ?? account.account_ref}`}
            className={cn("block text-[11px]", account.weekly_pace.held_until ? "text-ra-status-warning" : "text-ra-text-tertiary")}
            title={`与 Magpie 同口径：已用比例减本周已过时间比例。超过配速线 ${Math.round(account.weekly_pace.line * 100)}% 时暂停派发`}
          >
            配速 {signedPercent(account.weekly_pace.deviation)}
            {account.weekly_pace.draining
              ? "，已宣布重置，放开使用至 3%"
              : account.weekly_pace.held_until ? `，暂停派发，预计${untilLabel(account.weekly_pace.held_until, now)}恢复` : ""}
          </span>
        ) : null}
        {account.reset_cards && account.reset_cards.count > 0 ? (
          <span data-testid={`pool-cards-${account.provider ?? account.account_ref}`} className="block text-[11px] text-ra-text-tertiary">
            重置卡 {account.reset_cards.count} 张
            {account.reset_cards.next_expires_at
              ? `，最早 ${untilLabel(Date.parse(account.reset_cards.next_expires_at) / 1000, now)}过期`
              : ""}
          </span>
        ) : null}
        {account.cooldown ? (
          <span className="block text-[11px] text-ra-status-warning">
            {account.cooldown.tier === "quarantine" ? "隔离中" : "冷却中"}，{untilLabel(account.cooldown.until, now)}恢复
          </span>
        ) : null}
      </td>
      <td className="px-3.5 py-2.5 text-ra-text-secondary"><Headroom value={account.headroom_pct} /></td>
      <td className="px-3.5 py-2.5 text-ra-text-secondary">{untilLabel(account.next_reset_at, now)}</td>
      <td className="px-3.5 py-2.5 text-ra-text-secondary">{feedbackLabel(account)}</td>
    </tr>
  );
}

function budgetLine(label: string, limit: number | null | undefined, remaining: number | null | undefined,
                    format: (value: number) => string) {
  if (!limit) return `${label}：未设上限`;
  return `${label}：剩余 ${format(remaining ?? 0)} / ${format(limit)}`;
}

function BudgetPanel({ budget }: { budget: PoolBudget | null }) {
  const money = (value: number) => (value / 1_000_000).toFixed(2);
  const tokens = (value: number) => value.toLocaleString("zh-CN");
  return (
    <section aria-label="窗口预算" className="rounded-lg border border-ra-border px-3.5 py-3 text-sm">
      <h2 className="mb-1.5 text-xs font-medium text-ra-text-tertiary">当前窗口预算</h2>
      {budget ? (
        <>
          <p data-testid="pool-budget-cost" className="text-ra-text-secondary">
            {budgetLine("成本", budget.max_cost_micro_units, budget.remaining_cost_micro_units, money)}
          </p>
          <p className="text-ra-text-secondary">
            {budgetLine("Token", budget.max_token_units, budget.remaining_token_units, tokens)}
          </p>
        </>
      ) : (
        <p className="text-ra-text-tertiary">没有激活的自治窗口。</p>
      )}
    </section>
  );
}

function PolicyPanel({ policy }: { policy: PoolPolicy }) {
  const weights = policy.effective;
  return (
    <section aria-label="调度策略" className="rounded-lg border border-ra-border px-3.5 py-3 text-sm">
      <h2 className="mb-1.5 text-xs font-medium text-ra-text-tertiary">调度策略</h2>
      <p data-testid="pool-policy-state" className="text-ra-text-secondary">
        自进化{policy.enabled ? "已开启" : "未开启"} · 版本 {policy.revision ?? 0}
      </p>
      {weights ? (
        <p className="text-ra-text-secondary">
          权重：可靠性 {weights.reliability_weight.toFixed(2)} · 成本 {weights.cost_weight.toFixed(2)} · 时延{" "}
          {weights.latency_weight.toFixed(2)}
        </p>
      ) : null}
      <p className="mt-1 text-[11px] text-ra-text-tertiary">回滚需在宿主停止后通过命令行执行，不在浏览器中提供。</p>
    </section>
  );
}

/** Read-only operations view of the account pool. Nothing here changes routing. */
export function AccountsPage() {
  const query = useAccountPool();
  const pool = query.data;
  const now = Date.now();

  return (
    <main data-testid="accounts-page" className="h-full overflow-auto bg-ra-workspace px-4 py-5 lg:px-7 lg:py-7">
      <div className="mx-auto flex max-w-5xl flex-col gap-4">
        <PageHeader
          title="账户"
          icon={Users}
          description={pool ? sourceLabel(pool) : "所有额度账户的状态、余量与运行反馈。"}
        />

        {query.isPending ? <LoadingState label="正在读取账户状态…" /> : null}
        {query.isError ? (
          <ErrorState
            title={pool ? "账户状态更新失败，显示上次内容" : "账户状态读取失败"}
            error={query.error}
            onRetry={() => void query.refetch()}
          />
        ) : null}

        {pool ? (
          <>
            <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
              <Stat
                testId="pool-dispatchable"
                label="可派发账户"
                value={pool.summary ? `${pool.summary.dispatchable_accounts} / ${pool.summary.total_accounts}` : "—"}
                hint={pool.summary?.cooling_accounts ? `${pool.summary.cooling_accounts} 个冷却中` : undefined}
              />
              <Stat
                testId="pool-alert-count"
                label="活动告警"
                value={String(pool.alerts.active.length)}
                hint={pool.monitoring ? "持续监控中" : "监控线程未运行"}
              />
              <Stat
                testId="pool-best-headroom"
                label="最大余量"
                value={pool.summary?.best_headroom_pct == null ? "未知" : `${Math.round(pool.summary.best_headroom_pct)}%`}
              />
              <Stat
                testId="pool-next-capacity"
                label="最早恢复"
                value={untilLabel(pool.summary?.earliest_capacity_at, now)}
              />
            </div>

            {pool.codex_reset ? (
              <p data-testid="pool-codex-reset" className="rounded-lg border border-ra-border bg-ra-light px-3.5 py-2.5 text-sm text-ra-text">
                {pool.codex_reset.state === "PLAN_ONLY"
                  ? `Codex 已宣布提前重置：${pool.codex_reset.expected_reset_at ? new Date(pool.codex_reset.expected_reset_at).toLocaleString("zh-CN") : "近期"}前放开使用，保留 3%。`
                  : "Codex 已报告完成重置，正在重新读取额度。"}
                {pool.codex_reset.source_url ? (
                  <a href={pool.codex_reset.source_url} target="_blank" rel="noreferrer" className="ml-2 text-ra-accent hover:underline">公告</a>
                ) : null}
              </p>
            ) : null}

            <section aria-label="活动告警" className="rounded-lg border border-ra-border">
              {pool.alerts.active.length > 0 ? (
                <ul className="divide-y divide-ra-border">
                  {pool.alerts.active.map((alert) => (
                    <AlertRow key={`${alert.code}:${alert.subject}`} alert={alert} />
                  ))}
                </ul>
              ) : (
                <p data-testid="pool-no-alerts" className="flex items-center gap-2 px-3.5 py-2.5 text-sm text-ra-text-secondary">
                  <CheckCircle2 className="h-4 w-4 text-ra-status-success" aria-hidden="true" />
                  没有活动告警
                </p>
              )}
            </section>

            <section aria-label="账户列表" className="overflow-x-auto rounded-lg border border-ra-border custom-scrollbar">
              <table className="w-full min-w-[640px] text-left text-[13px]">
                <thead className="text-xs text-ra-text-tertiary">
                  <tr>
                    <th scope="col" className="px-3.5 py-2 font-normal">服务</th>
                    <th scope="col" className="px-3.5 py-2 font-normal">状态</th>
                    <th scope="col" className="px-3.5 py-2 font-normal">余量</th>
                    <th scope="col" className="px-3.5 py-2 font-normal">下次重置</th>
                    <th scope="col" className="px-3.5 py-2 font-normal">运行反馈</th>
                  </tr>
                </thead>
                <tbody>
                  {pool.accounts.map((account) => (
                    <AccountRow key={account.account_ref} account={account} now={now} />
                  ))}
                  {pool.accounts.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="border-t border-ra-border px-3.5 py-6 text-center text-sm text-ra-text-tertiary">
                        还没有账户。请在设置中接入 Magpie 或添加连接。
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </section>

            <div className="grid gap-2.5 md:grid-cols-2">
              <BudgetPanel budget={pool.budget} />
              <PolicyPanel policy={pool.policy} />
            </div>
          </>
        ) : null}
      </div>
    </main>
  );
}
