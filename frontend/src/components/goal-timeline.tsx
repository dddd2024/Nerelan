import { useState } from "react";
import { AlertTriangle, Check, ChevronRight, Circle, LoaderCircle, PauseCircle, ShieldAlert } from "lucide-react";
import { Link } from "react-router";
import type {
  PlatformGoal,
  PlatformGoalTimeline,
  PlatformRetryOptions,
  PlatformRunActivityEvent,
  PlatformTimelineAttempt,
  PlatformTimelineStep,
} from "@/lib/platform-client";
import { cn } from "@/lib/cn";
import { displayTitle } from "@/lib/display-title";
import { formatRelativeTime } from "@/lib/format";
import { functionalStatusLabel, normalizeFunctionalValidation } from "@/lib/functional-validation";
import { FunctionalValidationView } from "@/components/functional-validation";
import { StepRetry } from "@/components/step-retry";
import { humanCommand, stepTitle } from "@/lib/goal-view";
import { runtimeMessage } from "@/lib/runtime-labels";
import { collapseRepeats, eventDetail, failureText, meaningfulEvents, modelName, readableAgent } from "@/lib/run-explain";
import {
  activityCategoryClass,
  activityCategoryLabel,
  activityTitleRestatesCategory,
  livenessDotClass,
  livenessLabel,
} from "@/lib/run-vocabulary";
import {
  EXECUTOR_LABELS,
  isReviewReady,
  progressClassName,
  publicationText,
  statusFor,
  taskStateClass,
  taskStateText,
} from "@/components/goal-progress";

/** Blocks shown per attempt before "显示更早"; the server caps the events. */
export const TIMELINE_VISIBLE_BLOCKS = 12;

const STOPPED = new Set(["FAILED", "BLOCKED", "INTERRUPTED"]);
const TOOL_CATEGORIES = new Set(["READ", "SEARCH", "EDIT", "COMMAND", "TEST"]);

function who(attempt: Pick<PlatformTimelineAttempt, "executor_kind" | "binding_ref">) {
  return [EXECUTOR_LABELS[attempt.executor_kind ?? ""] ?? attempt.executor_kind, modelName(attempt.binding_ref)]
    .filter(Boolean).join(" · ");
}

function latestAttempt(step: PlatformTimelineStep) {
  return step.attempts[step.attempts.length - 1];
}

/** Stored sentences sometimes carry a broken curly quote ("I��ll"); show it as an apostrophe. */
export function cleanSpeech(text: string): string {
  return text.replace(/�+/g, "'").replace(/\.\.\.\[TRUNCATED\]$/, "…").trim();
}

function isSpeech(event: PlatformRunActivityEvent) {
  return event.type === "EXECUTOR_PROGRESS" && event.progress_kind === "text";
}

const FILE_VERBS: Record<string, string> = { READ: "正在读", EDIT: "正在修改", SEARCH: "正在搜索" };

/** One event as a short phrase: "正在跑测试", "正在修改 goal_service.py", or the agent's own words. */
export function eventPhrase(event: PlatformRunActivityEvent): string {
  const category = String(event.category);
  if (event.path && FILE_VERBS[category]) return `${FILE_VERBS[category]} ${event.path.split(/[\\/]/).pop()}`;
  if (category === "TEST") return "正在跑检查";
  const command = event.command?.summary || (category === "COMMAND" || category === "EDIT" ? event.description : "");
  if (command) return humanCommand(command);
  const detail = eventDetail(event) || activityCategoryLabel(event.category);
  return `正在做：${detail.length > 60 ? `${detail.slice(0, 59)}…` : detail}`;
}

/** Retries the host made by itself (interruption, stall, provider overload): not the model's failure. */
export function hostRetried(reason?: string): boolean {
  return /^(host_retry|transient_overload|executor_terminated)/.test(reason ?? "");
}

