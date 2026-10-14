import { Gauge } from "lucide-react";
import { useResources } from "@/hooks/use-model-access";
import { cn } from "@/lib/cn";
import {
  totalTokens,
  type EquivalentCost,
  type Quota,
  type QuotaWindow,
  type Resource,
  type TokenCounters,
} from "@/lib/resources";

const compact = new Intl.NumberFormat("zh-CN", { notation: "compact", maximumFractionDigits: 1 });
const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 });

const WINDOW_LABELS: Record<string, string> = {
  five_hour: "5 小时窗口",
  weekly: "每周窗口",
  seven_day_opus: "每周窗口（Opus）",
  seven_day_sonnet: "每周窗口（Sonnet）",
};

const QUOTA_REASONS: Record<string, string> = {
  api_key_has_no_subscription_window: "API Key 按量计费，没有订阅额度窗口",
  no_claude_rate_limit_observed_yet: "尚未观察到额度：用该账号运行一次任务后显示",
  codex_sessions_not_found: "未找到 Codex 会话记录",
  no_recent_codex_rate_limits: "最近 8 天的 Codex 会话记录中没有额度信息",
};

const OWNER_LABELS: Record<string, string> = {
  nerelan: "API Key · Nerelan 保管",
  "codex-cli": "订阅 · Codex CLI 登录",
  "claude-code-cli": "订阅 · Claude Code 登录",
  external_cli: "订阅 · 外部 CLI 登录",
  none: "无需凭据",
};

