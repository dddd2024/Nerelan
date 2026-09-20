import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { launchExistingGoal } from "@/lib/goal-continuation-operation";
import { PlatformClientError, type PlatformGoal } from "@/lib/platform-client";

const goal: PlatformGoal = {
  id: "goal-activation-error",
  title: "Activation error",
  objective: "Preserve actionable activation errors.",
  repository: "dddd2024/Nerelan",
  status: "APPROVED",
  revision: 7,
  spec_markdown: "# Spec",
  plan_markdown: "# Plan",
  tasks: [],
  acceptance_criteria: ["Use the approved revision"],
  artifact_digest: "fixture",
  executor_kind: "deterministic_fixture",
  orchestration_mode: "single",
  binding_ref: "",
  window_id: "",
  created_at: "2026-09-20T00:00:00Z",
  updated_at: "2026-09-20T00:00:00Z",
};

function response(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("activation error reconciliation", () => {
  beforeEach(() => vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1"));
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it.each([
    [409, "invalid_autonomy_policy_identity"],
    [409, "repository_workspace_unconfigured"],
    [400, "active_window_not_available"],
  ])("preserves activation %s %s when refresh finds no window", async (status, code) => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response({ autonomy: { active_window: null } }))
      .mockResolvedValueOnce(response({ error: code }, status))
      .mockResolvedValueOnce(response({ autonomy: { active_window: null } }));

    const result = launchExistingGoal(goal, 2);
    await expect(result).rejects.toBeInstanceOf(PlatformClientError);
    await expect(result).rejects.toMatchObject({ status, code });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    const paths = fetchMock.mock.calls.map(([input]) => String(input));
    expect(paths[2]).toBe(paths[0]);
    expect(paths[1]).toMatch(/\/api\/windows\/activate$/);
    expect(paths.some((path) => path.endsWith(`/api/goals/${goal.id}/launch`))).toBe(false);
  });

  it("uses a refreshed same-repository window without another activation", async () => {
    const active = { id: "window-concurrent", repositories: [goal.repository] };
    const running = { ...goal, status: "RUNNING", window_id: active.id };
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response({ autonomy: { active_window: null } }))
      .mockResolvedValueOnce(response({ error: "active_window_exists" }, 409))
      .mockResolvedValueOnce(response({ autonomy: { active_window: active } }))
      .mockResolvedValueOnce(response(running))
      .mockResolvedValueOnce(response(running));

    await expect(launchExistingGoal(goal, 2)).resolves.toMatchObject({ window_id: active.id });
    expect(fetchMock).toHaveBeenCalledTimes(5);
    expect(fetchMock.mock.calls[2][0]).toBe(fetchMock.mock.calls[0][0]);
    expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith("/api/windows/activate"))).toHaveLength(1);
    const launch = fetchMock.mock.calls.find(([input]) => String(input).endsWith(`/api/goals/${goal.id}/launch`));
    expect(JSON.parse(String(launch?.[1]?.body))).toEqual({ expected_revision: goal.revision, window_id: active.id });
  });

  it("rejects a refreshed other-repository window before launch", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response({ autonomy: { active_window: null } }))
      .mockResolvedValueOnce(response({ error: "active_window_exists" }, 409))
      .mockResolvedValueOnce(response({ autonomy: { active_window: { id: "other", repositories: ["other/repository"] } } }));

    await expect(launchExistingGoal(goal, 2)).rejects.toMatchObject({ code: "active_window_repository_conflict" });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[2][0]).toBe(fetchMock.mock.calls[0][0]);
  });
});
