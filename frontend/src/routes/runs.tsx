import { useState } from "react";
import {
  Activity,
  ChevronDown,
  ChevronRight,
  Clock3,
  FileCode2,
  GitPullRequest,
  PlayCircle,
  RefreshCw,
  UserRound,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchRun,
  fetchRuns,
  type PlatformAgentRun,
  type PlatformAgentRunDetail,
  type PlatformRunActivityEvent,
  type PlatformRunAgent,
} from "@/lib/platform-client";
import { cn } from "@/lib/cn";

const STATE_STYLES: Record<string, string> = {
  READY_FOR_HUMAN: "bg-emerald-400/10 text-emerald-300",
  RUNNING: "bg-sky-400/10 text-sky-300",
  BLOCKED_EXTERNAL: "bg-amber-300/10 text-amber-200",
  FAILED_TERMINAL: "bg-red-400/10 text-red-300",
  WAITING_FOR_OWNER: "bg-ra-light text-ra-text-secondary",
};

const STATE_LABELS: Record<string, string> = {
  READY_FOR_HUMAN: "等待人工审查",
  RUNNING: "运行中",
  BLOCKED_EXTERNAL: "外部受阻",
  FAILED_TERMINAL: "终态失败",
  WAITING_FOR_OWNER: "等待派发",
};

const STAGE_LABELS: Record<string, string> = {
  PLAN: "计划",
  PREPARE: "准备",
  EXECUTE: "执行",
  VERIFY: "验证",
  REVIEW: "审查",
  RECOVERY: "恢复",
  PUBLISH: "发布",
  COMPLETE: "完成",
  TERMINAL: "终态",
  UNKNOWN: "未知阶段",
};

const LIVENESS_LABELS: Record<string, string> = {
  ACTIVE: "活跃",
  WAITING: "等待中",
  VALIDATING: "验证中",
  BLOCKED: "已阻塞",
  OWNER_ACTION_REQUIRED: "需要 Owner 处理",
  STALE: "疑似停滞",
  TERMINAL: "已结束",
  UNKNOWN: "未知",
};

const LIVENESS_STYLES: Record<string, string> = {
  ACTIVE: "bg-emerald-400/10 text-emerald-300",
  WAITING: "bg-violet-400/10 text-violet-200",
  VALIDATING: "bg-sky-400/10 text-sky-300",
  BLOCKED: "bg-amber-300/10 text-amber-200",
  OWNER_ACTION_REQUIRED: "bg-amber-300/10 text-amber-200",
  STALE: "bg-red-400/10 text-red-300",
  TERMINAL: "bg-ra-light text-ra-text-secondary",
  UNKNOWN: "bg-ra-light text-ra-text-tertiary",
};

const ENFORCEMENT_LABELS: Record<string, string> = {
  HARD_ADMISSION_ENFORCED: "派发前硬预算",
  POST_RUN_OBSERVED: "仅运行后观测",
  USAGE_UNKNOWN: "用量未知，已停派发",
};

const CATEGORY_LABELS: Record<string, string> = {
  PLAN: "计划",
  READ: "读取",
  SEARCH: "搜索",
  EDIT: "编辑",
  COMMAND: "命令",
  TEST: "测试",
  VERIFY: "验证",
  AGENT_STARTED: "Agent 开始",
  AGENT_WAITING: "Agent 等待",
  AGENT_COMPLETED: "Agent 完成",
  CHECKPOINT: "检查点",
  RECOVERY: "恢复",
  BLOCKED: "阻塞",
  OWNER_ACTION_REQUIRED: "需要 Owner 处理",
  PUBLICATION: "发布",
};

function formatUnits(value: number) {
  return new Intl.NumberFormat("zh-CN").format(value);
}

function formatCost(microUnits: number) {
  return `$${(microUnits / 1_000_000).toFixed(4)}`;
}

function relativeTime(value: string) {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return "时间未知";
  const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
  if (seconds < 60) return "刚刚";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  return `${Math.floor(seconds / 86400)} 天前`;
}