/** The one sentence a reader needs first: what is happening now, or what waits on them. */
export function timelineStatusLine(timeline: PlatformGoalTimeline): { tone: "live" | "stopped" | "done" | "idle"; text: string } {
  for (const step of timeline.steps) {
    const attempt = latestAttempt(step);
    if (attempt && statusFor(attempt.status) === "running") {
      const shown = meaningfulEvents(attempt.events).filter((event) => !isSpeech(event));
      const last = shown[shown.length - 1];
      return { tone: "live", text: last ? eventPhrase(last) : "Agent 已启动，等待第一条动作" };
    }
  }
  const stopped = timeline.steps.find((step) => STOPPED.has(latestAttempt(step)?.status ?? ""));
  if (stopped) {
    const reason = failureText(latestAttempt(stopped)?.failure);
    return { tone: "stopped", text: `已停下：${reason.label}${reason.nextStep ? `。${reason.nextStep}` : ""}` };
  }
  if (timeline.steps.length > 0 && timeline.steps.every((step) => isReviewReady(statusFor(latestAttempt(step)?.status ?? step.status)))) {
    return { tone: "done", text: "执行完成，等待审查。" };
  }
  return { tone: "idle", text: runtimeMessage(String(timeline.goal.status ?? "")).label };
}

type Block =
  | { kind: "say"; key: string; text: string }
  | { kind: "actions"; key: string; events: PlatformRunActivityEvent[] }
  | { kind: "note"; key: string; event: PlatformRunActivityEvent };

/**
 * The agent's turn, the way an agent chat shows it: what it says as prose,
 * consecutive tool calls folded into one "读取 3 个文件、运行 1 条命令" row,
 * and the other events (model choice, a stop) as single lines.
 */
export function attemptBlocks(attempt: PlatformTimelineAttempt): Block[] {
  const stopped = STOPPED.has(attempt.status);
  const blocks: Block[] = [];
  meaningfulEvents(attempt.events).forEach((event, index) => {
    const key = event.id || `${attempt.task_id}-${index}`;
    if (isSpeech(event)) {
      const text = cleanSpeech(event.description);
      // A lone "…" (often a mis-decoded ellipsis) says nothing.
      if (/[\p{L}\p{N}]/u.test(text)) blocks.push({ kind: "say", key, text });
    } else if (TOOL_CATEGORIES.has(String(event.category)) || event.type === "EXECUTOR_PROGRESS") {
      const last = blocks[blocks.length - 1];
      if (last?.kind === "actions") last.events.push(event);
      else blocks.push({ kind: "actions", key, events: [event] });
    } else if (!(stopped && event.category === "BLOCKED")) {
      // A stop is said once, in the stop card below.
      blocks.push({ kind: "note", key, event });
    }
  });
  // Runs from before live progress kept only the agent's sentences (and a tool count)
  // in their exit evidence; show them when no live speech was recorded.
  if (!blocks.some((block) => block.kind === "say") && attempt.narration?.length) {
    const said = attempt.narration.map((item, index): Block => ({ kind: "say", key: `n-${index}`, text: cleanSpeech(item.text) }));
    const firstAction = blocks.findIndex((block) => block.kind === "actions");
    blocks.splice(firstAction < 0 ? blocks.length : firstAction, 0, ...said);
  }
  return blocks;
}

const ACTION_WORDS: Record<string, [string, string]> = {
  READ: ["读取", "个文件"], SEARCH: ["搜索", "次"], EDIT: ["修改", "处"], COMMAND: ["运行", "条命令"], TEST: ["运行", "项检查"],
};

