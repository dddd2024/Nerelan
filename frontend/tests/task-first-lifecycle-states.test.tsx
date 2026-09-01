import { afterEach, describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { GoalCurrentActivity } from "@/components/goal-current-activity";
import { GoalProgress } from "@/components/goal-progress";
import { HomePage } from "@/routes/home";
import {
  __setMockGoalStatus,
  type PlatformAgentRun,
  type PlatformGoal,
  type PlatformRunActivityEvent,
} from "@/lib/platform-client";
import { renderWithProviders } from "./test-utils";

// R3 handoff note: connection-degraded fixed-viewport acceptance stays separate.
// The current Goal/Run read model exposes run liveness, not connection-health truth.
// Do not synthesize a connection-health state into Goal or Run fixtures to make a visual case pass.

const GOAL_ID = "goal-demo-platform";

const ORIGINAL_LINKS = [
  { task_id: "task-demo-1", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "分析目标与代码库" },
  { task_id: "task-demo-2", plan_task_id: "T002", status: "RUNNING", title: "实现协调与恢复链路" },
  { task_id: "task-demo-3", plan_task_id: "T003", status: "QUEUED", title: "验证并准备证据" },
];

const BASE_GOAL: PlatformGoal = {
  id: "goal-lifecycle-v10",
  title: "Lifecycle presentation",
  objective: "Prove bounded task-first state presentation.",
  repository: "dddd2024/reverse-agent",
  status: "RUNNING",
  revision: 1,
  spec_markdown: "",
  plan_markdown: "",
  tasks: [],
  acceptance_criteria: [],
  artifact_digest: "",
  executor_kind: "opencode",
  orchestration_mode: "sequential_team",
  binding_ref: "",
  window_id: "window-v10",
  created_at: "2026-09-01T10:00:00Z",
  updated_at: "2026-09-01T10:10:00Z",
  task_links: [],
};

function event(
  id: string,
  taskId: string,
  category: PlatformRunActivityEvent["category"],
  title: string,
  minute: number,
): PlatformRunActivityEvent {
  return {
    id,
    task_id: taskId,
    timestamp: `2026-09-01T10:${String(minute).padStart(2, "0")}:00Z`,
    category,
    title,
    description: "",
    stage: category === "VERIFY" || category === "TEST" ? "VERIFY" : "EXECUTE",
  };
}

function run(
  taskId: string,
  overrides: Partial<PlatformAgentRun> = {},
): PlatformAgentRun {
  return {
    task_id: taskId,
    title: `[Lifecycle] ${taskId}`,
    repository: "dddd2024/reverse-agent",
    status: "RUNNING",
    state: "RUNNING",
    executor_kind: "opencode",
    orchestration_mode: "sequential_team",
    created_at: "2026-09-01T10:00:00Z",
    updated_at: "2026-09-01T10:10:00Z",
    failure_classification: "",
    goal_id: BASE_GOAL.id,
    goal_title: BASE_GOAL.title,
    window_id: BASE_GOAL.window_id,
    liveness: "ACTIVE",
    last_activity_at: new Date().toISOString(),
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
    ...overrides,
  };
}

afterEach(() => {
  __setMockGoalStatus(GOAL_ID, {
    status: "RUNNING",
    task_links: ORIGINAL_LINKS,
  });
});

describe("task-first lifecycle-state convergence before R3 visual acceptance", () => {
  it("presents validating liveness explicitly rather than as healthy active work", () => {
    const goal: PlatformGoal = {
      ...BASE_GOAL,
      task_links: [
        { task_id: "validate", plan_task_id: "T001", status: "VALIDATING", title: "验证候选结果" },
      ],
    };
    const validatingRun = run("validate", {
      liveness: "VALIDATING",
      current_agent: { agent_id: "reviewer", role: "reviewer", display_name: "Reviewer" },
      current_activity: {
        category: "VERIFY",
        title: "正在运行独立验证",
        description: "等待确定性验证完成。",
        agent: { agent_id: "reviewer", role: "reviewer", display_name: "Reviewer" },
        timestamp: new Date().toISOString(),
      },
    });

    renderWithProviders(<GoalCurrentActivity goal={goal} runs={[validatingRun]} />);

    const liveness = screen.getByTestId("goal-activity-liveness");
    expect(liveness).not.toHaveClass("sr-only");
    expect(liveness).toHaveTextContent("验证中");
    expect(liveness).not.toHaveTextContent("有新活动");
    expect(screen.getByTestId("goal-current-activity-now")).toHaveTextContent("正在运行独立验证");
  });

  it("presents a plain blocked run independently from Owner-action-required state", () => {
    const goal: PlatformGoal = {
      ...BASE_GOAL,
      status: "BLOCKED",
      task_links: [
        { task_id: "blocked", plan_task_id: "T001", status: "BLOCKED", title: "处理阻塞" },
      ],
    };
    const blockedRun = run("blocked", {
      status: "BLOCKED",
      state: "BLOCKED_EXTERNAL",
      liveness: "BLOCKED",
      current_activity: {
        category: "BLOCKED",
        title: "上游执行器不可用",
        description: "当前任务无法继续。",
        timestamp: new Date().toISOString(),
      },
      activity: [event("blocked-event", "blocked", "BLOCKED", "执行被阻塞", 9)],
    });

    renderWithProviders(<GoalCurrentActivity goal={goal} runs={[blockedRun]} />);

    expect(screen.getByTestId("goal-activity-liveness")).toHaveTextContent("已阻塞");
    const current = screen.getByTestId("goal-current-activity-now");
    expect(current).toHaveTextContent("上游执行器不可用");
    expect(current.querySelector("span")).toHaveClass("text-ra-status-error");
    expect(screen.getByTestId("goal-activity-event-blocked-event")).toHaveTextContent("阻塞");
  });

  it("converges a completed Goal to one terminal success treatment", async () => {
    __setMockGoalStatus(GOAL_ID, {
      status: "COMPLETED",
      task_links: ORIGINAL_LINKS.map((link) => ({ ...link, status: "READY_FOR_REVIEW" })),
    });

    renderWithProviders(<HomePage />);

    const state = await screen.findByTestId("goal-state-label");
    expect(state).toHaveTextContent("已完成");
    expect(state).toHaveClass("text-ra-status-running");
    expect(state).not.toHaveTextContent("正在执行");

    await waitFor(() => {
      expect(screen.getByTestId("goal-progress-summary")).toHaveTextContent("3/3");
    });
    expect(screen.getByTestId("goal-progress-bar").firstElementChild).toHaveClass(
      "bg-ra-status-running",
    );
  });

  it("converges a blocked Goal to one error treatment without a running status", async () => {
    __setMockGoalStatus(GOAL_ID, {
      status: "BLOCKED",
      task_links: [
        { ...ORIGINAL_LINKS[0], status: "READY_FOR_REVIEW" },
        { ...ORIGINAL_LINKS[1], status: "BLOCKED" },
        { ...ORIGINAL_LINKS[2], status: "QUEUED" },
      ],
    });

    renderWithProviders(<HomePage />);

    const state = await screen.findByTestId("goal-state-label");
    expect(state).toHaveTextContent("需要处理阻塞");
    expect(state).toHaveClass("text-ra-status-error");
    expect(state).not.toHaveClass("text-ra-accent");
    expect(screen.getByTestId("goal-progress-bar").firstElementChild).toHaveClass(
      "bg-ra-status-error",
    );
  });

  it("keeps large change totals as bounded metadata and does not render raw changed-file rows", () => {
    const goal: PlatformGoal = {
      ...BASE_GOAL,
      task_links: [
        { task_id: "large-a", plan_task_id: "T001", status: "RUNNING", title: "大规模修改 A" },
        { task_id: "large-b", plan_task_id: "T002", status: "RUNNING", title: "大规模修改 B" },
      ],
    };
    const runs = [
      run("large-a", {
        change_summary: { file_count: 85, additions: 4000, deletions: 3500 },
        changed_files: [
          { path: "SHOULD-NOT-RENDER-a.ts", status: "modified", additions: 4000, deletions: 3500 },
        ],
      }),
      run("large-b", {
        change_summary: { file_count: 64, additions: 2000, deletions: 1000 },
        changed_files: [
          { path: "SHOULD-NOT-RENDER-b.ts", status: "modified", additions: 2000, deletions: 1000 },
        ],
      }),
    ];

    renderWithProviders(<GoalCurrentActivity goal={goal} runs={runs} />);

    expect(screen.getByTestId("goal-activity-change-summary")).toHaveTextContent(
      "149 个文件变更 · +6000 -4500",
    );
    expect(screen.queryByText("SHOULD-NOT-RENDER-a.ts")).not.toBeInTheDocument();
    expect(screen.queryByText("SHOULD-NOT-RENDER-b.ts")).not.toBeInTheDocument();
  });

  it("bounds a long semantic history to the compact event limit", () => {
    const goal: PlatformGoal = {
      ...BASE_GOAL,
      task_links: [
        { task_id: "long-run", plan_task_id: "T001", status: "RUNNING", title: "长时任务" },
      ],
    };
    const longRun = run("long-run", {
      activity: Array.from({ length: 30 }, (_, index) =>
        event(
          `long-${index}`,
          "long-run",
          index % 3 === 0 ? "READ" : index % 3 === 1 ? "EDIT" : "VERIFY",
          `语义事件 ${index}`,
          index,
        ),
      ),
    });

    renderWithProviders(<GoalCurrentActivity goal={goal} runs={[longRun]} />);

    const rows = screen.getByTestId("goal-activity-events").querySelectorAll("li");
    expect(rows).toHaveLength(5);
    expect(screen.getByText("语义事件 29")).toBeInTheDocument();
    expect(screen.queryByText("语义事件 0")).not.toBeInTheDocument();
  });

  it("keeps GoalProgress error/success color contracts tied to authoritative Goal status", () => {
    const completed: PlatformGoal = {
      ...BASE_GOAL,
      status: "COMPLETED",
      task_links: [
        { task_id: "done", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "已验证" },
      ],
    };
    const { rerender } = renderWithProviders(<GoalProgress goal={completed} />);

    expect(screen.getByTestId("goal-progress-bar").firstElementChild).toHaveClass(
      "bg-ra-status-running",
    );

    const blocked: PlatformGoal = {
      ...completed,
      status: "BLOCKED",
      task_links: [
        { task_id: "blocked-progress", plan_task_id: "T001", status: "BLOCKED", title: "阻塞" },
      ],
    };
    rerender(<GoalProgress goal={blocked} />);

    expect(screen.getByTestId("goal-progress-bar").firstElementChild).toHaveClass(
      "bg-ra-status-error",
    );
    expect(screen.getByText("需要处理阻塞")).toHaveClass("text-ra-status-error");
  });
});
