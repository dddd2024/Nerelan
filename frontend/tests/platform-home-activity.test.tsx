import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { type ReactNode } from "react";
import { render as rtlRender, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { __setMockGoalStatus, __setMockRuns, type PlatformAgentRun, type PlatformRunActivityEvent } from "@/lib/platform-client";
import { HomePage } from "@/routes/home";

const GOAL_ID = "goal-demo-platform";

function makeWrapper() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity, staleTime: 0 },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/"]}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

function minutesAgo(minutes: number) {
  return new Date(Date.now() - minutes * 60_000).toISOString();
}

function secondsAgo(seconds: number) {
  return new Date(Date.now() - seconds * 1_000).toISOString();
}

function activity(
  id: string,
  taskId: string,
  category: PlatformRunActivityEvent["category"],
  title: string,
  timestamp: string,
  agentName?: string,
  extra: Partial<PlatformRunActivityEvent> = {},
): PlatformRunActivityEvent {
  return {
    id,
    task_id: taskId,
    timestamp,
    category,
    title,
    description: "",
    agent: agentName
      ? { agent_id: agentName.toLowerCase(), role: agentName.toLowerCase(), display_name: agentName }
      : undefined,
    ...extra,
  };
}

function makeRun(overrides: Partial<PlatformAgentRun> & { task_id: string }): PlatformAgentRun {
  return {
    title: `[演示] ${overrides.task_id}`,
    repository: "dddd2024/reverse-agent",
    status: "RUNNING",
    state: "RUNNING",
    executor_kind: "opencode",
    orchestration_mode: "sequential_team",
    created_at: minutesAgo(30),
    updated_at: minutesAgo(1),
    failure_classification: "",
    goal_id: GOAL_ID,
    goal_title: "完善无人值守多 Agent 平台",
    window_id: "window-demo",
    liveness: "ACTIVE",
    last_activity_at: secondsAgo(4),
    current_activity: null,
    current_agent: null,
    agents: [],
    change_summary: null,
    validation: null,
    events: [],
    activity: [],
    changed_files: [],
    usage: {
      status: "USAGE_UNKNOWN",
      input_units: 0,
      output_units: 0,
      reasoning_units: 0,
      cache_read_units: 0,
      cache_write_units: 0,
      cost_micro_units: 0,
      total_token_units: 0,
      observation_count: 0,
      unknown_observation_count: 0,
      provenance_ids: [],
      per_role: [],
    },
    budget: null,
    publication: null,
    controls: {
      cancel: {
        action: "CANCEL",
        scope: "QUEUE_ONLY",
        availability: "UNAVAILABLE",
        reason_code: "STATUS_NOT_CANCELLABLE",
      },
    },
    ...overrides,
  };
}

const defaultRuns: PlatformAgentRun[] = [];

