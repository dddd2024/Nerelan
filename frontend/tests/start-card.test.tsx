import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import * as client from "@/lib/platform-client";
import { PlatformClientError, type OwnerWindowCard, type PlatformGoal } from "@/lib/platform-client";
import { StartCard } from "@/components/start-card";

const GOAL = { id: "goal-x", revision: 2, status: "PLANNED", tasks: [{ id: "T001", title: "t", dependencies: [] }] } as unknown as PlatformGoal;

const CARD: OwnerWindowCard = {
  preset: "day", confirmation: "ui",
  presets: { trial: { label: "试跑", hours: 2, max_concurrent: 1, max_retries: 1, max_token_units: 300_000 },
             day: { label: "一天", hours: 24, max_concurrent: 1, max_retries: 2, max_token_units: 2_000_000 } },
  request: { goal_ids: ["goal-x"], hours: 24, max_tasks: 3, max_concurrent: 1, max_retries: 2,
             capabilities: ["execute_task"], max_token_units: 2_000_000, max_cost_micro_units: 0 },
};

const SCOPE = {
  repository: "dddd2024/Nerelan", base_sha: "b".repeat(40),
  goals: [{ id: "goal-x", revision: 2, objective: "o", mode: "agent_team", tasks: [{ id: "T001", title: "t" }] }],
  pool: [{ binding: "token-sensenova-glm", executor: "opencode", model: "glm-5.2", cost: "free", weekly_paced: false },
         { binding: "codex-gpt", executor: "codex", model: "gpt-6.1", cost: "subscription", weekly_paced: true }],
  pool_skipped: ["copilot-x (ValueError)"], envelope: {}, paid_api: "excluded",
};

const PASS = { ok: true, checks: [{ check: "goals", ok: true, reason: "", detail: "" }],
  preview: ["- goal-x T001: free (token-sensenova/glm-5.2, fixture_route)"], scope: SCOPE, card_digest: "a".repeat(64), confirmation: "ui" };

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("start card", () => {
  it("shows the bounds and each step's model, and starts with the card digest", async () => {
    vi.spyOn(client, "fetchOwnerWindowCard").mockResolvedValue(CARD);
    vi.spyOn(client, "preflightOwnerWindow").mockResolvedValue(PASS);
    const activate = vi.spyOn(client, "activateOwnerWindow").mockResolvedValue({} as never);
    renderWithProviders(<StartCard goal={GOAL} />);
    expect(await screen.findByTestId("start-bounds")).toHaveTextContent("时长 24 小时 · 最多 3 个任务 · 每步最多重试 2 次 · 同时 1 个 · Token 上限 2M");
    await waitFor(() => expect(screen.getByTestId("start-button")).toBeEnabled());
    expect(screen.getByTestId("start-preview")).toHaveTextContent("T001 → token-sensenova/glm-5.2（免费）");
    await userEvent.click(screen.getByTestId("start-button"));
    await waitFor(() => expect(activate).toHaveBeenCalledWith(CARD.request, "a".repeat(64)));
  });

  it("names a failed check in plain words and keeps Start disabled", async () => {
    vi.spyOn(client, "fetchOwnerWindowCard").mockResolvedValue(CARD);
    vi.spyOn(client, "preflightOwnerWindow").mockResolvedValue({ ...PASS, ok: false, checks: [
      { check: "leftover_claims", ok: false, reason: "owner_window_old_active_claims_hold", detail: "1 active" }] });
    renderWithProviders(<StartCard goal={GOAL} />);
    expect(await screen.findByTestId("start-check-leftover_claims")).toHaveTextContent("上一个窗口还留着执行占用");
    expect(screen.getByTestId("start-button")).toBeDisabled();
  });

  it("asks again when the scope changed after the Owner looked", async () => {
    vi.spyOn(client, "fetchOwnerWindowCard").mockResolvedValue(CARD);
    const preflight = vi.spyOn(client, "preflightOwnerWindow").mockResolvedValue(PASS);
    vi.spyOn(client, "activateOwnerWindow").mockRejectedValue(new PlatformClientError(409, "owner_window_scope_changed"));
    renderWithProviders(<StartCard goal={GOAL} />);
    await waitFor(() => expect(screen.getByTestId("start-button")).toBeEnabled());
    await userEvent.click(screen.getByTestId("start-button"));
    expect(await screen.findByRole("status")).toHaveTextContent("范围变了");
    await waitFor(() => expect(preflight.mock.calls.length).toBeGreaterThan(1));
  });

  it("shows the terminal command in the Owner's strict mode", async () => {
    vi.spyOn(client, "fetchOwnerWindowCard").mockResolvedValue({ ...CARD, confirmation: "terminal" });
    vi.spyOn(client, "preflightOwnerWindow").mockResolvedValue({ ...PASS, confirmation: "terminal" });
    renderWithProviders(<StartCard goal={GOAL} />);
    expect(await screen.findByTestId("start-terminal")).toHaveTextContent(
      "python -m reverse_agent.platform_v1.owner_window --goal goal-x --hours 24 --max-tasks 3");
    expect(screen.queryByTestId("start-button")).not.toBeInTheDocument();
  });

  it("shows every model Start authorizes and the ones left out", async () => {
    vi.spyOn(client, "fetchOwnerWindowCard").mockResolvedValue(CARD);
    vi.spyOn(client, "preflightOwnerWindow").mockResolvedValue(PASS);
    renderWithProviders(<StartCard goal={GOAL} />);
    const pool = await screen.findByTestId("start-pool");
    expect(pool).toHaveTextContent("本窗口可以用这些模型（2 个）");
    expect(pool).toHaveTextContent("glm-5.2 · opencode（免费）");
    expect(pool).toHaveTextContent("gpt-6.1 · codex（订阅额度，按周配额节奏）");
    expect(screen.getByTestId("start-pool-skipped")).toHaveTextContent("不会使用：copilot-x (ValueError)");
  });

  it("keeps Start disabled while the checked plan is newer than the plan on screen", async () => {
    vi.spyOn(client, "fetchOwnerWindowCard").mockResolvedValue(CARD);
    vi.spyOn(client, "preflightOwnerWindow").mockResolvedValue({
      ...PASS, scope: { ...SCOPE, goals: [{ ...SCOPE.goals[0], revision: 3 }] } });
    const activate = vi.spyOn(client, "activateOwnerWindow").mockResolvedValue({} as never);
    renderWithProviders(<StartCard goal={GOAL} />);
    expect(await screen.findByTestId("start-stale")).toHaveTextContent("计划刚被修改过");
    expect(screen.getByTestId("start-button")).toBeDisabled();
    expect(activate).not.toHaveBeenCalled();
  });

  it("refetches with the chosen preset", async () => {
    const fetchCard = vi.spyOn(client, "fetchOwnerWindowCard").mockResolvedValue(CARD);
    vi.spyOn(client, "preflightOwnerWindow").mockResolvedValue(PASS);
    renderWithProviders(<StartCard goal={GOAL} />);
    await userEvent.click(await screen.findByTestId("start-preset-trial"));
    await waitFor(() => expect(fetchCard).toHaveBeenLastCalledWith(["goal-x"], "trial"));
  });
});
