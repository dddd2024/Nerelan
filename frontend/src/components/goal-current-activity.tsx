import { ChevronRight } from "lucide-react";
import { useMemo } from "react";
import { Link } from "react-router";
import type {
  PlatformAgentRun,
  PlatformGoal,
  PlatformRunActivityEvent,
  PlatformRunAgent,
} from "@/lib/platform-client";
import { cn } from "@/lib/cn";
import {
  activityCategoryClass,
  activityCategoryLabel,
  activityTitleRestatesCategory,
  enumKey,
  executionStageLabel,
  livenessDotClass,
  livenessLabel,
} from "@/lib/run-vocabulary";

/*
 * Stage / liveness / activity-category labels and tones come from
 * `@/lib/run-vocabulary`. This component used to keep its own copies, which
 * had already drifted from the Agent Runs page: identical `BLOCKED` and
 * `OWNER_ACTION_REQUIRED` values rendered in different colours depending on
 * which surface you were looking at (`#448` §9 forbids that).
 */
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
  return activityCategoryClass(value);
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
  const livenessTextLabel = livenessLabel(livenessKey);
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
          ? `${livenessTextLabel} · ${livenessTime}`
          : livenessTextLabel;
  const quietLiveness =
    livenessKey === "ACTIVE" || livenessKey === "TERMINAL";
  const currentAgent = view.currentActivity
    ? view.currentActivity.agent ?? eventAgent(view.currentActivity)
    : null;
  const currentActivityTitleRestatesCategory = view.currentActivity
    ? activityTitleRestatesCategory(
        view.currentActivity.category,
        view.currentActivity.title,
      )
    : false;

  return (
    <section
      data-testid="goal-current-activity"
      aria-label="当前执行活动"
      className="rounded-2xl border border-ra-border/70 bg-ra-workspace p-4 sm:p-5"
    >
      <span className="sr-only">Agent 活动</span>

      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-2">
        <h2 className="mr-auto text-sm font-semibold text-ra-text">运行活动</h2>
        {view.agentNames.length > 0 ? (
          <p
            className="rounded-full bg-ra-tertiary/50 px-2.5 py-1 text-[11px] text-ra-text-secondary"
            data-testid="goal-activity-agents"
          >
            {view.agentNames.length > 1
              ? `${view.agentNames.length} 个 Agent 并行 · `
              : ""}
            {view.agentNames.join(" / ")}
          </p>
        ) : (
          <span />
        )}
        <p
          className={cn(
            "inline-flex items-center gap-1.5 text-[11px]",
            quietLiveness ? "sr-only" : "text-ra-text-secondary",
          )}
          data-testid="goal-activity-liveness"
        >
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              livenessDotClass(livenessKey),
            )}
            aria-hidden="true"
          />
          {livenessText}
        </p>
      </div>

      {view.currentActivity ? (
        <div
          className="mb-3 rounded-xl border border-ra-accent/20 bg-ra-accent/5 px-3 py-3"
          data-testid="goal-current-activity-now"
        >
          {/*
            Same rule as the Runs page: the read-model derives the activity title
            from the category alone, so on live data the title is a static
            English humanisation and printing it beside our own label stated one
            fact twice in two languages. The product language leads instead, and
            a title the server did not derive from the category — the fixtures
            carry real ones — is left exactly as it was.
          */}
          <div className="flex min-w-0 items-baseline justify-between gap-4">
            <p className="min-w-0 flex-1 truncate text-sm font-medium text-ra-text">
              {currentActivityTitleRestatesCategory
                ? activityCategoryLabel(view.currentActivity.category)
                : view.currentActivity.title}
            </p>
            <span
              className={cn(
                "shrink-0 text-[11px]",
                categoryTextStyle(view.currentActivity.category),
              )}
            >
              {[
                currentActivityTitleRestatesCategory
                  ? ""
                  : activityCategoryLabel(view.currentActivity.category),
                currentAgent ? agentLabel(currentAgent) : "",
              ]
                .filter(Boolean)
                .join(" · ")}
            </span>
          </div>
          {view.currentActivity.description ? (
            <p className="mt-0.5 text-xs leading-5 text-ra-text-tertiary">
              {view.currentActivity.description}
            </p>
          ) : null}
        </div>
      ) : null}

      {view.events.length > 0 ? (
        <ul
          className="divide-y divide-ra-border/45"
          data-testid="goal-activity-events"
          aria-label="最近活动"
        >
          {view.events.map(({ event, key }) => {
            const agent = eventAgent(event);
            const metadata = [
              activityCategoryLabel(event.category),
              event.stage ? executionStageLabel(event.stage) : "",
              agent ? agentLabel(agent) : "",
            ].filter(Boolean);
            const detail = event.path
              ? event.path
              : event.command
                ? event.command.summary
                : event.test
                  ? event.test.summary
                  : "";

            return (
              <li
                key={key}
                className="flex min-w-0 items-baseline gap-4 px-1 py-3"
                data-testid={`goal-activity-event-${event.id}`}
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs text-ra-text-secondary" title={event.title}>
                    {event.title}
                  </p>
                  {detail ? (
                    <p className="mt-0.5 truncate font-mono text-[11px] text-ra-text-tertiary">
                      {detail}
                    </p>
                  ) : null}
                </div>
                <span
                  className={cn(
                    "hidden shrink-0 text-[11px] sm:inline",
                    categoryTextStyle(event.category),
                  )}
                >
                  {metadata.join(" · ")}
                </span>
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="border-t border-ra-border/45 px-1 py-3 text-xs text-ra-text-tertiary">
          暂无结构化活动记录。
        </p>
      )}

      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-ra-border/45 px-1 pt-3">
        <p
          className="text-[11px] text-ra-text-tertiary"
          data-testid="goal-activity-change-summary"
        >
          {view.changeSummary.fileCount > 0
            ? `${view.changeSummary.fileCount} 个文件变更 · +${view.changeSummary.additions} -${view.changeSummary.deletions}`
            : "暂无变更统计"}
        </p>
        <Link
          to="/runs"
          data-testid="goal-activity-full-run-link"
          className="inline-flex min-h-6 items-center gap-1 rounded-lg py-0.5 text-[11px] font-medium text-ra-text-secondary underline-offset-2 hover:text-ra-text hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
        >
          查看完整 Run
          <ChevronRight className="h-3 w-3" aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}
