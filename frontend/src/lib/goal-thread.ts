/**
 * A goal as an agent conversation, the way Claude and Codex show one: the
 * Owner's request, then each agent attempt as an assistant turn with its words
 * as prose and its tool calls as collapsible rows.
 *
 * Nerelan stays the source of truth: this only converts the goal timeline into
 * assistant-ui messages (`ThreadMessageLike`); nothing is sent back.
 */
import type { ThreadMessageLike } from "@assistant-ui/react";
import type { PlatformGoal, PlatformRunActivityEvent, PlatformTimelineAttempt, PlatformTimelineStep } from "@/lib/platform-client";
import { checkSummary, mergeTimelineSteps, hostRetried, cleanSpeech } from "@/components/goal-timeline";
import { statusFor } from "@/components/goal-progress";
import { eventDetail, failureText, meaningfulEvents, modelName } from "@/lib/run-explain";
import { objectiveText, stepTitle } from "@/lib/goal-view";
import type { PlatformGoalTimeline } from "@/lib/platform-client";

/** Categories shown as tool calls; the rest are notes on the attempt. */
const TOOL_CATEGORIES = new Set(["READ", "SEARCH", "EDIT", "COMMAND", "TEST"]);
const STOPPED = new Set(["FAILED", "BLOCKED", "INTERRUPTED"]);

export interface AttemptHeader {
  step: string;
  attempt: number;
  attempts: number;
  agent: string;
  startedAt?: string;
  state: "running" | "done" | "stopped" | "queued" | "retried";
  live?: string;
}

export interface AttemptStop {
  /** The plan step, so the stop card can offer the Owner retry in place. */
  planTaskId: string;
  /** "180 个通过，1 个失败：…" when the host's message carries a pytest summary. */
  checks: string;
  label: string;
  nextStep: string;
  detail: string;
  /** A later attempt already retried this one: history, not an alert. */
  superseded: boolean;
}

export interface AttemptFiles {
  files: Array<{ path: string; additions: number; deletions: number }>;
}

export interface ToolArgs {
  [key: string]: string;
  category: string;
  detail: string;
}

const EXECUTORS: Record<string, string> = { opencode: "OpenCode", codex: "Codex", claude_code: "Claude Code", deterministic_fixture: "演示" };

function speech(event: PlatformRunActivityEvent): boolean {
  return event.type === "EXECUTOR_PROGRESS" && event.progress_kind === "text";
}

function attemptState(attempt: PlatformTimelineAttempt): AttemptHeader["state"] {
  if (hostRetried(attempt.retry_reason)) return "retried";
  const state = statusFor(attempt.status);
  if (state === "running") return "running";
  if (state === "review-ready" || state === "fixture-review-ready") return "done";
  if (STOPPED.has(attempt.status) || state === "blocked" || state === "interrupted") return "stopped";
  return "queued";
}

type Part = Exclude<ThreadMessageLike["content"], string>[number];

