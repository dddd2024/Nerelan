import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { type ReactNode } from "react";
import { fireEvent, render, render as rtlRender, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  __setMockGoalStatus,
  __setMockRuns,
  type PlatformAgentRun,
  type PlatformGoal,
  type PlatformGoalTimeline,
  type PlatformRunActivityEvent,
} from "@/lib/platform-client";
import { HomePage } from "@/routes/home";
import { GoalTimeline, TIMELINE_VISIBLE_BLOCKS, actionsSummary, checkSummary, cleanSpeech, mergeTimelineSteps, timelineStatusLine } from "@/components/goal-timeline";
import { collapseRepeats, eventDetail, failureText, meaningfulEvents, modelName, readableAgent } from "@/lib/run-explain";

const GOAL_ID = "goal-demo-platform";

function makeWrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity, staleTime: 0 } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/?goal=${GOAL_ID}`]}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

const secondsAgo = (seconds: number) => new Date(Date.now() - seconds * 1_000).toISOString();

function activity(id: string, category: PlatformRunActivityEvent["category"], title: string,
                  extra: Partial<PlatformRunActivityEvent> = {}): PlatformRunActivityEvent {
  return { id, task_id: "t-active", timestamp: "2026-09-01T09:41:00Z", category, title, description: "", ...extra };
}

function makeRun(overrides: Partial<PlatformAgentRun> & { task_id: string }): PlatformAgentRun {
  return {
    title: `[演示] ${overrides.task_id}`, repository: "dddd2024/reverse-agent", status: "RUNNING", state: "RUNNING",
    executor_kind: "opencode", orchestration_mode: "sequential_team", created_at: secondsAgo(1800), updated_at: secondsAgo(60),
    failure_classification: "", goal_id: GOAL_ID, goal_title: "完善无人值守多 Agent 平台", window_id: "window-demo",
    liveness: "ACTIVE", last_activity_at: secondsAgo(4), current_activity: null, current_agent: null, agents: [],
    change_summary: null, validation: null, events: [], activity: [], changed_files: [],
    usage: { status: "USAGE_UNKNOWN", input_units: 0, output_units: 0, reasoning_units: 0, cache_read_units: 0,
      cache_write_units: 0, cost_micro_units: 0, total_token_units: 0, observation_count: 0,
      unknown_observation_count: 0, provenance_ids: [], per_role: [] },
    budget: null, publication: null,
    ...overrides,
  } as PlatformAgentRun;
}

describe("Home goal timeline", () => {
  beforeEach(() => __setMockRuns([]));
  afterEach(() => __setMockRuns([]));

  async function mount(run: PlatformAgentRun, linkStatus = "RUNNING", extra: Record<string, unknown> = {}) {
    __setMockRuns([run]);
    __setMockGoalStatus(GOAL_ID, {
      status: linkStatus === "RUNNING" ? "RUNNING" : linkStatus === "READY_FOR_REVIEW" ? "COMPLETED" : "BLOCKED",
      task_links: [{ task_id: run.task_id, plan_task_id: "T001", status: linkStatus, title: "实现上传逻辑修复",
        executor_kind: "opencode", binding_ref: "magpie-codex-gpt-6.1-sol", ...extra }],
    });
    rtlRender(<HomePage />, { wrapper: makeWrapper() });
    await waitFor(() => expect(screen.getByTestId(`timeline-attempt-${run.task_id}`)).toBeInTheDocument());
  }

  it("shows each action in order with its category, detail and agent, and says what it is doing now", async () => {
    await mount(makeRun({ task_id: "t-active", activity: [
      activity("a1", "READ", "Repository read", { path: "upload_service.py", agent: { agent_id: "coder", role: "coder", display_name: "Coder" } }),
      activity("a2", "EDIT", "Repository change", { path: "validation.py" }),
      activity("a3", "COMMAND", "Approved command", { command: { summary: "pytest tests/test_upload.py -q", status: "RUNNING" },
        agent: { agent_id: "test", role: "test", display_name: "Test Agent" } }),
    ] }));
    expect(screen.getByTestId("timeline-event-a1")).toHaveTextContent("读取");
    expect(screen.getByTestId("timeline-event-a1")).toHaveTextContent("upload_service.py");
    expect(screen.getByTestId("timeline-event-a1")).toHaveTextContent("Coder");
    expect(screen.getByTestId("timeline-event-a3")).toHaveTextContent("pytest tests/test_upload.py -q");
    expect(screen.getByTestId("timeline-event-a3")).toHaveTextContent("Test Agent");
    // The server's generic English category titles never show beside the product label.
    expect(screen.getByTestId("timeline-event-a2").textContent).not.toContain("Repository change");
    expect(screen.getByTestId("goal-timeline-status")).toHaveTextContent("正在做：pytest tests/test_upload.py -q");
    expect(screen.getByTestId("timeline-liveness-t-active")).toHaveTextContent("有新活动");
    expect(screen.getByTestId("timeline-attempt-t-active")).toHaveTextContent("OpenCode · codex-gpt-6.1-sol");
    // Semantic activity, never an exact wall-clock stamp.
    expect(screen.getByTestId("timeline-events-t-active").textContent).not.toContain("09:41");
  });

  it.each([["WAITING", "等待中"], ["STALE", "疑似停滞"], ["VALIDATING", "验证中"]])(
    "labels %s liveness instead of presenting it as active work", async (state, label) => {
      await mount(makeRun({ task_id: "t-active", liveness: state as PlatformAgentRun["liveness"], activity: [activity("a1", "READ", "Repository read", { path: "a.py" })] }));
      expect(screen.getByTestId("timeline-liveness-t-active")).toHaveTextContent(label);
      expect(screen.getByTestId("timeline-liveness-t-active")).not.toHaveTextContent("有新活动");
    });

  it("puts the stop reason where the attempt stopped and leads with it", async () => {
    await mount(makeRun({ task_id: "t-active", status: "FAILED", state: "FAILED", liveness: "TERMINAL",
      activity: [activity("a1", "BLOCKED", "Run blocked", { description: "OpenCode CLI wrote nothing for too long (often a provider 429 it waits out)" })] }),
    "FAILED", { failure: { classification: "executor_stalled", detail: "opencode_stalled:900", message: "OpenCode stalled: OpenCode CLI wrote nothing for too long" } });
    expect(screen.getByTestId("timeline-stop-t-active")).toHaveTextContent("为什么停下：Agent 长时间没有任何输出，已被停止");
    expect(screen.getByTestId("timeline-stop-t-active")).toHaveTextContent("下一步：最常见的原因是模型被限流（429）");
    expect(screen.getByTestId("goal-timeline-status")).toHaveTextContent("已停下：Agent 长时间没有任何输出");
    expect(screen.queryByTestId("timeline-liveness-t-active")).not.toBeInTheDocument();
  });

  it("presents finished work without claiming it is still running", async () => {
    await mount(makeRun({ task_id: "t-active", status: "READY_FOR_REVIEW", state: "READY_FOR_REVIEW", liveness: "TERMINAL",
      activity: [activity("a1", "EDIT", "Repository change", { path: "a.py" })] }), "READY_FOR_REVIEW");
    expect(screen.getByTestId("goal-timeline-status")).toHaveTextContent("执行完成，等待审查");
    expect(screen.queryByTestId("timeline-liveness-t-active")).not.toBeInTheDocument();
    expect(screen.queryByText("Agent 正在执行")).not.toBeInTheDocument();
  });

  it("shows the agent's words as prose and folds its tool calls like an agent chat", async () => {
    const say = (id: string, text: string) => activity(id, "PLAN", "OpenCode", { type: "EXECUTOR_PROGRESS", progress_kind: "text", description: text });
    const tool = (id: string, category: PlatformRunActivityEvent["category"], path: string) =>
      activity(id, category, "OpenCode", { type: "EXECUTOR_PROGRESS", description: `x ${path}`, path });
    await mount(makeRun({ task_id: "t-active", activity: [
      say("s1", "I'll read the routing code first."),
      tool("t1", "READ", "a.py"), tool("t2", "READ", "b.py"), tool("t3", "COMMAND", "pytest"),
      say("s2", "Now I'll add the detector."),
      tool("t4", "EDIT", "c.py"),
    ] }));
    expect(screen.getByTestId("timeline-say-s1")).toHaveTextContent("I'll read the routing code first.");
    expect(screen.getByTestId("timeline-actions-t1")).toHaveTextContent("读取 2 个文件、运行 1 条命令");
    expect(screen.getByTestId("timeline-actions-t4")).toHaveTextContent("修改 1 处");
    // The newest group of a running attempt is open; older groups stay folded.
    expect(screen.getByTestId("timeline-actions-t4").closest("details")).toHaveAttribute("open");
    expect(screen.getByTestId("timeline-actions-t1").closest("details")).not.toHaveAttribute("open");
    expect(screen.getByTestId("goal-timeline-status")).toHaveTextContent("正在做：c.py");
  });

  it(`shows the newest ${TIMELINE_VISIBLE_BLOCKS} blocks and reveals older ones on request`, async () => {
    const many = Array.from({ length: TIMELINE_VISIBLE_BLOCKS + 2 }, (_, i) =>
      activity(`s${i}`, "PLAN", "OpenCode", { type: "EXECUTOR_PROGRESS", progress_kind: "text", description: `step ${i}` }));
    await mount(makeRun({ task_id: "t-active", activity: many }));
    expect(screen.queryByTestId("timeline-say-s0")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "显示更早的 2 段" }));
    expect(screen.getByTestId("timeline-say-s0")).toBeInTheDocument();
  });

  it("lists the plan before anything has run", async () => {
    __setMockGoalStatus(GOAL_ID, { status: "PLANNED", task_links: [] });
    rtlRender(<HomePage />, { wrapper: makeWrapper() });
    await waitFor(() => expect(screen.getByTestId("goal-timeline")).toBeInTheDocument());
    expect(screen.getByTestId("goal-timeline")).toHaveTextContent("计划");
    expect(screen.getByTestId("goal-timeline-status")).toHaveTextContent("等待启动");
  });
});

const GOAL = { id: "g", title: "t", objective: "o", status: "BLOCKED", repository: "r", tasks: [],
  task_links: [{ task_id: "task-3", plan_task_id: "T001", status: "FAILED", title: "#1458 [Routing] implement",
    executor_kind: "opencode", binding_ref: "magpie-codex-gpt-6.1-sol",
    failure: { classification: "executor_nonzero", detail: "opencode_nonzero:exit=1073807364", message: "OpenCode nonzero exit: exit=1073807364" } }],
} as unknown as PlatformGoal;

function attempt(index: number, taskId: string, status: string, binding: string, failure: PlatformGoalTimeline["steps"][number]["attempts"][number]["failure"]) {
  return { index, task_id: taskId, status, executor_kind: "opencode", binding_ref: binding, failure,
    events: [], events_total: 0, events_truncated: false, changed_files: [], validation: null, live: null };
}

const timeline: PlatformGoalTimeline = {
  goal: { id: "g", title: "t", objective: "o", status: "BLOCKED", repository: "r" }, plan: [],
  steps: [{ plan_task_id: "T001", title: "#1458 [Routing] implement", status: "FAILED", attempts: [
    attempt(1, "task-1", "FAILED", "magpie-opencode-zen-free-deepseek-v4.1-flash-free", { classification: "timeout", detail: "opencode_timeout:3600", message: "OpenCode timeout" }),
    { ...attempt(2, "task-2", "FAILED", "magpie-codex-gpt-6.1-sol", { classification: "deterministic_validation_failure", detail: "functional_check_failed", message: "Functional check failed" }),
      changed_files: [{ path: "a.py", status: "modified", additions: 10, deletions: 2 }, { path: "b.py", status: "added", additions: 5, deletions: 0 }] },
    attempt(3, "task-3", "FAILED", "magpie-codex-gpt-6.1-sol", null),
  ] }],
};

describe("GoalTimeline attempts", () => {

  it("reads as one story: every attempt in order with its own reason", () => {
    render(<MemoryRouter><GoalTimeline goal={GOAL} timeline={timeline} /></MemoryRouter>);
    expect(screen.getByTestId("timeline-attempt-task-1")).toHaveTextContent("第 1 次 · OpenCode · deepseek-v4.1-flash-free");
    expect(screen.getByTestId("timeline-stop-task-1")).toHaveTextContent("执行超过时间上限");
    expect(screen.getByTestId("timeline-stop-task-2")).toHaveTextContent("功能检查没有通过");
    expect(screen.getByTestId("timeline-files-task-2")).toHaveTextContent("改了 2 个文件 · +15 −2");
    // The current attempt takes its reason from the goal detail, the authority for status.
    expect(screen.getByTestId("timeline-stop-task-3")).toHaveTextContent("执行器异常退出");
    expect(screen.getByTestId("goal-timeline-status")).toHaveTextContent("已停下：执行器异常退出");
  });

  it("shows a new current attempt from the goal detail before the timeline has it", () => {
    const stale = { ...timeline, steps: [{ ...timeline.steps[0], attempts: timeline.steps[0].attempts.slice(0, 2) }] };
    const [step] = mergeTimelineSteps(GOAL, stale);
    expect(step.attempts.map((a) => a.task_id)).toEqual(["task-1", "task-2", "task-3"]);
    expect(timelineStatusLine({ ...stale, steps: [step] }).tone).toBe("stopped");
  });

  it("does not raise an alarm for a task the Owner cancelled", () => {
    const cancelled = { ...GOAL, task_links: [{ ...GOAL.task_links![0], status: "CANCELLED", failure: null }] } as PlatformGoal;
    render(<MemoryRouter><GoalTimeline goal={cancelled} /></MemoryRouter>);
    expect(screen.queryByTestId("timeline-stop-task-3")).not.toBeInTheDocument();
  });
});

describe("older runs and stop details", () => {
  it("shows what an older run kept: the agent's sentences, a tool count and its summary", () => {
    const legacy = { ...attempt(2, "task-3", "FAILED", "magpie-codex-gpt-6.1-sol", null),
      narration: [{ timestamp: "", text: "I��ll read the local scope first." }], tool_actions: 23,
      summary: "Implemented #1458 in the supplied worktree.\n\n- Added CLI discovery...[TRUNCATED]" };
    render(<MemoryRouter><GoalTimeline goal={GOAL} timeline={{ goal: timeline.goal, plan: [], steps: [{ ...timeline.steps[0], attempts: [legacy] }] }} /></MemoryRouter>);
    expect(screen.getByText("I'll read the local scope first.")).toBeInTheDocument();
    expect(screen.getByTestId("timeline-legacy-tools-task-3")).toHaveTextContent("调用了 23 次工具");
    expect(screen.getByTestId("timeline-summary-task-3")).toHaveTextContent("Implemented #1458");
    expect(screen.getByTestId("timeline-summary-task-3").textContent).not.toContain("[TRUNCATED]");
  });

  it("states a failed check in plain words and keeps the raw text folded", () => {
    const text = "Functional check failed: Reason: functional_check_failed python_pytest tests/a.py: exit 1, 180 passed, 1 failed FAILED tests.test_model_access.TestOriginGateHttpBoundary::test_foreign_origin_error_body_no_secret: ConnectionAbortedError";
    expect(checkSummary(text)).toBe("功能检查：180 个通过，1 个失败（test_foreign_origin_error_body_no_secret）");
    expect(checkSummary("nothing to parse")).toBe("");
    render(<MemoryRouter><GoalTimeline goal={GOAL} timeline={timeline} /></MemoryRouter>);
    const card = screen.getByTestId("timeline-stop-task-2");
    expect(card.querySelector("details")).not.toHaveAttribute("open");
    expect(card.querySelector("details")).toHaveTextContent("技术细节");
  });

  it("counts folded tool calls by kind", () => {
    const e = (category: PlatformRunActivityEvent["category"]) => ({ id: category, task_id: "t", timestamp: "", category, title: "", description: "" }) as PlatformRunActivityEvent;
    expect(actionsSummary([e("READ"), e("READ"), e("SEARCH"), e("EDIT"), e("COMMAND"), e("PLAN")])).toBe("读取 2 个文件、搜索 1 次、修改 1 处、运行 1 条命令、其他 1 个动作");
    expect(cleanSpeech("I��ll go...[TRUNCATED]")).toBe("I'll go…");
  });
});

describe("run explanation helpers", () => {
  it("prefers a specific code found in the detail and never shows a bare class as the label", () => {
    expect(failureText({ classification: "executor_nonzero", detail: "x", message: "" }).label).toBe("执行器异常退出");
    expect(failureText({ classification: "something_new", detail: "", message: "m" }).label).toBe("已停止");
    expect(failureText({ classification: "executor_stalled", detail: "planner_failed:opencode_stalled:900", message: "" }).label)
      .toBe("Agent 长时间没有任何输出，已被停止");
    expect(modelName("magpie-codex-gpt-6.1-sol")).toBe("codex-gpt-6.1-sol");
  });

  it("keeps only actions worth reading and names models and agents plainly", () => {
    const e = (id: string, category: PlatformRunActivityEvent["category"], title: string, extra: Partial<PlatformRunActivityEvent> = {}) =>
      ({ id, task_id: "t", timestamp: "", category, title, description: "", ...extra }) as PlatformRunActivityEvent;
    const kept = meaningfulEvents([
      e("1", "AGENT_STARTED", "Agent started"),
      e("2", "PLAN", "Model selected", { description: "codex/gpt-6.1-sol [magpie-codex-gpt-6.1-sol]: escalation (difficulty 3). Candidates: a; b; c" }),
      e("3", "BLOCKED", "Run blocked", { description: "failure_classification=executor_stalled" }),
      e("4", "BLOCKED", "Run blocked", { description: "OpenCode CLI wrote nothing for too long" }),
      e("5", "AGENT_COMPLETED", "Agent completed"),
      e("6", "READ", "Repository read", { path: "a.py" }),
    ]);
    expect(kept.map((x) => x.id)).toEqual(["2", "4", "6"]);
    expect(eventDetail(kept[0])).toBe("选择模型：codex/gpt-6.1-sol");
    expect(readableAgent(e("7", "READ", "x", { agent: { agent_id: "a", role: "", display_name: "agent-51fb3021bce33d5a" } }))).toBe("");
    expect(readableAgent(e("8", "READ", "x", { agent: { agent_id: "a", role: "coder", display_name: "Coder" } }))).toBe("Coder");
  });

  it("merges adjacent rows that say the same thing", () => {
    const row = (id: string, title: string, description = "") => ({
      key: id, event: { id, title, category: "AGENT_STARTED", description } as PlatformRunActivityEvent,
    });
    const rows = collapseRepeats([row("1", "Agent started"), row("2", "Agent started"), row("3", "Agent started", "read a.py"), row("4", "Agent started")]);
    expect(rows.map((r) => r.repeats)).toEqual([2, 1, 1]);
  });
});
