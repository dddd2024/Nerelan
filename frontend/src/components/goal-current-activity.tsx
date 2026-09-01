import { Activity, ChevronRight, UserRound } from "lucide-react";
import { useMemo } from "react";
import { Link } from "react-router";
import type {
  PlatformAgentRun,
  PlatformGoal,
  PlatformRunActivityEvent,
  PlatformRunAgent,
} from "@/lib/platform-client";
import { cn } from "@/lib/cn";

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
  ACTIVE: "有新活动",
  WAITING: "等待中",
  VALIDATING: "验证中",
  BLOCKED: "已阻塞",
  OWNER_ACTION_REQUIRED: "需要 Owner 处理",
  STALE: "疑似停滞",
  TERMINAL: "已结束",
  UNKNOWN: "未知",
};

const LIVENESS_DOT_STYLES: Record<string, string> = {
  ACTIVE: "bg-emerald-400",
  WAITING: "bg-violet-300",
  VALIDATING: "bg-sky-400",
  BLOCKED: "bg-amber-300",
  OWNER_ACTION_REQUIRED: "bg-amber-300",
  STALE: "bg-red-400",
  TERMINAL: "bg-ra-text-tertiary",
  UNKNOWN: "bg-ra-text-tertiary",
};

const CATEGORY_TEXT_STYLES: Record<string, string> = {
  BLOCKED: "text-ra-status-error",
  OWNER_ACTION_REQUIRED: "text-ra-status-error",
  VERIFY: "text-ra-status-running",
  TEST: "text-ra-status-running",
  CHECKPOINT: "text-ra-status-running",
  AGENT_STARTED: "text-ra-accent",
  COMMAND: "text-ra-accent",
};

function enumKey(value: string | undefined) {
  return String(value ?? "UNKNOWN").toUpperCase();
}

function categoryLabel(value: string | undefined) {
  return CATEGORY_LABELS[enumKey(value)] ?? "活动";
}

function stageLabel(value: string | undefined) {
  return STAGE_LABELS[enumKey(value)] ?? STAGE_LABELS.UNKNOWN;
}

function agentLabel(agent?: PlatformRunAgent | null) {
  if (!agent) return "未分配 Agent";
  return agent.display_name || agent.role || agent.agent_id || "未命名 Agent";
}

function eventAgent(
  event?: { agent?: PlatformRunAgent | null; agent_id?: string; role?: string } | null,
): PlatformRunAgent | null {
  if (!event) return null;
  if (event.agent) return event.agent;
  if (!event.agent_id && !event.role) return null;
  return { agent_id: event.agent_id ?? "", role: event.role ?? "" };
}

function relativeSeconds(value: string) {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return null;
  return Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
}

