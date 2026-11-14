/**
 * Goal timeline helpers shared by the goal thread (`goal-thread.ts`): merging
 * the polled goal detail with the timeline, and reading attempts in plain words.
 */
import type {
  PlatformGoal,
  PlatformGoalTimeline,
  PlatformRunActivityEvent,
  PlatformTimelineStep,
} from "@/lib/platform-client";
import { humanCommand } from "@/lib/goal-view";
import { runtimeMessage } from "@/lib/runtime-labels";
import { eventDetail, failureText, meaningfulEvents } from "@/lib/run-explain";
import { activityCategoryLabel } from "@/lib/run-vocabulary";
import { isReviewReady, statusFor } from "@/components/goal-progress";

const STOPPED = new Set(["FAILED", "BLOCKED", "INTERRUPTED"]);

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
function eventPhrase(event: PlatformRunActivityEvent): string {
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

/** "180 个通过，1 个失败：tests…::test_x" from a pytest summary inside the host's message. */
export function checkSummary(text: string): string {
  const counts = /(\d+) passed(?:, (\d+) failed)?|(\d+) failed(?:, (\d+) passed)?/.exec(text);
  if (!counts) return "";
  const passed = counts[1] ?? counts[4] ?? "0";
  const failed = counts[2] ?? counts[3] ?? "0";
  const names = [...text.matchAll(/FAILED (\S+?)(?::\s|$|\s)/g)].map((match) => match[1].split("::").pop()).filter(Boolean);
  return `功能检查：${passed} 个通过，${failed} 个失败${names.length ? `（${names.slice(0, 3).join("、")}）` : ""}`;
}

/**
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