function enumKey(value: string | undefined) {
  return String(value ?? "UNKNOWN").toUpperCase();
}

function stageLabel(value: string | undefined) {
  return STAGE_LABELS[enumKey(value)] ?? STAGE_LABELS.UNKNOWN;
}

function livenessLabel(value: string | undefined) {
  return LIVENESS_LABELS[enumKey(value)] ?? LIVENESS_LABELS.UNKNOWN;
}

function livenessKey(value: PlatformAgentRun["liveness"]) {
  if (value && typeof value === "object") return enumKey(value.state);
  return enumKey(value);
}

function lastActivityAt(run: PlatformAgentRun) {
  if (run.last_activity_at) return run.last_activity_at;
  if (run.liveness_detail?.last_activity_at) return run.liveness_detail.last_activity_at;
  if (run.liveness && typeof run.liveness === "object") return run.liveness.last_activity_at;
  return "";
}

function categoryLabel(value: string | undefined) {
  return CATEGORY_LABELS[enumKey(value)] ?? "活动";
}

function agentLabel(agent?: PlatformRunAgent | null) {
  if (!agent) return "未分配 Agent";
  return agent.display_name || agent.role || agent.agent_id || "未命名 Agent";
}

function eventAgent(event?: { agent?: PlatformRunAgent | null; agent_id?: string; role?: string } | null): PlatformRunAgent | null {
  if (!event) return null;
  if (event.agent) return event.agent;
  if (!event.agent_id && !event.role) return null;
  return { agent_id: event.agent_id ?? "", role: event.role ?? "" };
}

function categoryClass(value: string | undefined) {
  const key = enumKey(value);
  if (key === "BLOCKED" || key === "OWNER_ACTION_REQUIRED") return "text-amber-200";
  if (key === "VERIFY" || key === "TEST" || key === "CHECKPOINT") return "text-emerald-300";
  if (key === "AGENT_STARTED" || key === "COMMAND") return "text-sky-300";
  return "text-ra-text-tertiary";
}

function ActivityRow({ event }: { event: PlatformRunActivityEvent }) {
  const agent = eventAgent(event);
  return (
    <li
      className="flex min-w-0 gap-3 border-b border-ra-border/60 py-3 last:border-b-0"
      data-testid={`run-activity-${event.id}`}
    >
      <span className={cn("mt-1 h-2 w-2 shrink-0 rounded-full bg-current", categoryClass(event.category))} aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
          <p className="min-w-0 text-sm font-medium text-ra-text">{event.title || categoryLabel(event.category)}</p>
          <span className="shrink-0 text-[11px] text-ra-text-tertiary">{relativeTime(event.timestamp)}</span>
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-ra-text-secondary">
          <span className="rounded-full bg-ra-light px-2 py-0.5">{categoryLabel(event.category)}</span>
          {agent ? <span>{agentLabel(agent)}</span> : null}
          {event.stage ? <span>{stageLabel(event.stage)}</span> : null}
        </div>
        {event.description ? <p className="mt-1 text-xs leading-5 text-ra-text-tertiary">{event.description}</p> : null}
        {event.path ? <p className="mt-1 truncate font-mono text-xs text-ra-text-secondary" title={event.path}>{event.path}</p> : null}
        {event.command && !event.test ? <p className="mt-1 truncate font-mono text-xs text-ra-text-secondary" title={event.command.summary}>{event.command.summary || "命令"} · {event.command.status || event.status || "UNKNOWN"}</p> : null}
        {event.test ? <p className="mt-1 text-xs text-ra-text-secondary">{event.test.summary || "测试"} · {event.test.status || (event.test.exit_code === 0 ? "PASS" : event.test.exit_code == null ? "UNKNOWN" : "FAIL")}</p> : null}
      </div>
    </li>
  );
}

