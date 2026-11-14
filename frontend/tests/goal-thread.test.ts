import { describe, expect, it } from "vitest";
import type { ThreadMessageLike } from "@assistant-ui/react";
import type { PlatformGoal, PlatformGoalTimeline, PlatformRunActivityEvent, PlatformTimelineAttempt } from "@/lib/platform-client";
import { goalThread, type AttemptFiles, type AttemptHeader, type AttemptStop, type ToolArgs } from "@/lib/goal-thread";

type Part = Exclude<ThreadMessageLike["content"], string>[number];

function parts(message: ThreadMessageLike): Part[] {
  return typeof message.content === "string" ? [] : [...message.content];
}

function dataPart<T>(message: ThreadMessageLike, name: string): T | undefined {
  const part = parts(message).find((item) => item.type === `data-${name}`) as { data: T } | undefined;
  return part?.data;
}

function event(id: string, category: PlatformRunActivityEvent["category"], extra: Partial<PlatformRunActivityEvent> = {}): PlatformRunActivityEvent {
  return { id, task_id: "t", timestamp: "", category, title: "OpenCode", description: "", type: "EXECUTOR_PROGRESS", ...extra };
}

function attempt(index: number, taskId: string, status: string, extra: Partial<PlatformTimelineAttempt> = {}): PlatformTimelineAttempt {
  return { index, task_id: taskId, status, executor_kind: "opencode", binding_ref: "magpie-codex-gpt-6.1-sol", failure: null,
    events: [], events_total: 0, events_truncated: false, changed_files: [], validation: null, live: null, ...extra };
}

function goal(links: Array<{ task_id: string; plan_task_id: string; status: string; title: string; failure?: PlatformTimelineAttempt["failure"] }>): PlatformGoal {
  return { id: "g", title: "Goal", objective: "Fix the upload flow", status: "RUNNING", repository: "r", tasks: [],
    created_at: "2026-11-01T08:00:00Z", task_links: links } as unknown as PlatformGoal;
}

function timeline(steps: PlatformGoalTimeline["steps"]): PlatformGoalTimeline {
  return { goal: { id: "g", title: "Goal", objective: "Fix the upload flow", status: "RUNNING", repository: "r" }, plan: [], steps };
}