function livenessTimeText(seconds: number | null) {
  if (seconds == null) return "";
  if (seconds < 60) return `${seconds} 秒`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时`;
  return `${Math.floor(seconds / 86400)} 天`;
}

function lastActivityAt(run: PlatformAgentRun) {
  if (run.last_activity_at) return run.last_activity_at;
  if (run.liveness_detail?.last_activity_at) return run.liveness_detail.last_activity_at;
  if (run.liveness && typeof run.liveness === "object") return run.liveness.last_activity_at;
  return "";
}

function livenessState(run: PlatformAgentRun) {
  const value = run.liveness;
  if (value && typeof value === "object") return enumKey(value.state);
  return enumKey(value);
}

function categoryTextStyle(value: string | undefined) {
  return CATEGORY_TEXT_STYLES[enumKey(value)] ?? "text-ra-text-tertiary";
}

function eventKey(event: PlatformRunActivityEvent, runId: string) {
  return event.id || `${runId}-${event.timestamp}-${event.title}`;
}

interface GoalCurrentActivityProps {
  goal: PlatformGoal;
  runs: PlatformAgentRun[];
  limit?: number;
}

export function GoalCurrentActivity({
  goal,
  runs,
  limit = 5,
}: GoalCurrentActivityProps) {
  const linkedRuns = useMemo(() => {
    const ids = new Set((goal.task_links ?? []).map((link) => link.task_id));
    return runs.filter((run) => ids.has(run.task_id));
  }, [goal.task_links, runs]);

  const view = useMemo(() => {
    if (linkedRuns.length === 0) return null;

    const currentRuns = linkedRuns.filter(
      (run) =>
        run.state === "RUNNING" ||
        livenessState(run) === "ACTIVE" ||
        livenessState(run) === "VALIDATING",
    );
    const workingRuns = linkedRuns.filter(
      (run) =>
        livenessState(run) === "ACTIVE" ||
        livenessState(run) === "VALIDATING",
    );
    const pool = currentRuns.length > 0 ? currentRuns : linkedRuns;
    const primary =
      pool.find((run) => run.current_activity) ??
      [...pool].sort(
        (a, b) =>
          Date.parse(lastActivityAt(b) || "0") -
          Date.parse(lastActivityAt(a) || "0"),
      )[0] ??
      linkedRuns[0];

    const flattened: Array<{
      event: PlatformRunActivityEvent;
      runId: string;
      key: string;
    }> = [];
    for (const run of linkedRuns) {
      for (const event of run.activity ?? run.events ?? []) {
        flattened.push({
          event,
          runId: run.task_id,
          key: eventKey(event, run.task_id),
        });
      }
    }
    const seen = new Set<string>();
    const events = flattened
      .filter(({ key }) => {
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort(
        (a, b) =>
          Date.parse(b.event.timestamp || "0") -
          Date.parse(a.event.timestamp || "0"),
      )
      .slice(0, limit);

    const agentSource = workingRuns.length > 0 ? workingRuns : [primary];
    const agentNames: string[] = [];
    for (const run of agentSource) {
      const agent = run.current_agent ?? eventAgent(run.current_activity);
      const label = agent ? agentLabel(agent) : "";
      if (label && !agentNames.includes(label)) agentNames.push(label);
    }

    const changeSummary = linkedRuns.reduce(
      (acc, run) => {
        if (run.change_summary) {
          acc.fileCount += run.change_summary.file_count;
          acc.additions += run.change_summary.additions;
          acc.deletions += run.change_summary.deletions;
        }
        return acc;
      },
      { fileCount: 0, additions: 0, deletions: 0 },
    );

    return {
      primary,
      events,
      agentNames,
      activeCount: workingRuns.length,
      changeSummary,
      currentActivity: primary.current_activity ?? null,
      liveness: livenessState(primary),
      lastActivity: lastActivityAt(primary),
    };
  }, [linkedRuns, limit]);

  if (!view || linkedRuns.length === 0) return null;

  const livenessKey = view.liveness;
  const livenessSeconds = view.lastActivity
    ? relativeSeconds(view.lastActivity)
    : null;
  const livenessTime = livenessTimeText(livenessSeconds);
  const livenessLabel =
    LIVENESS_LABELS[livenessKey] ?? LIVENESS_LABELS.UNKNOWN;
  const livenessText =
    livenessKey === "ACTIVE"
      ? livenessTime
        ? `${livenessTime}前有新活动`
        : "有新活动"
      : livenessKey === "STALE"
        ? livenessTime
          ? `${livenessTime}没有新活动`
          : "疑似停滞"
        : livenessTime
          ? `${livenessLabel} · ${livenessTime}`
          : livenessLabel;
  const currentAgent = view.currentActivity
    ? view.currentActivity.agent ?? eventAgent(view.currentActivity)
    : null;

  return (
    <section
      data-testid="goal-current-activity"
      aria-label="当前执行活动"
      className="mt-7 border-t border-ra-border/70 pt-6"
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-ra-text-tertiary">
          Agent 活动
        </p>
        <p
          className="flex items-center gap-2 text-xs text-ra-text-secondary"
          data-testid="goal-activity-liveness"
        >
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              LIVENESS_DOT_STYLES[livenessKey] ?? LIVENESS_DOT_STYLES.UNKNOWN,
            )}
            aria-hidden="true"
          />
          {livenessText}
        </p>
      </div>

      {view.agentNames.length > 0 ? (
        <p
          className="mb-3 flex flex-wrap items-center gap-2 text-xs text-ra-text-secondary"
          data-testid="goal-activity-agents"
        >
          <UserRound
            className="h-3.5 w-3.5 text-ra-text-tertiary"
            aria-hidden="true"
          />
          {view.agentNames.length > 1
            ? `${view.agentNames.length} 个 Agent 并行 · `
            : ""}
          {view.agentNames.join(" / ")}
        </p>
      ) : null}

      {view.currentActivity ? (
        <div
          className="mb-4 border-l-2 border-ra-border-strong pl-3"
          data-testid="goal-current-activity-now"
        >
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-xs">
            <Activity
              className={cn(
                "h-3.5 w-3.5 self-center",
                categoryTextStyle(view.currentActivity.category),
              )}
              aria-hidden="true"
            />
            <span className="font-medium text-ra-text-secondary">当前</span>
            <span className="min-w-0 text-ra-text">
              {view.currentActivity.title}
            </span>
            <span className={categoryTextStyle(view.currentActivity.category)}>
              {categoryLabel(view.currentActivity.category)}
            </span>
            {currentAgent ? (
              <span className="text-ra-text-tertiary">
                · {agentLabel(currentAgent)}
              </span>
            ) : null}
          </div>
          {view.currentActivity.description ? (
            <p className="mt-1 text-xs leading-5 text-ra-text-tertiary">
              {view.currentActivity.description}
            </p>
          ) : null}
        </div>
      ) : null}

      {view.events.length > 0 ? (
        <ul
          className="divide-y divide-ra-border/50"
          data-testid="goal-activity-events"
          aria-label="最近活动"
        >
          {view.events.map(({ event, key }) => {
            const agent = eventAgent(event);
            const metadata = [
              agent ? agentLabel(agent) : "",
              event.stage ? stageLabel(event.stage) : "",
            ].filter(Boolean);

            return (
              <li
                key={key}
                className="flex min-w-0 items-baseline gap-3 py-2 text-xs"
                data-testid={`goal-activity-event-${event.id}`}
              >
                <span className="w-12 shrink-0 tabular-nums text-ra-text-tertiary">
                  {event.timestamp ? relativeTimeShort(event.timestamp) : "—"}
                </span>
                <span
                  className={cn(
                    "w-20 shrink-0 font-medium",
                    categoryTextStyle(event.category),
                  )}
                >
                  {categoryLabel(event.category)}
                </span>
                <span
                  className="min-w-0 flex-1 truncate text-ra-text-secondary"
                  title={event.title}
                >
                  {event.title}
                  {event.path ? (
                    <span className="ml-2 font-mono text-ra-text-tertiary">
                      {event.path}
                    </span>
                  ) : null}
                  {event.command ? (
                    <span className="ml-2 font-mono text-ra-text-tertiary">
                      {event.command.summary}
                    </span>
                  ) : null}
                  {event.test ? (
                    <span className="ml-2 font-mono text-ra-text-tertiary">
                      {event.test.summary}
                    </span>
                  ) : null}
                </span>
                {metadata.length > 0 ? (
                  <span className="hidden shrink-0 text-ra-text-tertiary sm:inline">
                    {metadata.join(" · ")}
                  </span>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="text-xs text-ra-text-tertiary">暂无结构化活动记录。</p>
      )}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <p
          className="text-xs text-ra-text-tertiary"
          data-testid="goal-activity-change-summary"
        >
          {view.changeSummary.fileCount > 0
            ? `${view.changeSummary.fileCount} 个文件变更 · +${view.changeSummary.additions} -${view.changeSummary.deletions}`
            : "暂无变更统计"}
        </p>
        <Link
          to="/runs"
          data-testid="goal-activity-full-run-link"
          className="inline-flex items-center gap-1 rounded-lg text-xs font-medium text-ra-accent underline-offset-2 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
        >
          查看完整 Run
          <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}

function relativeTimeShort(value: string) {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return "—";
  const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
  const date = new Date(timestamp);
  if (seconds < 86400) {
    return `${String(date.getHours()).padStart(2, "0")}:${String(
      date.getMinutes(),
    ).padStart(2, "0")}`;
  }
  return `${String(date.getMonth() + 1).padStart(2, "0")}-${String(
    date.getDate(),
  ).padStart(2, "0")}`;
}