function RunDetail({ run, open }: { run: PlatformAgentRun; open: boolean }) {
  const detailQuery = useQuery<PlatformAgentRunDetail>({
    queryKey: ["run", run.task_id],
    queryFn: () => fetchRun(run.task_id),
    enabled: open,
    staleTime: 2_000,
    refetchInterval: open ? 4_000 : false,
  });

  if (!open) return null;

  return (
    <div id={`run-detail-${run.task_id}`} role="region" aria-labelledby={`run-toggle-${run.task_id}`} data-testid={`run-detail-${run.task_id}`} className="mt-4 border-t border-ra-border/70 pt-4">
      {detailQuery.isLoading ? (
        <div role="status" aria-live="polite" data-testid={`run-detail-loading-${run.task_id}`} className="rounded-xl border border-dashed border-ra-border py-8 text-center text-sm text-ra-text-tertiary">正在加载运行详情…</div>
      ) : detailQuery.isError ? (
        <div role="alert" data-testid={`run-detail-error-${run.task_id}`} className="rounded-xl border border-dashed border-ra-border py-8 text-center">
          <p className="text-sm text-ra-text-secondary">暂时无法加载运行详情。</p>
          <button type="button" onClick={() => void detailQuery.refetch()} className="mt-3 inline-flex items-center gap-2 rounded-lg border border-ra-border px-3 py-1.5 text-xs text-ra-text-secondary hover:bg-ra-light focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"><RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />重试</button>
        </div>
      ) : (
        <RunDetailContent run={detailQuery.data ?? { ...run, events: [], changed_files: [] }} />
      )}
    </div>
  );
}