describe("goalThread", () => {
  it("opens with the Owner's request, then attempts by start time across steps, unstarted last", () => {
    const g = goal([
      { task_id: "impl-2", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "Implement" },
      { task_id: "review-1", plan_task_id: "T002", status: "RUNNING", title: "Review" },
      { task_id: "verify-1", plan_task_id: "T003", status: "QUEUED", title: "Verify" },
    ]);
    const t = timeline([
      { plan_task_id: "T001", title: "Implement", status: "READY_FOR_REVIEW", attempts: [
        attempt(1, "impl-1", "FAILED", { started_at: "2026-11-01T09:00:00Z" }),
        attempt(2, "impl-2", "READY_FOR_REVIEW", { started_at: "2026-11-01T11:00:00Z" }),
      ] },
      { plan_task_id: "T002", title: "Review", status: "RUNNING", attempts: [
        attempt(1, "review-1", "RUNNING", { started_at: "2026-11-01T10:00:00Z" }),
      ] },
      // A queued attempt carries its creation time, earlier than every start: it still goes last.
      { plan_task_id: "T003", title: "Verify", status: "QUEUED", attempts: [attempt(1, "verify-1", "QUEUED", { started_at: "2026-11-01T08:30:00Z" })] },
    ]);
    const thread = goalThread(g, t);
    expect(thread.messages.map((message) => [message.role, message.id])).toEqual([
      ["user", "g-objective"],
      ["assistant", "impl-1"],
      ["assistant", "review-1"],
      ["assistant", "impl-2"],
      ["assistant", "verify-1"],
    ]);
    expect(thread.messages[0].content).toBe("Fix the upload flow");
    expect(thread.running).toBe(true);
    expect(thread.messages.find((message) => message.id === "review-1")?.status).toEqual({ type: "running" });
    expect(thread.messages.find((message) => message.id === "impl-2")?.status).toEqual({ type: "complete", reason: "stop" });
    expect(thread.steps.map((step) => step.plan_task_id)).toEqual(["T001", "T002", "T003"]);
    const queued = dataPart<AttemptHeader>(thread.messages[4], "attempt");
    expect(queued?.state).toBe("queued");
  });

  it("heads each turn with its step, attempt number, agent, start time and state", () => {
    const g = goal([{ task_id: "a2", plan_task_id: "T001", status: "RUNNING", title: "实现上传逻辑修复" }]);
    const t = timeline([{ plan_task_id: "T001", title: "实现上传逻辑修复", status: "RUNNING", attempts: [
      attempt(1, "a1", "FAILED", { started_at: "2026-11-01T09:00:00Z" }),
      attempt(2, "a2", "RUNNING", { started_at: "2026-11-01T10:00:00Z", live: { state: "WAITING" } }),
    ] }]);
    const header = dataPart<AttemptHeader>(goalThread(g, t).messages[2], "attempt");
    expect(header).toEqual({ step: "实现上传逻辑修复", attempt: 2, attempts: 2, agent: "OpenCode · codex-gpt-6.1-sol",
      startedAt: "2026-11-01T10:00:00Z", state: "running", live: "WAITING" });
  });

  it("turns tool events into tool-call parts and speech into text, in order", () => {
    const g = goal([{ task_id: "a1", plan_task_id: "T001", status: "RUNNING", title: "Implement" }]);
    const t = timeline([{ plan_task_id: "T001", title: "Implement", status: "RUNNING", attempts: [attempt(1, "a1", "RUNNING", { events: [
      event("s1", "PLAN", { progress_kind: "text", description: "I��ll read the code." }),
      event("e1", "READ", { path: "src/a.py" }),
      event("e2", "COMMAND", { command: { summary: "pytest -q", status: "DONE" } }),
      event("m1", "PLAN", { type: "ACTIVITY", title: "Model selected", description: "codex/gpt-6.1-sol [magpie-codex-gpt-6.1-sol]: escalation" }),
      event("s2", "PLAN", { progress_kind: "text", description: "…" }),
    ] })] }]);
    const content = parts(goalThread(g, t).messages[1]);
    expect(content.map((part) => part.type)).toEqual(["data-attempt", "text", "tool-call", "tool-call", "data-note"]);
    expect(content[1]).toEqual({ type: "text", text: "I'll read the code." });
    const read = content[2] as unknown as { toolCallId: string; toolName: string; args: ToolArgs };
    expect(read).toMatchObject({ toolCallId: "e1", toolName: "read", args: { category: "READ", detail: "src/a.py" } });
    const command = content[3] as unknown as { toolName: string; args: ToolArgs };
    expect(command).toMatchObject({ toolName: "command", args: { category: "COMMAND", detail: "pytest -q" } });
    expect((content[4] as { data: { text: string } }).data.text).toContain("codex/gpt-6.1-sol");
  });

  it("keeps an older run's narration as text when no live speech was recorded", () => {
    const g = goal([{ task_id: "a1", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "Implement" }]);
    const t = timeline([{ plan_task_id: "T001", title: "Implement", status: "READY_FOR_REVIEW", attempts: [attempt(1, "a1", "READY_FOR_REVIEW", {
      events: [event("e1", "READ", { path: "a.py" })],
      narration: [{ timestamp: "", text: "First." }, { timestamp: "", text: "Second." }],
    })] }]);
    const content = parts(goalThread(g, t).messages[1]);
    expect(content.map((part) => part.type)).toEqual(["data-attempt", "text", "text", "tool-call"]);
    expect(content.slice(1, 3)).toEqual([{ type: "text", text: "First." }, { type: "text", text: "Second." }]);
  });

  it("adds the changed files and makes the agent's summary its last words", () => {
    const g = goal([{ task_id: "a1", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "Implement" }]);
    const t = timeline([{ plan_task_id: "T001", title: "Implement", status: "READY_FOR_REVIEW", attempts: [attempt(1, "a1", "READY_FOR_REVIEW", {
      changed_files: [{ path: "a.py", status: "modified", additions: 10, deletions: 2 }, { path: "b.py", status: "added" } as never],
      summary: "Done.\n\n- Added X...[TRUNCATED]",
    })] }]);
    const message = goalThread(g, t).messages[1];
    const content = parts(message);
    expect(content.map((part) => part.type)).toEqual(["data-attempt", "data-files", "text"]);
    expect(dataPart<AttemptFiles>(message, "files")).toEqual({ files: [
      { path: "a.py", additions: 10, deletions: 2 }, { path: "b.py", additions: 0, deletions: 0 },
    ] });
    expect(content[2]).toEqual({ type: "text", text: "Done.\n\n- Added X…" });
    expect(dataPart<AttemptHeader>(message, "attempt")?.state).toBe("done");
  });

  it("marks a stop superseded once a later attempt retried it, and current on the latest", () => {
    const g = goal([{ task_id: "a2", plan_task_id: "T001", status: "FAILED", title: "Implement",
      failure: { classification: "executor_nonzero", detail: "x", message: "" } }]);
    const t = timeline([{ plan_task_id: "T001", title: "Implement", status: "FAILED", attempts: [
      attempt(1, "a1", "FAILED", { failure: { classification: "timeout", detail: "opencode_timeout:3600", message: "" } }),
      attempt(2, "a2", "FAILED"),
    ] }]);
    const [, first, second] = goalThread(g, t).messages;
    const earlier = dataPart<AttemptStop>(first, "stop");
    const latest = dataPart<AttemptStop>(second, "stop");
    expect(earlier).toMatchObject({ superseded: true, label: "执行超过时间上限" });
    // The current attempt's failure comes from the goal detail.
    expect(latest).toMatchObject({ superseded: false, label: "执行器异常退出" });
    expect(parts(second).at(-1)?.type).toBe("data-stop");
    expect(dataPart<AttemptHeader>(second, "attempt")?.state).toBe("stopped");
  });

  it("gives a host-retried attempt no stop part and the interrupted-and-retried state", () => {
    const g = goal([{ task_id: "a2", plan_task_id: "T001", status: "RUNNING", title: "Implement" }]);
    const t = timeline([{ plan_task_id: "T001", title: "Implement", status: "RUNNING", attempts: [
      attempt(1, "a1", "FAILED", { retry_reason: "host_retry:restart", started_at: "2026-11-01T09:00:00Z",
        failure: { classification: "executor_terminated", detail: "host_restart", message: "" } }),
      attempt(2, "a2", "RUNNING", { started_at: "2026-11-01T09:05:00Z" }),
    ] }]);
    const [, retried, current] = goalThread(g, t).messages;
    expect(dataPart<AttemptHeader>(retried, "attempt")?.state).toBe("retried");
    expect(dataPart(retried, "stop")).toBeUndefined();
    expect(retried.status).toEqual({ type: "complete", reason: "stop" });
    expect(dataPart<AttemptHeader>(current, "attempt")?.state).toBe("running");
  });

  it("shows only the request when nothing has been dispatched", () => {
    const thread = goalThread(goal([]));
    expect(thread.messages).toHaveLength(1);
    expect(thread.messages[0].role).toBe("user");
    expect(thread.running).toBe(false);
    expect(thread.steps).toEqual([]);
  });
});
