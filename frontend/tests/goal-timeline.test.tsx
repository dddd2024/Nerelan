import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { type ReactNode } from "react";
import { render, render as rtlRender, screen, waitFor, within } from "@testing-library/react";
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
import { GoalThread } from "@/components/goal-thread";
import { checkSummary, cleanSpeech, mergeTimelineSteps, timelineStatusLine } from "@/components/goal-timeline";
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

/** One attempt's assistant message (assistant-ui keys it by the attempt's task id). */
function turn(taskId: string): HTMLElement {
  const message = document.querySelector<HTMLElement>(`[data-testid="thread-assistant-message"][data-message-id="${taskId}"]`);
  if (!message) throw new Error(`no assistant message for ${taskId}`);
  return message;
}

describe("Home goal thread", () => {
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
    await waitFor(() => expect(within(turn(run.task_id)).getAllByTestId("thread-attempt-header")).toHaveLength(1));
  }

  it("shows each action in order with its detail, and says what the attempt is doing now", async () => {
    await mount(makeRun({ task_id: "t-active", activity: [
      activity("a1", "READ", "Repository read", { path: "upload_service.py", agent: { agent_id: "coder", role: "coder", display_name: "Coder" } }),
      activity("a2", "EDIT", "Repository change", { path: "validation.py" }),
      activity("a3", "COMMAND", "Approved command", { command: { summary: "pytest tests/test_upload.py -q", status: "RUNNING" },
        agent: { agent_id: "test", role: "test", display_name: "Test Agent" } }),
    ] }));
    // The timeline (with the attempt's actions) arrives after the goal detail.
    await waitFor(() => expect(screen.getByTestId("thread-tool-a3")).toBeInTheDocument());
    const message = turn("t-active");
    expect(within(message).getByTestId("thread-tool-group").querySelector("summary")).toHaveTextContent("读取 1 个文件、修改 1 处、运行 1 条命令");
    expect(screen.getByTestId("thread-tool-a1")).toHaveTextContent("upload_service.py");
    expect(screen.getByTestId("thread-tool-a2")).toHaveTextContent("validation.py");
    expect(screen.getByTestId("thread-tool-a3")).toHaveTextContent("pytest tests/test_upload.py -q");
    // Actions keep their order.
    const ids = [...message.querySelectorAll("[data-testid^='thread-tool-a']")].map((row) => row.getAttribute("data-testid"));
    expect(ids).toEqual(["thread-tool-a1", "thread-tool-a2", "thread-tool-a3"]);
    // The server's generic English category titles never show beside the detail.
    expect(screen.getByTestId("thread-tool-a2").textContent).not.toContain("Repository change");
    const header = within(message).getByTestId("thread-attempt-header");
    expect(header).toHaveTextContent("OpenCode · codex-gpt-6.1-sol");
    expect(header).toHaveTextContent("有新活动");
    expect(screen.getByTestId("goal-state-label")).toHaveTextContent("进行中");
    // Semantic activity, never an exact wall-clock stamp.
    expect(message.textContent).not.toContain("09:41");
  });

  it.each([["WAITING", "等待中"], ["STALE", "疑似停滞"], ["VALIDATING", "验证中"]])(
    "labels %s liveness instead of presenting it as active work", async (state, label) => {
      await mount(makeRun({ task_id: "t-active", liveness: state as PlatformAgentRun["liveness"], activity: [activity("a1", "READ", "Repository read", { path: "a.py" })] }));
      await waitFor(() => expect(within(turn("t-active")).getByTestId("thread-attempt-header")).toHaveTextContent(label));
      expect(within(turn("t-active")).getByTestId("thread-attempt-header")).not.toHaveTextContent("有新活动");
    });

  it("puts the stop reason where the attempt stopped and leads with it", async () => {
    await mount(makeRun({ task_id: "t-active", status: "FAILED", state: "FAILED", liveness: "TERMINAL",
      activity: [activity("a1", "BLOCKED", "Run blocked", { description: "OpenCode CLI wrote nothing for too long (often a provider 429 it waits out)" })] }),
    "FAILED", { failure: { classification: "executor_stalled", detail: "opencode_stalled:900", message: "OpenCode stalled: OpenCode CLI wrote nothing for too long" } });
    const message = turn("t-active");
    const stop = within(message).getByTestId("thread-stop");
    expect(stop).toHaveAttribute("role", "alert");
    expect(stop).toHaveTextContent("停下了：Agent 长时间没有任何输出，已被停止");
    expect(stop).toHaveTextContent("最常见的原因是模型被限流（429）");
    expect(within(message).getByTestId("thread-attempt-header")).toHaveTextContent("停下");
    expect(within(message).getByTestId("thread-attempt-header")).not.toHaveTextContent("有新活动");
    expect(screen.getByTestId("goal-state-label")).toHaveTextContent("已停下");
  });

  it("presents finished work without claiming it is still running", async () => {
    await mount(makeRun({ task_id: "t-active", status: "READY_FOR_REVIEW", state: "READY_FOR_REVIEW", liveness: "TERMINAL",
      activity: [activity("a1", "EDIT", "Repository change", { path: "a.py" })] }), "READY_FOR_REVIEW");
    expect(within(turn("t-active")).getByTestId("thread-attempt-header")).toHaveTextContent("完成");
    expect(within(turn("t-active")).getByTestId("thread-attempt-header")).not.toHaveTextContent("进行中");
    expect(screen.getByTestId("goal-state-label")).toHaveTextContent("待审查");
    expect(screen.queryByText("有新活动")).not.toBeInTheDocument();
    expect(screen.queryByText("Agent 正在执行")).not.toBeInTheDocument();
  });

  it("shows the agent's words as prose and folds its tool calls like an agent chat", async () => {
    const say = (id: string, text: string) => activity(id, "PLAN", "OpenCode", { type: "EXECUTOR_PROGRESS", progress_kind: "text", description: text });
    const tool = (id: string, category: PlatformRunActivityEvent["category"], path: string) =>
      activity(id, category, "OpenCode", { type: "EXECUTOR_PROGRESS", description: `x ${path}`, path });
    await mount(makeRun({ task_id: "t-active", activity: [
      say("s1", "I'll read the **routing** code first."),
      tool("t1", "READ", "a.py"), tool("t2", "READ", "b.py"), tool("t3", "COMMAND", "pytest"),
      say("s2", "Now I'll add the detector."),
      tool("t4", "EDIT", "c.py"),
    ] }));
    // A running turn's prose streams in, as in an agent chat.
    await waitFor(() => expect(turn("t-active")).toHaveTextContent("Now I'll add the detector."));
    const message = turn("t-active");
    // The agent's words are markdown.
    expect(within(message).getByText("routing").tagName).toBe("STRONG");
    const groups = within(message).getAllByTestId("thread-tool-group");
    expect(groups).toHaveLength(2);
    expect(groups[0].querySelector("summary")).toHaveTextContent("读取 2 个文件、运行 1 条命令");
    expect(groups[1].querySelector("summary")).toHaveTextContent("修改 1 处");
    expect(within(groups[0]).getByTestId("thread-tool-t2")).toHaveTextContent("b.py");
    // Prose and tool calls stay in the order the agent produced them.
    const first = within(message).getByText(/read the/);
    expect(first.compareDocumentPosition(groups[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("lists the plan's steps before any has started", async () => {
    __setMockGoalStatus(GOAL_ID, { status: "RUNNING", task_links: [
      { task_id: "q1", plan_task_id: "T001", status: "QUEUED", title: "实现上传逻辑修复" },
      { task_id: "q2", plan_task_id: "T002", status: "QUEUED", title: "审查改动" },
    ] });
    rtlRender(<HomePage />, { wrapper: makeWrapper() });
    await waitFor(() => expect(screen.getByTestId("goal-panel-step-T002")).toBeInTheDocument());
    expect(screen.getByTestId("goal-panel-step-T001")).toHaveTextContent("实现上传逻辑修复");
    const headers = screen.getAllByTestId("thread-attempt-header");
    expect(headers).toHaveLength(2);
    for (const header of headers) expect(header).toHaveTextContent("等待开始");
  });

  // A goal with a plan but no task links yet (e.g. PLANNED) still shows its steps.
  it("lists the plan before any task has been dispatched", async () => {
    __setMockGoalStatus(GOAL_ID, { status: "PLANNED", task_links: [] });
    rtlRender(<HomePage />, { wrapper: makeWrapper() });
    await waitFor(() => expect(screen.getByTestId("goal-panel")).toBeInTheDocument());
    await waitFor(() => expect(screen.getByTestId("goal-panel").querySelectorAll("[data-testid^='goal-panel-step-']").length).toBeGreaterThan(0), { timeout: 1500 });
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

function renderThread(goal: PlatformGoal, data?: PlatformGoalTimeline) {
  return render(<MemoryRouter><GoalThread goal={goal} timeline={data} /></MemoryRouter>);
}

describe("GoalThread attempts", () => {

  it("reads as one story: every attempt in order with its own reason", () => {
    renderThread(GOAL, timeline);
    const turns = screen.getAllByTestId("thread-assistant-message").map((message) => message.getAttribute("data-message-id"));
    expect(turns).toEqual(["task-1", "task-2", "task-3"]);
    const first = within(turn("task-1")).getByTestId("thread-attempt-header");
    expect(first).toHaveTextContent("第 1 次");
    expect(first).toHaveTextContent("OpenCode · deepseek-v4.1-flash-free");
    expect(within(turn("task-1")).getByTestId("thread-stop")).toHaveTextContent("执行超过时间上限");
    expect(within(turn("task-2")).getByTestId("thread-stop")).toHaveTextContent("功能检查没有通过");
    const files = within(turn("task-2")).getByTestId("thread-files");
    expect(files).toHaveTextContent("改了 2 个文件");
    expect(files).toHaveTextContent("+15");
    expect(files).toHaveTextContent("−2");
    // The current attempt takes its reason from the goal detail, the authority for status.
    expect(within(turn("task-3")).getByTestId("thread-stop")).toHaveTextContent("停下了：执行器异常退出");
    // The side panel lists the step once, with its attempt count and what changed.
    expect(screen.getByTestId("goal-panel-step-T001")).toHaveTextContent("3 次");
    expect(screen.getByTestId("goal-panel-files")).toHaveTextContent("a.py");
    expect(screen.getByRole("link", { name: "查看完整运行记录" })).toHaveAttribute("href", "/runs?goal=g");
  });

  it("marks a host-retried attempt as interrupted-and-retried instead of a red stop card", () => {
    const retried = { ...timeline, steps: [{ ...timeline.steps[0], attempts: [
      { ...attempt(1, "task-1", "FAILED", "magpie-codex-gpt-6.1-sol", { classification: "executor_terminated", detail: "host_restart", message: "Executor terminated" }), retry_reason: "host_retry:restart" },
      attempt(2, "task-2", "FAILED", "magpie-codex-gpt-6.1-sol", { classification: "timeout", detail: "opencode_timeout:3600", message: "OpenCode timeout" }),
    ] }] } as PlatformGoalTimeline;
    renderThread(GOAL, retried);
    expect(within(turn("task-1")).getByTestId("thread-attempt-header")).toHaveTextContent("被中断，已自动重试");
    expect(within(turn("task-1")).queryByTestId("thread-stop")).not.toBeInTheDocument();
    expect(within(turn("task-2")).getByTestId("thread-attempt-header")).not.toHaveTextContent("被中断，已自动重试");
  });

  it("shows a new current attempt from the goal detail before the timeline has it", () => {
    const stale = { ...timeline, steps: [{ ...timeline.steps[0], attempts: timeline.steps[0].attempts.slice(0, 2) }] };
    const [step] = mergeTimelineSteps(GOAL, stale);
    expect(step.attempts.map((a) => a.task_id)).toEqual(["task-1", "task-2", "task-3"]);
    expect(timelineStatusLine({ ...stale, steps: [step] }).tone).toBe("stopped");
    renderThread(GOAL, stale);
    expect(within(turn("task-3")).getByTestId("thread-stop")).toHaveAttribute("role", "alert");
  });

  it("does not raise an alarm for a task the Owner cancelled", () => {
    const cancelled = { ...GOAL, task_links: [{ ...GOAL.task_links![0], status: "CANCELLED", failure: null }] } as PlatformGoal;
    renderThread(cancelled);
    expect(screen.queryByTestId("thread-stop")).not.toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("older runs and stop details", () => {
  it("shows what an older run kept: the agent's sentences and its summary", () => {
    const legacy = { ...attempt(2, "task-3", "FAILED", "magpie-codex-gpt-6.1-sol", null),
      narration: [{ timestamp: "", text: "I��ll read the local scope first." }], tool_actions: 23,
      summary: "Implemented #1458 in the supplied worktree.\n\n- Added CLI discovery...[TRUNCATED]" };
    renderThread(GOAL, { goal: timeline.goal, plan: [], steps: [{ ...timeline.steps[0], attempts: [legacy] }] });
    const message = turn("task-3");
    expect(within(message).getByText("I'll read the local scope first.")).toBeInTheDocument();
    expect(message).toHaveTextContent("Implemented #1458");
    // The summary's markdown list renders as a list.
    expect(within(message).getByRole("listitem")).toHaveTextContent("Added CLI discovery…");
    expect(message.textContent).not.toContain("[TRUNCATED]");
  });

  it("states a failed check in plain words and keeps the raw text folded", () => {
    const text = "Functional check failed: Reason: functional_check_failed python_pytest tests/a.py: exit 1, 180 passed, 1 failed FAILED tests.test_model_access.TestOriginGateHttpBoundary::test_foreign_origin_error_body_no_secret: ConnectionAbortedError";
    expect(checkSummary(text)).toBe("功能检查：180 个通过，1 个失败（test_foreign_origin_error_body_no_secret）");
    expect(checkSummary("nothing to parse")).toBe("");
    renderThread(GOAL, timeline);
    // An attempt a later one already retried is history: a muted line, not an alert card.
    const earlier = within(turn("task-2")).getByTestId("thread-stop");
    expect(earlier).not.toHaveAttribute("role");
    expect(earlier).toHaveTextContent("之后已重试");
    // The latest attempt keeps the alert card with its raw detail folded.
    const latest = within(turn("task-3")).getByTestId("thread-stop");
    expect(latest).toHaveAttribute("role", "alert");
    expect(latest.querySelector("details")).not.toHaveAttribute("open");
    expect(latest.querySelector("details")).toHaveTextContent("技术细节");
    expect(screen.getAllByRole("alert")).toHaveLength(1);
  });

  it("cleans stored speech", () => {
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
