import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import {
  launchExistingGoal,
  planExistingGoal,
} from "@/lib/goal-continuation-operation";
import {
  __setMockGoalStatus,
  captureInboxItem,
  promoteInboxItem,
  type PlatformGoal,
} from "@/lib/platform-client";
import { ApprovalsPage } from "@/routes/approvals";

const DEMO_GOAL_ID = "goal-demo-platform";

function goalFixture(status: PlatformGoal["status"] = "DRAFT"): PlatformGoal {
  return {
    id: "goal-conflict-test",
    title: "Conflict test",
    objective: "Verify fail-closed continuation behavior.",
    repository: "dddd2024/Nerelan",
    status,
    revision: 7,
    spec_markdown: "# Spec",
    plan_markdown: "# Plan\n\nExact current plan.",
    tasks: [],
    acceptance_criteria: ["Use exact revision"],
    artifact_digest: "fixture",
    executor_kind: "deterministic_fixture",
    orchestration_mode: "single",
    binding_ref: "",
    window_id: "",
    created_at: "2026-09-11T00:00:00Z",
    updated_at: "2026-09-11T00:00:00Z",
  };
}

describe("Approvals continuation page", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
    __setMockGoalStatus(DEMO_GOAL_ID, {
      status: "DRAFT",
      revision: 2,
      plan_markdown: "",
      acceptance_criteria: ["任务可恢复", "结果可审查"],
      executor_kind: "opencode",
      binding_ref: "coding-default",
      window_id: "",
    });
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("deep-links the same Goal through explicit Plan, Approve, and Launch", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ApprovalsPage />, {
      initialEntries: [`/approvals?goal=${DEMO_GOAL_ID}`],
    });

    await waitFor(() =>
      expect(screen.getByText("完善无人值守多 Agent 平台")).toBeInTheDocument(),
    );
    expect(screen.getAllByText("草稿").length).toBeGreaterThan(0);
    expect(screen.getByTestId("approval-plan-button")).toBeInTheDocument();

    await user.click(screen.getByTestId("approval-plan-button"));
    await waitFor(() =>
      expect(screen.getByTestId("approval-approve-button")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("approval-plan")).toHaveTextContent(
      "Review the generated plan before approval.",
    );

    await user.click(screen.getByTestId("approval-approve-button"));
    await waitFor(() =>
      expect(screen.getByTestId("approval-launch-button")).toBeInTheDocument(),
    );

    await user.selectOptions(screen.getByLabelText("自治窗口时长"), "4");
    await user.click(screen.getByTestId("approval-launch-button"));
    await waitFor(() => expect(screen.getByText("运行中")).toBeInTheDocument());

    expect(screen.queryByTestId("approval-plan-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-approve-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-launch-button")).not.toBeInTheDocument();
  });

  it("shows the exact current plan and multiple pending Goals before approval", async () => {
    __setMockGoalStatus(DEMO_GOAL_ID, {
      status: "PLANNED",
      plan_markdown: "# Plan\n\nExact plan visible before approval.",
      acceptance_criteria: ["Exact criterion"],
    });
    const captured = await captureInboxItem({
      objective: "Second pending approval",
      repository: "dddd2024/Nerelan",
    });
    await promoteInboxItem(captured.id);

    renderWithProviders(<ApprovalsPage />, {
      initialEntries: [`/approvals?goal=${DEMO_GOAL_ID}`],
    });

    await waitFor(() =>
      expect(screen.getByText("Exact criterion")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("approval-plan")).toHaveTextContent(
      "Exact plan visible before approval.",
    );
    expect(
      screen.getByTestId("approval-pending-list").querySelectorAll("button").length,
    ).toBeGreaterThanOrEqual(2);
  });

  it("keeps terminal Goals read-only even when opened by deep link", async () => {
    __setMockGoalStatus(DEMO_GOAL_ID, { status: "COMPLETED" });
    renderWithProviders(<ApprovalsPage />, {
      initialEntries: [`/approvals?goal=${DEMO_GOAL_ID}`],
    });

    await waitFor(() => expect(screen.getByText("已完成")).toBeInTheDocument());
    expect(screen.getByText(/当前状态只读/)).toBeInTheDocument();
    expect(screen.queryByTestId("approval-plan-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-approve-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-launch-button")).not.toBeInTheDocument();
  });

  it("maps a revision conflict to a visible fail-closed continuation error", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ error: "goal_revision_conflict" }), {
        status: 409,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(planExistingGoal(goalFixture())).rejects.toMatchObject({
      code: "goal_revision_conflict",
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("refuses to replace an active window owned by another repository", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          autonomy: {
            active_window: {
              id: "window-other",
              repositories: ["other/repository"],
            },
          },
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await expect(
      launchExistingGoal(goalFixture("APPROVED"), 2),
    ).rejects.toMatchObject({
      code: "active_window_repository_conflict",
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
