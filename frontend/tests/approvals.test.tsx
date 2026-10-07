import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import * as platformClient from "@/lib/platform-client";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import {
  launchExistingGoal,
  planExistingGoal,
  saveGoalConfiguration,
} from "@/lib/goal-continuation-operation";
import {
  __setMockGoalStatus,
  captureInboxItem,
  promoteInboxItem,
  type PlatformGoal,
} from "@/lib/platform-client";
import { ApprovalsPage } from "@/routes/approvals";
import { profileToPolicy } from "@/lib/profile-mapper";

function approvedTemplate() {
  const policy = profileToPolicy("ASK_FOR_APPROVAL");
  policy.repository = "dddd2024/Nerelan";
  policy.autonomousWindow.expiresAt = "2030-12-31T08:00:00Z";
  return { available: true, policy_id: "approved-continuation-fixture", policy_revision: 1,
    policy_digest: "a".repeat(64), window_id: "window-same", policy,
    confirmation_provenance: { confirmation_mode: "DELEGATED_CONTROLLER", personally_human: false },
    supported_operations: ["execute_task"], validation_command_id: "git_diff_check" };
}

function approvedWindow() {
  const template = approvedTemplate();
  return { id: template.window_id, policy_id: template.policy_id, policy_revision: template.policy_revision,
    canonical_policy_digest: template.policy_digest, status: "ACTIVE", expires_at: template.policy.autonomousWindow.expiresAt,
    repositories: [template.policy.repository], tasks_started: 1, tasks_completed: 0 };
}

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

