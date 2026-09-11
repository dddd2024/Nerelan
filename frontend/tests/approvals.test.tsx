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
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ error: "goal_revision_or_state_mismatch" }, 409),
    );

    await expect(planExistingGoal(goalFixture())).rejects.toMatchObject({
      code: "goal_revision_conflict",
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
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
      .mockResolvedValueOnce(jsonResponse({
        autonomy: {
          active_window: {
            id: "window-same",
            repositories: [goal.repository],
          },
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

  it("uses fresh time-bound policy identities when the same approved Goal activates again", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const goal = goalFixture("APPROVED");
    const firstStart = Date.parse("2026-09-11T12:00:00.000Z");
    const secondStart = Date.parse("2026-09-11T12:00:01.000Z");
    vi.spyOn(Date, "now")
      .mockReturnValueOnce(firstStart)
      .mockReturnValueOnce(secondStart);

    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ autonomy: { active_window: null } }))
      .mockResolvedValueOnce(jsonResponse({ id: "window-first", repositories: [goal.repository] }, 201))
      .mockResolvedValueOnce(jsonResponse({ error: "repository_workspace_unconfigured" }, 409))
      .mockResolvedValueOnce(jsonResponse({ autonomy: { active_window: null } }))
      .mockResolvedValueOnce(jsonResponse({ id: "window-second", repositories: [goal.repository] }, 201))
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

    expect(firstPolicy.policy_id).not.toBe(secondPolicy.policy_id);
    expect(firstPolicy.policy_id).toContain(String(firstStart));
    expect(secondPolicy.policy_id).toContain(String(secondStart));
    expect(firstPolicy.starts_at).toBe(new Date(firstStart).toISOString());
    expect(secondPolicy.starts_at).toBe(new Date(secondStart).toISOString());
    expect(firstPolicy.expires_at).toBe(new Date(firstStart + 2 * 60 * 60 * 1000).toISOString());
    expect(secondPolicy.expires_at).toBe(new Date(secondStart + 2 * 60 * 60 * 1000).toISOString());

    const launchCalls = fetchMock.mock.calls.filter(([input]) =>
      String(input).endsWith(`/api/goals/${goal.id}/launch`),
    );
    expect(launchCalls).toHaveLength(2);
    expect(JSON.parse(String(launchCalls[0][1]?.body))).toEqual({
      expected_revision: goal.revision,
      window_id: "window-first",
    });
    expect(JSON.parse(String(launchCalls[1][1]?.body))).toEqual({
      expected_revision: goal.revision,
      window_id: "window-second",
    });
  });

  it("refuses to replace an active window owned by another repository", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
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
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