function RunDetailContent({ run }: { run: PlatformAgentRunDetail }) {
  const events = run.activity ?? run.events ?? [];
  const activityTotal = run.activity_total ?? run.event_count ?? run.events?.length ?? events.length;
  const changedFiles = run.changed_files ?? [];
  const agents = run.agents ?? [];
  const currentAgent = run.current_agent ?? eventAgent(run.current_activity);
  const fileCount = run.change_summary?.file_count ?? changedFiles.length;
  const additions = run.change_summary?.additions ?? changedFiles.reduce((sum, file) => sum + file.additions, 0);
  const deletions = run.change_summary?.deletions ?? changedFiles.reduce((sum, file) => sum + file.deletions, 0);

  return (
    <div className="space-y-5">
      <section aria-labelledby={`run-overview-heading-${run.task_id}`} data-testid={`run-overview-${run.task_id}`}>
        <h3 id={`run-overview-heading-${run.task_id}`} className="text-xs font-semibold uppercase tracking-wide text-ra-text-tertiary">Overview</h3>
        <dl className="mt-3 grid grid-cols-1 gap-3 text-xs sm:grid-cols-2 lg:grid-cols-4">
          <div><dt className="text-ra-text-tertiary">当前阶段</dt><dd className="mt-1 text-ra-text-secondary">{stageLabel(run.stage)}</dd></div>
          <div><dt className="text-ra-text-tertiary">活跃状态</dt><dd className="mt-1"><span className={cn("rounded-full px-2 py-0.5", LIVENESS_STYLES[livenessKey(run.liveness)] ?? LIVENESS_STYLES.UNKNOWN)}>{livenessLabel(livenessKey(run.liveness))}</span></dd></div>
          <div><dt className="text-ra-text-tertiary">当前 Agent</dt><dd className="mt-1 inline-flex items-center gap-1.5 text-ra-text-secondary"><UserRound className="h-3.5 w-3.5" aria-hidden="true" />{agentLabel(currentAgent)}</dd></div>
          <div><dt className="text-ra-text-tertiary">最近活动</dt><dd className="mt-1 inline-flex items-center gap-1.5 text-ra-text-secondary"><Clock3 className="h-3.5 w-3.5" aria-hidden="true" />{lastActivityAt(run) ? relativeTime(lastActivityAt(run)) : "未知"}</dd></div>
        </dl>
        {agents.length > 0 ? <div className="mt-3 flex flex-wrap gap-2 text-xs text-ra-text-tertiary" data-testid={`run-agents-${run.task_id}`}>{agents.map((agent) => <span key={`${agent.agent_id}:${agent.role}`} className="rounded-full border border-ra-border px-2 py-1">{agentLabel(agent)} · {agent.role || "role unknown"}</span>)}</div> : null}
        {run.validation ? <p className="mt-3 text-xs text-ra-text-secondary" data-testid={`run-validation-${run.task_id}`}>验证：<span className="font-mono">{run.validation.command_id}</span> · {run.validation.status}{run.validation.summary ? ` · ${run.validation.summary}` : ""}</p> : null}
      </section>

      <section aria-labelledby={`run-activity-heading-${run.task_id}`} data-testid={`run-activity-section-${run.task_id}`}>
        <div className="flex items-center justify-between gap-3"><h3 id={`run-activity-heading-${run.task_id}`} className="text-xs font-semibold uppercase tracking-wide text-ra-text-tertiary">Activity</h3><span className="text-[11px] text-ra-text-tertiary">{activityTotal > events.length ? `最近 ${events.length} / 共 ${activityTotal} 条` : `${events.length} 条结构化活动`}</span></div>
        {activityTotal > events.length ? <p className="mt-2 text-[11px] text-ra-text-tertiary">为保持详情清晰，仅显示最近 {events.length} 条结构化活动。</p> : null}
        {events.length > 0 ? <ol className="mt-2" aria-label="运行活动时间线">{events.map((event) => <ActivityRow key={event.id} event={event} />)}</ol> : <p data-testid={`run-activity-empty-${run.task_id}`} className="mt-3 rounded-xl border border-dashed border-ra-border py-6 text-center text-xs text-ra-text-tertiary">暂无结构化活动。</p>}
      </section>

      <section aria-labelledby={`run-files-heading-${run.task_id}`} data-testid={`run-files-section-${run.task_id}`}>
        <div className="flex items-center justify-between gap-3"><h3 id={`run-files-heading-${run.task_id}`} className="text-xs font-semibold uppercase tracking-wide text-ra-text-tertiary">Files</h3><span className="text-[11px] text-ra-text-tertiary">{fileCount} 个文件 · +{additions} -{deletions}</span></div>
        {changedFiles.length > 0 ? <ul className="mt-2 divide-y divide-ra-border/60 rounded-xl border border-ra-border" data-testid={`run-files-${run.task_id}`}>{changedFiles.map((file) => <li key={file.path} className="flex min-w-0 items-center gap-2 px-3 py-2 text-xs"><FileCode2 className="h-3.5 w-3.5 shrink-0 text-ra-text-tertiary" aria-hidden="true" /><span className="min-w-0 flex-1 truncate font-mono text-ra-text-secondary" title={file.path}>{file.path}</span><span className="text-emerald-300">+{file.additions}</span><span className="text-ra-status-error">-{file.deletions}</span></li>)}</ul> : <p data-testid={`run-files-empty-${run.task_id}`} className="mt-3 rounded-xl border border-dashed border-ra-border py-6 text-center text-xs text-ra-text-tertiary">暂无文件变更。</p>}
      </section>
    </div>
  );
}