function attemptParts(step: PlatformTimelineStep, attempt: PlatformTimelineAttempt, role?: string): Part[] {
  const header: AttemptHeader = {
    step: stepTitle(step.title, role),
    attempt: attempt.index,
    attempts: step.attempts.length,
    agent: [EXECUTORS[attempt.executor_kind ?? ""] ?? attempt.executor_kind, modelName(attempt.binding_ref)].filter(Boolean).join(" · "),
    startedAt: attempt.started_at,
    state: attemptState(attempt),
    live: attempt.live?.state,
  };
  const parts: Part[] = [{ type: "data-attempt", id: `${attempt.task_id}-header`, data: header }];
  const said = new Set<string>();
  for (const event of meaningfulEvents(attempt.events)) {
    if (speech(event)) {
      const text = cleanSpeech(event.description);
      // A lone "…" (often a mis-decoded ellipsis) says nothing.
      if (/[\p{L}\p{N}]/u.test(text)) {
        parts.push({ type: "text", text });
        said.add(text);
      }
    } else if (TOOL_CATEGORIES.has(String(event.category)) || event.type === "EXECUTOR_PROGRESS") {
      const args: ToolArgs = { category: String(event.category), detail: eventDetail(event) || event.title };
      parts.push({ type: "tool-call", toolCallId: event.id, toolName: String(event.category).toLowerCase(), args, result: "done" });
    } else if (event.title === "Model selected") {
      parts.push({ type: "data-note", id: event.id, data: { text: eventDetail(event) } });
    }
  }
  if (!said.size && attempt.narration?.length) {
    parts.splice(1, 0, ...attempt.narration.map((item): Part => ({ type: "text", text: cleanSpeech(item.text) })));
  }
  // Runs from before live progress kept only a tool count.
  const legacyTools = !attempt.events.some((event) => event.type === "EXECUTOR_PROGRESS") ? attempt.tool_actions ?? 0 : 0;
  if (legacyTools > 0) {
    parts.push({ type: "data-note", id: `${attempt.task_id}-legacy`, data: { text: `调用了 ${legacyTools} 次工具（这次运行没有记录每次调用的明细）` } });
  }
  if (attempt.events_truncated) {
    parts.push({ type: "data-note", id: `${attempt.task_id}-truncated`, data: {
      text: `只显示最近 ${attempt.events.length} 条记录，共 ${attempt.events_total} 条`, taskId: attempt.task_id } });
  }
  const files = attempt.changed_files ?? [];
  if (files.length) {
    const data: AttemptFiles = { files: files.map((file) => ({ path: file.path, additions: file.additions ?? 0, deletions: file.deletions ?? 0 })) };
    parts.push({ type: "data-files", id: `${attempt.task_id}-files`, data });
  }
  // The agent's final answer is prose like the rest of its turn.
  if (attempt.summary) parts.push({ type: "text", text: cleanSpeech(attempt.summary) });
  if (STOPPED.has(attempt.status) && !hostRetried(attempt.retry_reason)) {
    const reason = failureText(attempt.failure);
    const stop: AttemptStop = {
      ...reason, planTaskId: step.plan_task_id, checks: checkSummary(reason.detail),
      superseded: attempt.index < step.attempts.length,
    };
    parts.push({ type: "data-stop", id: `${attempt.task_id}-stop`, data: stop });
  }
  return parts;
}

export interface GoalThread {
  messages: ThreadMessageLike[];
  running: boolean;
  steps: PlatformTimelineStep[];
}

/** The whole goal as messages, oldest first. */
export function goalThread(goal: PlatformGoal, timeline?: PlatformGoalTimeline): GoalThread {
  const linked = mergeTimelineSteps(goal, timeline);
  // Before dispatch a goal has a plan but no task links: show its steps as not started.
  const plan = timeline?.plan?.length ? timeline.plan : goal.tasks.map((task) => ({ plan_task_id: task.id, title: task.title }));
  const steps: PlatformTimelineStep[] = linked.length ? linked
    : plan.map((item) => ({ plan_task_id: item.plan_task_id, title: item.title, status: "QUEUED", attempts: [] }));
  const roles = new Map((timeline?.plan ?? []).map((item) => [item.plan_task_id, item.role]));
  for (const task of goal.tasks) if (!roles.has(task.id) && task.agent_role) roles.set(task.id, task.agent_role);
  const messages: ThreadMessageLike[] = [{
    id: `${goal.id}-objective`, role: "user",
    content: objectiveText(goal) || goal.objective || goal.title,
    createdAt: goal.created_at ? new Date(goal.created_at) : undefined,
  }];
  let running = false;
  for (const step of steps) {
    for (const attempt of step.attempts) {
      const state = attemptState(attempt);
      if (state === "running") running = true;
      messages.push({
        id: attempt.task_id,
        role: "assistant",
        content: attemptParts(step, attempt, roles.get(step.plan_task_id) ?? step.plan_task_id),
        // A queued attempt's timestamp is its creation, not a start: it sorts last.
        createdAt: attempt.started_at && state !== "queued" ? new Date(attempt.started_at) : undefined,
        status: state === "running" ? { type: "running" } : { type: "complete", reason: "stop" },
      });
    }
  }
  // One conversation in time order across steps; attempts that have not started go last.
  const [request, ...turns] = messages;
  const at = (message: ThreadMessageLike) => message.createdAt?.getTime() ?? Number.MAX_SAFE_INTEGER;
  turns.sort((a, b) => at(a) - at(b));
  return { messages: [request, ...turns], running, steps };
}