function formatReset(iso: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function costText(cost: EquivalentCost | null): string {
  if (!cost || cost.state === "UNKNOWN" || cost.usd === null) return "未知";
  return `${usd.format(cost.usd)}${cost.state === "PARTIAL" ? "（部分）" : ""}`;
}

function QuotaWindowRow({ window }: { window: QuotaWindow }) {
  const label = WINDOW_LABELS[window.window] ?? window.window;
  const reset = formatReset(window.resetsAt);
  const used = window.resetPassed ? null : window.usedPercent;
  return (
    <div data-testid={`quota-window-${window.window}`}>
      <div className="flex items-baseline justify-between gap-2 text-xs">
        <span className="font-medium text-ra-text">{label}</span>
        <span className="text-ra-text-secondary">
          {window.resetPassed ? "已过重置时间，当前用量未知" : used === null ? "用量未知" : `已用 ${Math.round(used)}%`}
        </span>
      </div>
      <div
        className="mt-1 h-1.5 overflow-hidden rounded-full bg-ra-tertiary"
        role="meter"
        aria-label={`${label}已用比例`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={used ?? undefined}
      >
        {used !== null && (
          <div
            className={cn(
              "h-full rounded-full",
              used >= 95 ? "bg-ra-status-error" : used >= 80 ? "bg-ra-status-warning" : "bg-ra-accent",
            )}
            style={{ width: `${Math.max(used, 1)}%` }}
          />
        )}
      </div>
      {reset && !window.resetPassed && (
        <p className="mt-0.5 text-[11px] text-ra-text-tertiary">{reset} 重置</p>
      )}
    </div>
  );
}

function QuotaBlock({ quota }: { quota: Quota }) {
  if (quota.state !== "OBSERVED" || quota.windows.length === 0) {
    return (
      <p className="text-xs text-ra-text-tertiary" data-testid="quota-unknown">
        额度：{QUOTA_REASONS[quota.reason ?? ""] ?? "未知（没有官方来源）"}
      </p>
    );
  }
  const source = quota.source === "codex_session_log" ? "Codex 会话记录" : "Claude Code 运行时通知";
  return (
    <div className="flex flex-col gap-2" data-testid="quota-observed">
      {quota.windows.map((window) => (
        <QuotaWindowRow key={window.window} window={window} />
      ))}
      <p className="text-[11px] text-ra-text-tertiary">
        来源：{source}
        {quota.plan ? ` · 计划 ${quota.plan}` : ""}
        {formatReset(quota.observedAt) ? ` · 记录于 ${formatReset(quota.observedAt)}` : ""}
      </p>
    </div>
  );
}

function TokenLine({ tokens }: { tokens: TokenCounters }) {
  return (
    <dl className="grid grid-cols-4 gap-1 text-[11px]">
      {([
        ["输入", tokens.input],
        ["缓存读取", tokens.cacheRead],
        ["缓存写入", tokens.cacheWrite],
        ["输出", tokens.output],
      ] as const).map(([label, value]) => (
        <div key={label}>
          <dt className="text-ra-text-tertiary">{label}</dt>
          <dd className="font-medium tabular-nums text-ra-text">{compact.format(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function ResourceCard({ resource }: { resource: Resource }) {
  const used = resource.bindings.filter((b) => b.tokens && b.tokens.input + b.tokens.output > 0);
  return (
    <article
      data-testid={`resource-${resource.connectionId}`}
      className="flex flex-col gap-3 rounded-xl border border-ra-border/60 p-3"
    >
      <header className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-medium text-ra-text">{resource.name}</h3>
          <p className="text-[11px] text-ra-text-tertiary">
            {OWNER_LABELS[resource.credentialOwner] ?? resource.credentialOwner}
            {!resource.credentialConfigured && <span className="text-ra-status-warning"> · 未就绪</span>}
          </p>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-sm font-medium tabular-nums text-ra-text" data-testid="resource-cost">
            {costText(resource.equivalentCost)}
          </p>
          <p className="text-[11px] text-ra-text-tertiary">等价 API 成本</p>
        </div>
      </header>
      <QuotaBlock quota={resource.quota} />
      {resource.tasksWithTokens > 0 ? (
        <div className="flex flex-col gap-1">
          <TokenLine tokens={resource.tokens} />
          <p className="text-[11px] text-ra-text-tertiary">来自 Nerelan 的 {resource.tasksWithTokens} 个任务</p>
        </div>
      ) : (
        <p className="text-xs text-ra-text-tertiary">Nerelan 还没有用这个连接运行过有 Token 记录的任务。</p>
      )}
      {used.length > 0 && (
        <details className="text-xs">
          <summary className="cursor-pointer text-ra-text-secondary">按模型 × 执行器（{used.length}）</summary>
          <ul className="mt-2 flex flex-col gap-1">
            {used.map((binding) => (
              <li key={binding.bindingId} className="flex items-center justify-between gap-2">
                <span className="truncate text-ra-text">
                  {binding.modelId} · {binding.executorId}
                </span>
                <span className="shrink-0 tabular-nums text-ra-text-secondary">
                  {compact.format(binding.tokens ? totalTokens(binding.tokens) : 0)} tokens ·{" "}
                  {costText(binding.equivalentCost)}
                </span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  );
}

export function ResourceOverview() {
  const query = useResources();
  const overview = query.data;
  const priceAsOf = overview?.equivalentCost?.priceAsOf;
  return (
    <section
      aria-labelledby="resource-overview-heading"
      data-testid="resource-overview"
      className="mt-6 rounded-2xl border border-ra-border/70 bg-ra-workspace p-4 sm:p-5"
    >
      <div className="flex items-start gap-2">
        <Gauge className="mt-0.5 h-4 w-4 shrink-0 text-ra-text-tertiary" aria-hidden="true" />
        <div className="min-w-0">
          <h2 id="resource-overview-heading" className="text-sm font-semibold text-ra-text">资源与用量</h2>
          <p className="mt-1 text-xs leading-5 text-ra-text-secondary">
            每个连接的订阅额度、Token 用量，以及按模型厂商官方按量价格折算的等价成本。等价成本只是估算，
            不是账单：订阅、免费网关或折扣中转的实际花费可能不同。
          </p>
        </div>
      </div>
      {query.isLoading && <p className="mt-3 text-sm text-ra-text-tertiary">正在加载…</p>}
      {query.isError && (
        <p role="alert" className="mt-3 text-sm text-ra-status-error" data-testid="resource-overview-error">
          无法读取资源：{query.error instanceof Error ? query.error.message : "操作失败"}
        </p>
      )}
      {overview && (
        <>
          <p className="mt-3 text-sm text-ra-text" data-testid="resource-summary">
            合计 {compact.format(totalTokens(overview.tokens))} tokens · 等价成本 {costText(overview.equivalentCost)}
            {priceAsOf && (
              <span className="text-xs text-ra-text-tertiary">（价格来源 models.dev，{priceAsOf}）</span>
            )}
          </p>
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            {overview.resources.map((resource) => (
              <ResourceCard key={resource.connectionId} resource={resource} />
            ))}
          </div>
        </>
      )}
    </section>
  );
}