function jsonResponse(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
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
      executor_kind: "deterministic_fixture",
      orchestration_mode: "single",
      binding_ref: "",
      tasks: [],
      task_links: [],
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
      expect(
        screen.getAllByText("完善无人值守多 Agent 平台").length,
      ).toBeGreaterThan(0),
    );
    expect(screen.getAllByText("草稿").length).toBeGreaterThan(0);
    expect(screen.getByTestId("approval-plan-button")).toBeInTheDocument();

    await user.click(screen.getByTestId("approval-plan-button"));
    await waitFor(() =>
      expect(screen.getByTestId("approval-approve-button")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("approval-plan")).toHaveTextContent(
      "实现并验证目标",
    );

    await user.click(screen.getByTestId("approval-approve-button"));
    await waitFor(() =>
      expect(screen.getByTestId("approval-launch-button")).toBeInTheDocument(),
    );

    await user.selectOptions(screen.getByLabelText("自治窗口时长"), "4");
    expect(screen.getByTestId("approval-launch-button")).toBeDisabled();
    await user.click(screen.getByLabelText("确认启动当前计划"));
    await user.click(screen.getByTestId("approval-launch-button"));
    await waitFor(() => expect(screen.getByText("运行中")).toBeInTheDocument());

    expect(screen.queryByTestId("approval-plan-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-approve-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-launch-button")).not.toBeInTheDocument();
  });

  it("collapses to a single actionable empty state when the queue is empty and nothing is selected", async () => {
    __setMockGoalStatus(DEMO_GOAL_ID, { status: "RUNNING" });
    renderWithProviders(<ApprovalsPage />);

    expect(await screen.findByTestId("approval-empty")).toBeInTheDocument();
    expect(screen.getByText("当前没有待处理的目标")).toBeInTheDocument();
    /*
     * A queue rail reading "0 项" next to a pane instructing the operator to
     * "select a Goal" is a contradictory state (`#448` §9) — the collapsed
     * state must not keep either half of that pair on screen.
     */
    expect(screen.queryByTestId("approval-pending-list")).not.toBeInTheDocument();
    expect(screen.queryByText(/从左侧选择一个目标/)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "查看所有目标" })).toHaveAttribute("href", "/goals");
    expect(screen.getByRole("link", { name: "打开想法收件箱" })).toHaveAttribute("href", "/inbox");
  });

  it("keeps a deep-linked Goal visible after it leaves the pending queue", async () => {
    __setMockGoalStatus(DEMO_GOAL_ID, { status: "RUNNING" });
    renderWithProviders(<ApprovalsPage />, {
      initialEntries: [`/approvals?goal=${DEMO_GOAL_ID}`],
    });

    /*
     * Live server truth outranks the empty-queue presentation: the Goal moved
     * on from the queue, so the operator must still be able to see where it
     * went instead of losing it behind an empty state.
     */
    expect(await screen.findByTestId("approval-goal-detail")).toBeInTheDocument();
    expect(screen.getAllByText("运行中").length).toBeGreaterThan(0);
    expect(screen.queryByTestId("approval-empty")).not.toBeInTheDocument();
    expect(screen.getByText(/该目标当前不在待处理队列中/)).toBeInTheDocument();
    expect(screen.getByText(/当前状态只读/)).toBeInTheDocument();
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

  it("keeps terminal Goals read-only and labels completion as awaiting review", async () => {
    __setMockGoalStatus(DEMO_GOAL_ID, { status: "COMPLETED" });
    renderWithProviders(<ApprovalsPage />, {
      initialEntries: [`/approvals?goal=${DEMO_GOAL_ID}`],
    });

    await waitFor(() => expect(screen.getByText("执行完成，待审查")).toBeInTheDocument());
    expect(screen.queryByText("已完成")).not.toBeInTheDocument();
    expect(screen.getByText(/当前状态只读/)).toBeInTheDocument();
    expect(screen.queryByTestId("approval-plan-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-approve-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-launch-button")).not.toBeInTheDocument();
  });

  it("preserves unsaved configuration when the background Goal list refresh fails", async () => {
    const fetchGoals = platformClient.fetchGoals;
    let failRefresh = false;
    vi.spyOn(platformClient, "fetchGoals").mockImplementation(() => failRefresh
      ? Promise.reject(new Error("Goal list temporarily unavailable")) : fetchGoals());
    const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
    render(<QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/approvals?goal=${DEMO_GOAL_ID}`]}><ApprovalsPage /></MemoryRouter>
    </QueryClientProvider>);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "编辑目标配置" }));
    await user.clear(screen.getByLabelText("目标规格"));
    await user.type(screen.getByLabelText("目标规格"), "My unsaved specification");
    failRefresh = true;
    await act(async () => { await client.invalidateQueries({ queryKey: ["goals"], exact: true }); });
    expect(await screen.findByRole("alert")).toHaveTextContent("Goal list temporarily unavailable");
    expect(screen.getByLabelText("目标规格")).toHaveValue("My unsaved specification");
    expect(screen.getByTestId("approval-plan-button")).toBeDisabled();
    expect((await platformClient.fetchGoal(DEMO_GOAL_ID)).objective).not.toBe("My unsaved specification");
  });

  it("maps an explicit Goal revision/state mismatch to the fail-closed continuation error", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(approvedTemplate()))
      .mockResolvedValueOnce(jsonResponse({ error: "goal_revision_or_state_mismatch" }, 409));

    await expect(planExistingGoal(goalFixture())).rejects.toMatchObject({
      code: "goal_revision_conflict",
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(String(fetchMock.mock.calls[1][0])).toMatch(/\/api\/goals\/goal-conflict-test\/plan$/);
  });

  it("maps an explicit Goal configuration state conflict to the fail-closed continuation error", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ error: "goal_configuration_not_editable" }, 409),
    );
    const goal = goalFixture("APPROVED");

    await expect(saveGoalConfiguration(goal, {
      objective: goal.objective,
      repository: goal.repository,
      executor_kind: goal.executor_kind,
      orchestration_mode: goal.orchestration_mode,
      binding_ref: goal.binding_ref,
    })).rejects.toMatchObject({
      code: "goal_revision_conflict",
    });
  });

  it("preserves an actionable operational 409 instead of fabricating a revision conflict", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ error: "repository_workspace_unconfigured" }, 409),
    );

    let observed: unknown;
    try {
      await planExistingGoal(goalFixture());
    } catch (error) {
      observed = error;
    }

    expect(observed).toBeInstanceOf(platformClient.PlatformClientError);
    expect(observed).toMatchObject({
      status: 409,
      code: "repository_workspace_unconfigured",
    });
  });

  it("reuses an active window for the same repository without activating another one", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const goal = goalFixture("APPROVED");
    const running = { ...goal, status: "RUNNING" as const, window_id: "window-same" };
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(approvedTemplate()))
      .mockResolvedValueOnce(jsonResponse({
        autonomy: {
          active_window: approvedWindow(),
        },
      }))
      .mockResolvedValueOnce(jsonResponse(running))
      .mockResolvedValueOnce(jsonResponse(running));

    const result = await launchExistingGoal(goal, 2);

    expect(result).toMatchObject({ id: goal.id, revision: goal.revision, window_id: "window-same" });
    expect(
      fetchMock.mock.calls.some(([input]) => String(input).endsWith("/api/windows/activate")),
    ).toBe(false);
    const launchCall = fetchMock.mock.calls.find(([input]) =>
      String(input).endsWith(`/api/goals/${goal.id}/launch`),
    );
    expect(JSON.parse(String(launchCall?.[1]?.body))).toEqual({
      expected_revision: goal.revision,
      window_id: "window-same",
    });
  });

  it("replays the same approved revision without resetting spending or granting a fresh expiry", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const goal = goalFixture("APPROVED");
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(approvedTemplate()))
      .mockResolvedValueOnce(jsonResponse({ autonomy: { active_window: null } }))
      .mockResolvedValueOnce(jsonResponse(approvedWindow(), 201))
      .mockResolvedValueOnce(jsonResponse({ error: "repository_workspace_unconfigured" }, 409))
      .mockResolvedValueOnce(jsonResponse(approvedTemplate()))
      .mockResolvedValueOnce(jsonResponse({ autonomy: { active_window: null } }))
      .mockResolvedValueOnce(jsonResponse(approvedWindow(), 201))
      .mockResolvedValueOnce(jsonResponse({ error: "repository_workspace_unconfigured" }, 409));

    for (let attempt = 0; attempt < 2; attempt += 1) {
      let observed: unknown;
      try {
        await launchExistingGoal(goal, 2);
      } catch (error) {
        observed = error;
      }
      expect(observed).toBeInstanceOf(platformClient.PlatformClientError);
      expect(observed).toMatchObject({
        status: 409,
        code: "repository_workspace_unconfigured",
      });
    }

    const activationCalls = fetchMock.mock.calls.filter(([input]) =>
      String(input).endsWith("/api/windows/activate"),
    );
    expect(activationCalls).toHaveLength(2);
    const firstPolicy = JSON.parse(String(activationCalls[0][1]?.body));
    const secondPolicy = JSON.parse(String(activationCalls[1][1]?.body));

    expect(firstPolicy).toEqual(secondPolicy);
    expect(firstPolicy).toEqual({ policy_id: approvedTemplate().policy_id, policy_revision: 1, policy: approvedTemplate().policy });
    expect(firstPolicy.policy.autonomousWindow.expiresAt).toBe("2030-12-31T08:00:00Z");
    expect(firstPolicy).not.toHaveProperty("starts_at");
    expect(firstPolicy).not.toHaveProperty("expires_at");
    expect(firstPolicy).not.toHaveProperty("confirmation");
    expect(firstPolicy).not.toHaveProperty("tasks_started");

    const launchCalls = fetchMock.mock.calls.filter(([input]) =>
      String(input).endsWith(`/api/goals/${goal.id}/launch`),
    );
    expect(launchCalls).toHaveLength(2);
    expect(JSON.parse(String(launchCalls[0][1]?.body))).toEqual({
      expected_revision: goal.revision,
      window_id: approvedTemplate().window_id,
    });
    expect(JSON.parse(String(launchCalls[1][1]?.body))).toEqual({
      expected_revision: goal.revision,
      window_id: approvedTemplate().window_id,
    });
  });

  it("refuses to replace an active window owned by another repository", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResponse(approvedTemplate())).mockResolvedValueOnce(
      jsonResponse({
        autonomy: {
          active_window: {
            id: "window-other",
            repositories: ["other/repository"],
          },
        },
      }),
    );

    await expect(
      launchExistingGoal(goalFixture("APPROVED"), 2),
    ).rejects.toMatchObject({
      code: "active_window_repository_conflict",
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