/** "读取 3 个文件、运行 2 条命令" for one folded group of tool calls. */
export function actionsSummary(events: PlatformRunActivityEvent[]): string {
  const counts = new Map<string, number>();
  for (const event of events) {
    const key = ACTION_WORDS[String(event.category)] ? String(event.category) : "OTHER";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const parts = [...counts.entries()].map(([key, n]) =>
    key === "OTHER" ? `其他 ${n} 个动作` : `${ACTION_WORDS[key][0]} ${n} ${ACTION_WORDS[key][1]}`);
  return parts.join("、");
}

function ActionRow({ event, repeats }: { event: PlatformRunActivityEvent; repeats: number }) {
  const label = activityCategoryLabel(event.category);
  const title = activityTitleRestatesCategory(event.category, event.title) || event.title === "Model selected" || event.title === "OpenCode" ? "" : event.title;
  const detail = eventDetail(event);
  const agent = readableAgent(event);
  return (
    <li data-testid={`timeline-event-${event.id}`} className="flex min-w-0 items-baseline gap-2 text-xs">
      <span className={cn("w-12 shrink-0 text-xs", activityCategoryClass(event.category))}>{label}</span>
      <span className="min-w-0 flex-1 truncate font-mono text-xs text-ra-text-secondary" title={[title, detail].filter(Boolean).join(" · ")}>
        {[title, detail].filter(Boolean).join(" · ") || label}
        {repeats > 1 ? ` ×${repeats}` : ""}
      </span>
      {agent && <span className="hidden shrink-0 text-xs text-ra-text-tertiary sm:inline">{agent}</span>}
    </li>
  );
}

function AgentTurn({ attempt, live }: { attempt: PlatformTimelineAttempt; live: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const blocks = attemptBlocks(attempt);
  const visible = expanded ? blocks : blocks.slice(-TIMELINE_VISIBLE_BLOCKS);
  const hidden = blocks.length - visible.length;
  const lastActions = [...visible].reverse().find((block) => block.kind === "actions")?.key;
  // Older runs recorded tool calls only as a count; live runs list each one.
  const legacyTools = !attempt.events.some((event) => event.type === "EXECUTOR_PROGRESS") ? attempt.tool_actions ?? 0 : 0;
  if (blocks.length === 0 && !legacyTools && !attempt.summary) {
    return <p className="text-xs text-ra-text-tertiary">还没有动作记录。</p>;
  }
  return (
    <div className="space-y-1.5" data-testid={`timeline-events-${attempt.task_id}`}>
      {hidden > 0 && (
        <button type="button" onClick={() => setExpanded(true)}
          className="text-xs text-ra-accent underline-offset-4 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
          显示更早的 {hidden} 段
        </button>
      )}
      {visible.map((block) => {
        if (block.kind === "say") {
          return <p key={block.key} data-testid={`timeline-say-${block.key}`} className="whitespace-pre-wrap text-sm leading-6 text-ra-text">{block.text}</p>;
        }
        if (block.kind === "note") {
          return <ul key={block.key} className="space-y-1"><ActionRow event={block.event} repeats={1} /></ul>;
        }
        return <ActionGroup key={block.key} block={block} open={live && block.key === lastActions} />;
      })}
      {legacyTools > 0 && (
        <p className="text-xs text-ra-text-secondary" data-testid={`timeline-legacy-tools-${attempt.task_id}`}>
          调用了 {legacyTools} 次工具 <span className="text-ra-text-tertiary">（这次运行没有记录每次调用的明细）</span>
        </p>
      )}
      {attempt.summary && <AgentSummary text={cleanSpeech(attempt.summary)} taskId={attempt.task_id} />}
      {attempt.events_truncated && (
        <p className="text-xs text-ra-text-tertiary">
          只显示最近 {attempt.events.length} 条记录，共 {attempt.events_total} 条。
          <Link to={`/runs?task=${encodeURIComponent(attempt.task_id)}`} className="ml-1 text-ra-accent hover:underline">查看完整运行</Link>
        </p>
      )}
    </div>
  );
}

/** Rows shown in an open action group before "显示全部". */
export const ACTION_ROWS_SHOWN = 6;

function ActionGroup({ block, open }: { block: Extract<Block, { kind: "actions" }>; open: boolean }) {
  const [all, setAll] = useState(false);
  const rows = collapseRepeats(block.events.map((event) => ({ event, key: event.id })));
  const shown = all ? rows : rows.slice(-ACTION_ROWS_SHOWN);
  return (
    <details open={open} className="group">
      <summary data-testid={`timeline-actions-${block.key}`}
        className="flex w-fit cursor-pointer list-none items-center gap-1 rounded text-xs text-ra-text-secondary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
        {actionsSummary(block.events)}
        <ChevronRight className="h-3 w-3 transition-transform group-open:rotate-90" aria-hidden="true" />
      </summary>
      <ul className="mt-1 space-y-1 border-l border-ra-border/60 pl-3">
        {shown.length < rows.length && (
          <li>
            <button type="button" onClick={() => setAll(true)}
              className="text-xs text-ra-accent underline-offset-4 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
              显示全部 {rows.length} 条
            </button>
          </li>
        )}
        {shown.map(({ event, key, repeats }) => <ActionRow key={key} event={event} repeats={repeats} />)}
      </ul>
    </details>
  );
}

function AgentSummary({ text, taskId }: { text: string; taskId: string }) {
  const [open, setOpen] = useState(false);
  const long = text.length > 280 || text.split("\n").length > 5;
  return (
    <div data-testid={`timeline-summary-${taskId}`} className="rounded-xl bg-ra-light/60 px-3 py-2">
      <p className="mb-0.5 text-xs font-medium text-ra-text-tertiary">Agent 的总结</p>
      <p className={cn("whitespace-pre-wrap text-sm leading-6 text-ra-text", long && !open && "line-clamp-4")}>{text}</p>
      {long && (
        <button type="button" onClick={() => setOpen((value) => !value)}
          className="mt-0.5 text-xs text-ra-accent underline-offset-4 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
          {open ? "收起" : "展开全部"}
        </button>
      )}
    </div>
  );
}

/** "180 个通过，1 个失败：tests…::test_x" from a pytest summary inside the host's message. */
export function checkSummary(text: string): string {
  const counts = /(\d+) passed(?:, (\d+) failed)?|(\d+) failed(?:, (\d+) passed)?/.exec(text);
  if (!counts) return "";
  const passed = counts[1] ?? counts[4] ?? "0";
  const failed = counts[2] ?? counts[3] ?? "0";
  const names = [...text.matchAll(/FAILED (\S+?)(?::\s|$|\s)/g)].map((match) => match[1].split("::").pop()).filter(Boolean);
  return `功能检查：${passed} 个通过，${failed} 个失败${names.length ? `（${names.slice(0, 3).join("、")}）` : ""}`;
}

function AttemptBlock({ attempt, total }: { attempt: PlatformTimelineAttempt; total: number }) {
  const state = statusFor(attempt.status);
  // An attempt the host retried by itself (restart, stall, overload) is not a failure to act on;
  // `retry_reason` is recorded on the attempt that was retried.
  const autoRetried = hostRetried(attempt.retry_reason);
  // A failure that a later attempt already retried is history, not something to act on.
  const superseded = attempt.index < total;
  const stopped = STOPPED.has(attempt.status) && !autoRetried;
  const reason = stopped ? failureText(attempt.failure) : null;
  const checks = reason ? checkSummary(reason.detail) : "";
  const files = attempt.changed_files ?? [];
  const additions = files.reduce((sum, file) => sum + (file.additions ?? 0), 0);
  const deletions = files.reduce((sum, file) => sum + (file.deletions ?? 0), 0);
  return (
    <li data-testid={`timeline-attempt-${attempt.task_id}`} className="relative border-l border-ra-border/70 pb-4 pl-4 last:pb-1">
      <span aria-hidden="true" className={cn("absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full border-2 bg-ra-base",
        stopped && !superseded ? "border-ra-status-error" : state === "running" ? "border-ra-accent" : isReviewReady(state) ? "border-ra-status-running" : "border-ra-border-strong")} />
      <div className="mb-1.5 flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
        <p className="text-xs font-medium text-ra-text">
          {total > 1 ? `第 ${attempt.index} 次` : "执行"}{who(attempt) ? ` · ${who(attempt)}` : ""}
        </p>
        {attempt.started_at && state !== "queued" && <span className="text-xs text-ra-text-tertiary">{formatRelativeTime(attempt.started_at)}开始</span>}
        {state === "queued" && <span className="text-xs text-ra-text-tertiary">还没开始</span>}
        <span className="ml-auto inline-flex items-center gap-1.5 text-xs">
          {/* The step header carries the state; an attempt adds only liveness or its stop reason. */}
          {attempt.live && state === "running" ? <>
            <span className={cn("h-1.5 w-1.5 rounded-full", livenessDotClass(attempt.live.state))} aria-hidden="true" />
            <span className="text-ra-text-secondary" data-testid={`timeline-liveness-${attempt.task_id}`}>{livenessLabel(attempt.live.state)}</span>
          </> : stopped && reason && total > 1 ? <span className={superseded ? "text-ra-text-tertiary" : taskStateClass(state)}>{reason.label}</span>
            : autoRetried ? <span data-testid={`timeline-auto-retry-${attempt.task_id}`} className="text-ra-text-tertiary">被中断，已自动重试</span> : null}
        </span>
      </div>
      <AgentTurn attempt={attempt} live={state === "running"} />
      {files.length > 0 && (
        <p className="mt-2 text-xs text-ra-text-secondary" data-testid={`timeline-files-${attempt.task_id}`}>
          改了 {files.length} 个文件 · +{additions} −{deletions}
          <span className="ml-1 font-mono text-ra-text-tertiary">{files.slice(0, 3).map((file) => file.path).join("、")}{files.length > 3 ? " …" : ""}</span>
        </p>
      )}
      {reason && superseded && (
        <details data-testid={`timeline-stop-${attempt.task_id}`} className="mt-2 text-xs text-ra-text-secondary">
          <summary className="w-fit cursor-pointer rounded hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
            这次因“{reason.label}”停下，之后已重试
          </summary>
          <div className="mt-1 space-y-0.5 pl-3 text-ra-text-tertiary">
            {checks && <p data-testid={`timeline-checks-${attempt.task_id}`}>{checks}</p>}
            {reason.detail && <p className="break-words font-mono leading-5">{reason.detail}</p>}
          </div>
        </details>
      )}
      {reason && !superseded && (
        <div role="alert" data-testid={`timeline-stop-${attempt.task_id}`}
          className="mt-2 flex items-start gap-2.5 rounded-xl border border-ra-status-error/30 bg-ra-status-error/5 px-3 py-2.5">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ra-status-error" aria-hidden="true" />
          <div className="min-w-0 space-y-0.5">
            <p className="text-sm font-semibold text-ra-text">为什么停下：{reason.label}</p>
            {checks && <p className="text-xs text-ra-text" data-testid={`timeline-checks-${attempt.task_id}`}>{checks}</p>}
            {reason.nextStep && <p className="text-xs text-ra-text-secondary">下一步：{reason.nextStep}</p>}
            {reason.detail && (
              <details className="text-xs text-ra-text-tertiary">
                <summary className="w-fit cursor-pointer rounded hover:text-ra-text-secondary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">技术细节</summary>
                <p className="mt-1 break-words font-mono leading-5">{reason.detail}</p>
              </details>
            )}
          </div>
        </div>
      )}
    </li>
  );
}

function StepIcon({ state }: { state: string }) {
  const Icon = isReviewReady(state) ? Check : state === "running" ? LoaderCircle
    : state === "interrupted" ? PauseCircle : state === "blocked" ? ShieldAlert : Circle;
  return (
    <span aria-hidden="true" className={cn("mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center", taskStateClass(state))}>
      <Icon className={cn(state === "queued" ? "h-2.5 w-2.5" : "h-3.5 w-3.5", state === "running" && "animate-spin")} />
    </span>
  );
}

/** Stopped attempts the Owner can retry (the host refuses others). */
const RETRYABLE = new Set(["FAILED", "BLOCKED"]);

function StepBlock({ step, goalId, retry, role }: { step: PlatformTimelineStep; goalId: string; retry?: PlatformRetryOptions; role?: string }) {
  const current = latestAttempt(step);
  const state = statusFor(current?.status ?? step.status);
  const executor = (current?.status ?? "").endsWith("_FIXTURE") ? "deterministic_fixture" : current?.executor_kind;
  const proof = normalizeFunctionalValidation(step.functional_validation, executor);
  const taskId = current?.task_id ?? step.plan_task_id;
  return (
    <article data-testid={`goal-task-${taskId}`} className="rounded-2xl border border-ra-border/70 bg-ra-workspace px-4 pt-3.5 pb-2 sm:px-5">
      <header className="flex min-w-0 items-start gap-3">
        <StepIcon state={state} />
        <h3 className="min-w-0 flex-1 break-words text-sm font-medium leading-5 text-ra-text" title={`${displayTitle(step.title, 160)}（${step.plan_task_id}）`}>
          {stepTitle(step.title, role)}
        </h3>
      </header>
      <div className="ml-7 mt-2 flex flex-wrap items-center gap-x-2 gap-y-1.5 text-xs leading-4">
        <span className={cn("rounded-md bg-ra-light px-1.5 py-0.5", taskStateClass(state))}>
          {state === "blocked" && current?.failure ? failureText(current.failure).label : taskStateText(state)}
        </span>
        <span data-testid={`goal-functional-status-${taskId}`}
          className={cn("rounded-md border border-ra-border/60 px-1.5 py-0.5", proof.verified ? "text-ra-status-running" : proof.status === "FAILED" ? "text-ra-status-error" : "text-ra-text-secondary")}>
          {functionalStatusLabel(proof.status)}
        </span>
        <span data-testid={`goal-publication-${taskId}`}
          className={cn("rounded-md px-1.5 py-0.5", step.publication ? "bg-ra-light text-ra-text-secondary" : step.publication_blocked ? "text-ra-status-error" : "text-ra-text-tertiary")}>
          {publicationText(step.publication, step.publication_blocked)}
        </span>
        <Link to={`/runs?task=${encodeURIComponent(taskId)}`}
          aria-label={`查看 ${step.title} 的${state === "interrupted" ? "中断" : ""}运行`}
          className="ml-auto inline-flex min-h-6 items-center rounded px-1 font-medium text-ra-accent underline-offset-4 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
          查看运行
        </Link>
      </div>
      <ol className="ml-2 mt-3" aria-label="尝试">
        {step.attempts.map((attempt) => <AttemptBlock key={attempt.task_id} attempt={attempt} total={step.attempts.length} />)}
      </ol>
      {retry && RETRYABLE.has(current?.status ?? "") && (
        <StepRetry goalId={goalId} planTaskId={step.plan_task_id} options={retry} />
      )}
      <details className="ml-7 mb-1 text-xs text-ra-text-secondary">
        <summary className="min-h-6 w-fit cursor-pointer rounded underline-offset-4 hover:text-ra-text hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">查看功能检查</summary>
        <FunctionalValidationView evidence={proof} executor={executor} />
      </details>
    </article>
  );
}

/**
 * The goal page as one conversation: status sentence, then each plan step with
 * its attempts in order, each attempt's actions, its stop reason where it
 * stopped, and what it changed.
 *
 * The goal detail (already polled) is the authority for which steps exist and
 * their status; the timeline adds each attempt's actions and history. Until
 * the timeline arrives, each step shows its current attempt from the detail.
 */
export function mergeTimelineSteps(goal: PlatformGoal, timeline?: PlatformGoalTimeline): PlatformTimelineStep[] {
  const byPlanTask = new Map((timeline?.steps ?? []).map((step) => [step.plan_task_id, step]));
  return (goal.task_links ?? []).map((link) => {
    const fromTimeline = byPlanTask.get(link.plan_task_id);
    const attempts = fromTimeline?.attempts.length ? fromTimeline.attempts.map((attempt, index, all) =>
      index === all.length - 1 && attempt.task_id === link.task_id
        ? { ...attempt, status: link.status, failure: link.failure ?? attempt.failure } : attempt)
      : [{
        index: (link.attempts?.length ?? 0) + 1, task_id: link.task_id, status: link.status,
        executor_kind: link.executor_kind, binding_ref: link.binding_ref, failure: link.failure ?? null,
        events: [], events_total: 0, events_truncated: false, changed_files: [], validation: null, live: null,
      }];
    // A new attempt the timeline has not seen yet still shows up at once.
    const last = attempts[attempts.length - 1];
    const withCurrent = last.task_id === link.task_id ? attempts : [...attempts, {
      index: attempts.length + 1, task_id: link.task_id, status: link.status, executor_kind: link.executor_kind,
      binding_ref: link.binding_ref, failure: link.failure ?? null, events: [], events_total: 0,
      events_truncated: false, changed_files: [], validation: null, live: null,
    }];
    return {
      plan_task_id: link.plan_task_id, title: link.title, status: link.status,
      functional_validation: link.functional_validation, publication: link.publication,
      publication_blocked: link.publication_blocked, attempts: withCurrent,
    };
  });
}

export function GoalTimeline({ goal, timeline }: { goal: PlatformGoal; timeline?: PlatformGoalTimeline }) {
  const steps = mergeTimelineSteps(goal, timeline);
  const status = steps.length || timeline ? timelineStatusLine({ goal: { ...goal }, plan: timeline?.plan ?? [], steps }) : null;
  const reviewReady = steps.filter((step) => isReviewReady(statusFor(latestAttempt(step)?.status ?? step.status))).length;
  const total = steps.length || goal.tasks.length;
  const progress = total ? Math.round((reviewReady / total) * 100) : 0;
  return (
    <section aria-label="执行过程" data-testid="goal-timeline" className="space-y-4">
      <span className="sr-only">执行进度</span>
      <div className="flex items-center gap-3 px-1" aria-label={`执行进度 ${reviewReady}/${total}`}>
        <div className="h-1 flex-1 overflow-hidden rounded-full bg-ra-tertiary" data-testid="goal-progress-bar">
          <div className={cn("h-full rounded-full transition-[width] duration-200", progressClassName(goal.status))} style={{ width: `${progress}%` }} />
        </div>
        <span data-testid="goal-progress-summary" className="shrink-0 font-mono text-xs tabular-nums text-ra-text-tertiary">
          {reviewReady}/{total}
        </span>
      </div>
      {status && (
        <p data-testid="goal-timeline-status"
          className={cn("flex items-center gap-2 rounded-xl px-3.5 py-2.5 text-sm",
            status.tone === "live" ? "bg-ra-accent/5 text-ra-text" : status.tone === "stopped" ? "bg-ra-status-error/5 text-ra-text"
              : status.tone === "done" ? "bg-ra-status-running/10 text-ra-text" : "bg-ra-light/60 text-ra-text-secondary")}>
          {status.tone === "live" && <LoaderCircle className="h-3.5 w-3.5 shrink-0 animate-spin text-ra-accent" aria-hidden="true" />}
          {status.tone === "stopped" && <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-ra-status-error" aria-hidden="true" />}
          {status.tone === "done" && <Check className="h-3.5 w-3.5 shrink-0 text-ra-status-running" aria-hidden="true" />}
          <span className="min-w-0">{status.text}</span>
        </p>
      )}
      {steps.length === 0 ? (
        <ol aria-label="计划" className="space-y-2 rounded-2xl border border-ra-border/70 bg-ra-workspace px-4 py-3.5">
          <li className="text-xs font-medium text-ra-text-secondary">计划</li>
          {(timeline?.plan ?? goal.tasks.map((task) => ({ plan_task_id: task.id, title: task.title }))).map((task) => (
            <li key={task.plan_task_id} data-testid={`goal-plan-${task.plan_task_id}`} className="flex items-start gap-3 text-sm text-ra-text">
              <Circle className="mt-1.5 h-2.5 w-2.5 shrink-0 text-ra-text-tertiary" aria-hidden="true" />
              <span className="min-w-0 flex-1">{displayTitle(task.title)}</span>
              <span className="shrink-0 text-xs text-ra-text-tertiary">尚未启动</span>
            </li>
          ))}
        </ol>
      ) : steps.map((step) => (
        <StepBlock key={step.plan_task_id} step={step} goalId={goal.id} retry={timeline?.retry}
          role={timeline?.plan.find((item) => item.plan_task_id === step.plan_task_id)?.role
            ?? goal.tasks.find((task) => task.id === step.plan_task_id)?.agent_role ?? step.plan_task_id} />
      ))}
      <p className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs leading-5 text-ra-text-tertiary">
        <span>执行完成不代表功能验证或交付完成；远端审查、合并与交付另行确认。</span>
        {steps.length > 0 && (
          <Link to={`/runs?goal=${encodeURIComponent(goal.id)}`} data-testid="goal-timeline-runs-link"
            className="font-medium text-ra-text-secondary underline-offset-2 hover:text-ra-text hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
            查看这个目标的全部运行
          </Link>
        )}
      </p>
    </section>
  );
}