describe("Home compact activity stream (OBS-1)", () => {
  beforeEach(() => {
    __setMockRuns(defaultRuns);
  });

  afterEach(() => {
    __setMockRuns(defaultRuns);
  });

  it("shows current semantic activity, recent events, liveness and agent attribution for an active run", async () => {
    const run = makeRun({
      task_id: "t-active",
      current_activity: {
        category: "READ",
        title: "正在检查上传接口的文件校验逻辑",
        description: "读取相关实现以定位问题。",
        agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
        timestamp: secondsAgo(4),
      },
      current_agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
      change_summary: { file_count: 3, additions: 42, deletions: 11 },
      activity: [
        activity("a1", "t-active", "READ", "读取 upload_service.py", secondsAgo(8), "Coder", { path: "upload_service.py" }),
        activity("a2", "t-active", "EDIT", "修改 validation.py", secondsAgo(12), "Coder", { path: "validation.py" }),
        activity("a3", "t-active", "COMMAND", "运行单元测试", secondsAgo(20), "Test Agent", {
          command: { summary: "pytest tests/test_upload.py -q", status: "RUNNING" },
        }),
      ],
    });
    __setMockRuns([run]);
    __setMockGoalStatus(GOAL_ID, {
      status: "RUNNING",
      task_links: [
        { task_id: "t-active", plan_task_id: "T001", status: "RUNNING", title: "实现上传逻辑修复" },
      ],
    });

    rtlRender(<HomePage />, { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("goal-current-activity")).toBeTruthy();
    });

    expect(screen.getByTestId("goal-current-activity-now").textContent).toContain("正在检查上传接口的文件校验逻辑");
    expect(screen.getByTestId("goal-current-activity-now").textContent).toContain("Coder");
    expect(screen.getByTestId("goal-current-activity-now").textContent).toContain("读取");

    const liveness = screen.getByTestId("goal-activity-liveness");
    expect(liveness.textContent).toContain("有新活动");

    expect(screen.getByTestId("goal-activity-event-a1").textContent).toContain("读取 upload_service.py");
    expect(screen.getByTestId("goal-activity-event-a1").textContent).toContain("Coder");
    expect(screen.getByTestId("goal-activity-event-a2").textContent).toContain("validation.py");
    expect(screen.getByTestId("goal-activity-event-a3").textContent).toContain("pytest tests/test_upload.py -q");
    expect(screen.getByTestId("goal-activity-event-a3").textContent).toContain("Test Agent");

    expect(screen.getByTestId("goal-activity-change-summary").textContent).toContain("3 个文件变更");
    expect(screen.getByTestId("goal-activity-change-summary").textContent).toContain("+42");
    expect(screen.getByTestId("goal-activity-change-summary").textContent).toContain("-11");

    const link = screen.getByTestId("goal-activity-full-run-link") as HTMLAnchorElement;
    expect(link.getAttribute("href")).toBe("/runs");
  });

  it("distinguishes a waiting run from active work", async () => {
    __setMockRuns([
      makeRun({
        task_id: "t-waiting",
        state: "RUNNING",
        liveness: "WAITING",
        last_activity_at: minutesAgo(2),
        current_activity: {
          category: "AGENT_WAITING",
          title: "等待模型响应",
          description: "执行器等待上游响应。",
          agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
          timestamp: minutesAgo(2),
        },
      }),
    ]);
    __setMockGoalStatus(GOAL_ID, {
      status: "RUNNING",
      task_links: [{ task_id: "t-waiting", plan_task_id: "T001", status: "RUNNING", title: "等待中的任务" }],
    });

    rtlRender(<HomePage />, { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("goal-activity-liveness")).toBeTruthy();
    });
    expect(screen.getByTestId("goal-activity-liveness").textContent).toContain("等待中");
    expect(screen.getByTestId("goal-activity-liveness").textContent).not.toContain("有新活动");
  });

  it("distinguishes a blocked / owner-action-required run", async () => {
    __setMockRuns([
      makeRun({
        task_id: "t-blocked",
        state: "BLOCKED_EXTERNAL",
        status: "BLOCKED_EXTERNAL",
        liveness: "OWNER_ACTION_REQUIRED",
        last_activity_at: minutesAgo(3),
        activity: [
          activity("b1", "t-blocked", "OWNER_ACTION_REQUIRED", "等待 Owner 审查", minutesAgo(3), "Reviewer"),
        ],
      }),
    ]);
    __setMockGoalStatus(GOAL_ID, {
      status: "RUNNING",
      task_links: [{ task_id: "t-blocked", plan_task_id: "T001", status: "RUNNING", title: "阻塞任务" }],
    });

    rtlRender(<HomePage />, { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("goal-activity-liveness")).toBeTruthy();
    });
    expect(screen.getByTestId("goal-activity-liveness").textContent).toContain("需要 Owner 处理");
    expect(screen.getByTestId("goal-activity-event-b1").textContent).toContain("Reviewer");
  });

  it("flags a stale run instead of presenting it as active", async () => {
    __setMockRuns([
      makeRun({
        task_id: "t-stale",
        state: "RUNNING",
        liveness: "STALE",
        last_activity_at: minutesAgo(12),
        current_activity: {
          category: "COMMAND",
          title: "运行集成测试",
          description: "命令仍在执行。",
          agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
          timestamp: minutesAgo(12),
        },
      }),
    ]);
    __setMockGoalStatus(GOAL_ID, {
      status: "RUNNING",
      task_links: [{ task_id: "t-stale", plan_task_id: "T001", status: "RUNNING", title: "疑似停滞任务" }],
    });

    rtlRender(<HomePage />, { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("goal-activity-liveness")).toBeTruthy();
    });
    expect(screen.getByTestId("goal-activity-liveness").textContent).toContain("12 分钟没有新活动");
    expect(screen.getByTestId("goal-activity-liveness").textContent).not.toContain("前有新活动");
  });

  it("attributes parallel events to multiple agents and summarizes concurrency", async () => {
    __setMockRuns([
      makeRun({
        task_id: "t-parallel-1",
        current_agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
        current_activity: {
          category: "EDIT",
          title: "修改认证实现",
          description: "更新 auth/service.py。",
          agent: { agent_id: "coder", role: "coder", display_name: "Coder" },
          timestamp: secondsAgo(5),
        },
        activity: [activity("p1", "t-parallel-1", "EDIT", "修改 auth/service.py", secondsAgo(5), "Coder")],
      }),
      makeRun({
        task_id: "t-parallel-2",
        current_agent: { agent_id: "test", role: "test", display_name: "Test Agent" },
        current_activity: {
          category: "COMMAND",
          title: "运行集成测试",
          description: "执行 pytest。",
          agent: { agent_id: "test", role: "test", display_name: "Test Agent" },
          timestamp: secondsAgo(6),
        },
        activity: [activity("p2", "t-parallel-2", "TEST", "运行集成测试", secondsAgo(6), "Test Agent", {
          test: { summary: "pytest tests/integration -q", status: "RUNNING" },
        })],
      }),
    ]);
    __setMockGoalStatus(GOAL_ID, {
      status: "RUNNING",
      task_links: [
        { task_id: "t-parallel-1", plan_task_id: "T001", status: "RUNNING", title: "认证修复" },
        { task_id: "t-parallel-2", plan_task_id: "T002", status: "RUNNING", title: "集成测试" },
      ],
    });

    rtlRender(<HomePage />, { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("goal-activity-agents")).toBeTruthy();
    });
    const agents = screen.getByTestId("goal-activity-agents").textContent ?? "";
    expect(agents).toContain("2 个 Agent 并行");
    expect(agents).toContain("Coder");
    expect(agents).toContain("Test Agent");

    expect(screen.getByTestId("goal-activity-event-p1").textContent).toContain("Coder");
    expect(screen.getByTestId("goal-activity-event-p2").textContent).toContain("Test Agent");
    expect(screen.getByTestId("goal-activity-event-p2").textContent).toContain("pytest tests/integration -q");
  });

  it("keeps the panel hidden when the goal has no linked runs", async () => {
    __setMockRuns([
      makeRun({ task_id: "unrelated-run" }),
    ]);
    __setMockGoalStatus(GOAL_ID, {
      status: "RUNNING",
      task_links: [{ task_id: "t-no-match", plan_task_id: "T001", status: "RUNNING", title: "没有关联运行" }],
    });

    rtlRender(<HomePage />, { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("platform-home")).toBeTruthy();
    });
    expect(screen.queryByTestId("goal-current-activity")).toBeNull();
  });

  it("presents terminal runs without claiming active work", async () => {
    __setMockRuns([
      makeRun({
        task_id: "t-terminal",
        state: "READY_FOR_HUMAN",
        status: "READY_FOR_REVIEW",
        liveness: "TERMINAL",
        last_activity_at: minutesAgo(5),
        current_activity: null,
        change_summary: { file_count: 2, additions: 18, deletions: 6 },
        activity: [
          activity("term1", "t-terminal", "VERIFY", "验证通过", minutesAgo(5), "Reviewer", {
            stage: "VERIFY",
            test: { summary: "pytest tests/platform_v1 -q", status: "PASS", exit_code: 0 },
          }),
        ],
      }),
    ]);
    __setMockGoalStatus(GOAL_ID, {
      status: "RUNNING",
      task_links: [{ task_id: "t-terminal", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "已完成任务" }],
    });

    rtlRender(<HomePage />, { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("goal-current-activity")).toBeTruthy();
    });
    expect(screen.queryByTestId("goal-current-activity-now")).toBeNull();
    expect(screen.getByTestId("goal-activity-liveness").textContent).toContain("已结束");
    expect(screen.getByTestId("goal-activity-event-term1").textContent).toContain("验证");
    expect(screen.getByTestId("goal-activity-event-term1").textContent).toContain("验证");
    expect(screen.getByTestId("goal-activity-change-summary").textContent).toContain("2 个文件变更");
  });

  it("caps recent events to the compact limit", async () => {
    __setMockRuns([
      makeRun({
        task_id: "t-capped",
        activity: Array.from({ length: 9 }, (_, index) =>
          activity(`cap-${index}`, "t-capped", "READ", `事件 ${index}`, minutesAgo(index + 1), "Coder"),
        ),
      }),
    ]);
    __setMockGoalStatus(GOAL_ID, {
      status: "RUNNING",
      task_links: [{ task_id: "t-capped", plan_task_id: "T001", status: "RUNNING", title: "事件上限任务" }],
    });

    rtlRender(<HomePage />, { wrapper: makeWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("goal-activity-events")).toBeTruthy();
    });
    const items = screen.getByTestId("goal-activity-events").querySelectorAll("li");
    expect(items.length).toBe(5);
  });
});
