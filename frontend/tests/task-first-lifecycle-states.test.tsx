import { afterEach, describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { GoalProgress } from "@/components/goal-progress";
import { HomePage } from "@/routes/home";
import {
  __setMockGoalStatus,
  type PlatformGoal,
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

afterEach(() => {
  __setMockGoalStatus(GOAL_ID, {
    status: "RUNNING",
    task_links: ORIGINAL_LINKS,
  });
});

describe("task-first lifecycle-state convergence before R3 visual acceptance", () => {
  // Activity-stream cases moved to goal-timeline.test.tsx with the unified goal timeline.
  it("converges a completed Goal to execution-complete review-pending treatment", async () => {
    __setMockGoalStatus(GOAL_ID, {
      status: "COMPLETED",
      task_links: ORIGINAL_LINKS.map((link) => ({ ...link, status: "READY_FOR_REVIEW" })),
    });

    renderWithProviders(<HomePage />, { initialEntries: [`/?goal=${GOAL_ID}`] });

    const state = await screen.findByTestId("goal-state-label");
    expect(state).toHaveTextContent("待审查");
    expect(state).toHaveClass("text-ra-status-running");
    expect(state).not.toHaveTextContent("进行中");

    // Every step's turn reads done; nothing claims verification.
    await waitFor(() => {
      const headers = screen.getAllByTestId("thread-attempt-header");
      expect(headers).toHaveLength(3);
      for (const header of headers) expect(header.lastElementChild).toHaveTextContent(/^完成$/);
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByText("结果已验证")).not.toBeInTheDocument();
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

    renderWithProviders(<HomePage />, { initialEntries: [`/?goal=${GOAL_ID}`] });

    const state = await screen.findByTestId("goal-state-label");
    expect(state).toHaveTextContent("已停下");
    expect(state).not.toHaveTextContent("进行中");
    expect(state).toHaveClass("text-ra-status-error");
    expect(state).not.toHaveClass("text-ra-accent");
    // One error treatment: the stopped attempt's alert, and no turn still running.
    await waitFor(() => expect(screen.getAllByTestId("thread-attempt-header")).toHaveLength(3));
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(screen.getByTestId("thread-stop")).toHaveAttribute("role", "alert");
    const states = screen.getAllByTestId("thread-attempt-header").map((header) => header.lastElementChild?.textContent);
    expect(states).not.toContain("进行中");
    expect(states).toContain("停下");
  });

  it("keeps GoalProgress color contracts while distinguishing real and fixture review-ready states", () => {
    const completed: PlatformGoal = {
      ...BASE_GOAL,
      status: "COMPLETED",
      task_links: [
        { task_id: "done", plan_task_id: "T001", status: "READY_FOR_REVIEW", title: "待审查结果" },
      ],
    };
    const { rerender } = renderWithProviders(<GoalProgress goal={completed} />);

    expect(screen.getByTestId("goal-progress-bar").firstElementChild).toHaveClass(
      "bg-ra-status-running",
    );
    expect(screen.getByText("执行完成，待审查")).toBeInTheDocument();
    expect(screen.queryByText("结果已验证")).not.toBeInTheDocument();

    const fixture: PlatformGoal = {
      ...completed,
      task_links: [
        { task_id: "fixture", plan_task_id: "T001", status: "READY_FOR_REVIEW_FIXTURE", title: "Fixture 结果" },
      ],
    };
    rerender(<GoalProgress goal={fixture} />);
    expect(screen.getByText("Fixture 完成，待审查")).toBeInTheDocument();
    expect(screen.queryByText("结果已验证")).not.toBeInTheDocument();

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