function RunCard({ run }: { run: PlatformAgentRun }) {
  const [open, setOpen] = useState(false);
  const currentAgent = run.current_agent ?? eventAgent(run.current_activity);
  const currentActivity = run.current_activity;
  const changeSummary = run.change_summary;

  return (
    <li data-testid={`run-${run.task_id}`} className="rounded-2xl border border-ra-border bg-ra-base p-4">
      <button type="button" id={`run-toggle-${run.task_id}`} data-testid={`run-toggle-${run.task_id}`} aria-expanded={open} aria-controls={`run-detail-${run.task_id}`} onClick={() => setOpen((value) => !value)} className="w-full rounded-lg text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-2">{open ? <ChevronDown className="mt-0.5 h-4 w-4 shrink-0 text-ra-text-tertiary" aria-hidden="true" /> : <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-ra-text-tertiary" aria-hidden="true" />}<div className="min-w-0"><p className="text-sm font-medium text-ra-text">{run.title}</p><p className="mt-1 text-xs text-ra-text-tertiary">{run.repository} · {run.executor_kind} · {relativeTime(run.updated_at)}</p></div></div>
          <span data-testid={`run-state-${run.task_id}`} className={cn("shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium", STATE_STYLES[run.state] ?? STATE_STYLES.WAITING_FOR_OWNER)}>{STATE_LABELS[run.state] ?? run.state}</span>
        </div>
      </button>

      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs"><span className="rounded-full border border-ra-border px-2 py-0.5 text-ra-text-secondary">阶段：{stageLabel(run.stage)}</span><span className={cn("rounded-full px-2 py-0.5", LIVENESS_STYLES[livenessKey(run.liveness)] ?? LIVENESS_STYLES.UNKNOWN)} data-testid={`run-liveness-${run.task_id}`}>活跃度：{livenessLabel(livenessKey(run.liveness))}</span><span className="inline-flex items-center gap-1 text-ra-text-secondary" data-testid={`run-agent-${run.task_id}`}><UserRound className="h-3.5 w-3.5" aria-hidden="true" />{agentLabel(currentAgent)}</span>{lastActivityAt(run) ? <span className="text-ra-text-tertiary">最近活动 {relativeTime(lastActivityAt(run))}</span> : null}</div>
      {currentActivity ? <div className="mt-3 rounded-xl border border-ra-border/70 bg-ra-light/40 p-3" data-testid={`run-current-activity-${run.task_id}`}><div className="flex flex-wrap items-center gap-2 text-xs"><Activity className={cn("h-3.5 w-3.5", categoryClass(currentActivity.category))} aria-hidden="true" /><span className="font-medium text-ra-text-secondary">当前活动：{currentActivity.title}</span><span className="rounded-full bg-ra-light px-2 py-0.5 text-ra-text-tertiary">{categoryLabel(currentActivity.category)}</span></div><p className="mt-1 text-xs text-ra-text-tertiary">{currentActivity.description}</p></div> : <p className="mt-3 text-xs text-ra-text-tertiary">暂无当前结构化活动。</p>}
      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">{run.goal_id ? <span data-testid={`run-goal-${run.task_id}`} className="text-ra-text-secondary">目标：{run.goal_title}</span> : <span className="text-ra-text-tertiary">未关联目标</span>}{changeSummary ? <span data-testid={`run-change-summary-${run.task_id}`} className="text-ra-text-secondary">{changeSummary.file_count} 个文件 · +{changeSummary.additions} -{changeSummary.deletions}</span> : null}{run.publication && run.publication.pr_number > 0 ? <a href={run.publication.pr_url} target="_blank" rel="noreferrer" data-testid={`run-pr-${run.task_id}`} className="inline-flex items-center gap-1 text-ra-accent hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"><GitPullRequest className="h-3.5 w-3.5" aria-hidden="true" />PR #{run.publication.pr_number}</a> : null}</div>

      <section data-testid={`run-usage-${run.task_id}`} className="mt-4 rounded-xl border border-ra-border/70 bg-ra-light/40 p-3"><div className="flex flex-wrap items-center justify-between gap-2 text-xs"><div className="flex flex-wrap gap-x-4 gap-y-1 text-ra-text-secondary"><span>Tokens {formatUnits(run.usage.total_token_units)}</span><span>Cost {formatCost(run.usage.cost_micro_units)}</span><span>{run.usage.observation_count} 条数值观测</span></div><span data-testid={`run-enforcement-${run.task_id}`} className={cn("rounded-full px-2 py-1 font-medium", run.budget?.enforcement_class === "HARD_ADMISSION_ENFORCED" ? "bg-emerald-400/10 text-emerald-300" : run.budget?.enforcement_class === "USAGE_UNKNOWN" ? "bg-amber-300/10 text-amber-200" : "bg-ra-light text-ra-text-secondary")}>{ENFORCEMENT_LABELS[run.budget?.enforcement_class ?? "POST_RUN_OBSERVED"]}</span></div>{run.budget?.enforcement_class === "HARD_ADMISSION_ENFORCED" && run.budget.max_token_units !== null ? <div className="mt-3" data-testid={`run-budget-${run.task_id}`}><div className="mb-1 flex justify-between text-[11px] text-ra-text-tertiary"><span>已观测 + 已预留</span><span>{formatUnits(run.budget.observed_token_units + run.budget.reserved_token_units)} / {formatUnits(run.budget.max_token_units)}</span></div><div role="progressbar" aria-label="Token hard admission budget" aria-valuemin={0} aria-valuemax={run.budget.max_token_units} aria-valuenow={run.budget.observed_token_units + run.budget.reserved_token_units} className="h-1.5 overflow-hidden rounded-full bg-ra-border"><div className="h-full rounded-full bg-ra-accent" style={{ width: `${Math.min(100, ((run.budget.observed_token_units + run.budget.reserved_token_units) / run.budget.max_token_units) * 100)}%` }} /></div></div> : null}{run.budget?.enforcement_class === "USAGE_UNKNOWN" ? <p data-testid={`run-usage-unknown-${run.task_id}`} className="mt-2 text-xs text-amber-200">Provider usage unavailable；UNKNOWN 不是 0，后续派发保持停止。</p> : null}{run.usage.status === "USAGE_UNKNOWN" && run.budget?.enforcement_class !== "USAGE_UNKNOWN" ? <p className="mt-2 text-xs text-ra-text-tertiary">尚无可信数值观测；不会把缺失用量显示为 0。</p> : null}{run.budget?.stop_reason === "usage_reservation_overrun" ? <p data-testid={`run-usage-overrun-${run.task_id}`} className="mt-2 text-xs text-amber-200">实际用量超过派发前预留；当前调用仅在完成后发现，后续派发已停止。</p> : null}{run.usage.per_role.length > 0 ? <p className="mt-2 text-[11px] text-ra-text-tertiary">Roles：{run.usage.per_role.map((role) => `${role.role} ${formatUnits(role.input_units + role.output_units + role.reasoning_units + role.cache_read_units + role.cache_write_units)}`).join(" · ")}</p> : null}</section>
      <RunDetail run={run} open={open} />
    </li>
  );
}

export function RunsPage() {
  const runsQuery = useQuery({ queryKey: ["runs"], queryFn: fetchRuns, staleTime: 2_000, refetchInterval: 4_000 });
  const runs = runsQuery.data ?? [];

  return (
    <main data-testid="runs-page" className="min-h-full bg-[var(--oh-surface)] px-4 py-7 sm:px-8 lg:px-12 lg:py-10">
      <div className="mx-auto w-full max-w-[1000px]">
        <header className="mb-8"><p className="text-xs font-medium uppercase tracking-[0.18em] text-ra-text-tertiary">Agent runs</p><h1 className="mt-2 flex items-center gap-2 text-3xl font-medium tracking-[-0.025em] text-ra-text sm:text-4xl"><PlayCircle className="h-7 w-7" aria-hidden="true" />Agent 运行</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-ra-text-secondary">由任务库、目标链接与发布记录派生的只读时间线；任务状态变化会直接反映在这里。</p></header>
        {runsQuery.isError ? <div role="alert" className="rounded-xl border border-dashed border-ra-border py-10 text-center"><p className="text-sm text-ra-text-secondary">暂时无法加载 Agent 运行。</p><button type="button" onClick={() => void runsQuery.refetch()} className="mt-3 inline-flex items-center gap-2 rounded-lg border border-ra-border px-3 py-1.5 text-xs text-ra-text-secondary hover:bg-ra-light focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"><RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />重试</button></div> : runsQuery.isLoading ? <div role="status" aria-live="polite" data-testid="runs-loading" className="rounded-xl border border-dashed border-ra-border py-12 text-center text-sm text-ra-text-tertiary">正在加载 Agent 运行…</div> : <ul className="space-y-2" data-testid="runs-list">{runs.map((run) => <RunCard key={run.task_id} run={run} />)}{runs.length === 0 ? <li className="rounded-2xl border border-dashed border-ra-border py-12 text-center text-sm text-ra-text-tertiary">还没有 Agent 运行记录。</li> : null}</ul>}
      </div>
    </main>
  );
}
