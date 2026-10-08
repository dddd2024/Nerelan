import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { launchExistingGoal } from "@/lib/goal-continuation-operation";
import { PlatformClientError, type PlatformGoal } from "@/lib/platform-client";
import { profileToPolicy } from "@/lib/profile-mapper";

function template() {
  const policy = profileToPolicy("ASK_FOR_APPROVAL");
  policy.repository = goal.repository;
  policy.autonomousWindow.expiresAt = "2030-12-31T08:00:00Z";
  return { available: true, policy_id: "approved-fixture", policy_revision: 1, policy_digest: "a".repeat(64),
    window_id: "window-concurrent", policy, confirmation_provenance: { confirmation_mode: "DELEGATED_CONTROLLER", personally_human: false },
    supported_operations: ["validate_task"], validation_command_id: "git_diff_check" };
}

function approvedWindow() {
  const approved = template();
  return { id: approved.window_id, policy_id: approved.policy_id, policy_revision: approved.policy_revision,
    canonical_policy_digest: approved.policy_digest, status: "ACTIVE", expires_at: approved.policy.autonomousWindow.expiresAt,
    repositories: [goal.repository] };
}

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
      .mockResolvedValueOnce(response(template()))
      .mockResolvedValueOnce(response({ autonomy: { active_window: null } }))
      .mockResolvedValueOnce(response({ error: code }, status))
      .mockResolvedValueOnce(response({ autonomy: { active_window: null } }));

    const result = launchExistingGoal(goal, 2);
    await expect(result).rejects.toBeInstanceOf(PlatformClientError);
    await expect(result).rejects.toMatchObject({ status, code });
    expect(fetchMock).toHaveBeenCalledTimes(4);
    const paths = fetchMock.mock.calls.map(([input]) => String(input));
    expect(paths[0]).toMatch(/\/api\/windows\/policy$/);
    expect(paths[3]).toBe(paths[1]);
    expect(paths[2]).toMatch(/\/api\/windows\/activate$/);
    expect(JSON.parse(String(fetchMock.mock.calls[2][1]?.body))).toEqual({ policy_id: template().policy_id, policy_revision: 1, policy: template().policy });
    expect(paths.some((path) => path.endsWith(`/api/goals/${goal.id}/launch`))).toBe(false);
  });

  it("uses a refreshed same-repository window without another activation", async () => {
    const active = approvedWindow();
    const running = { ...goal, status: "RUNNING", window_id: active.id };
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(template()))
      .mockResolvedValueOnce(response({ autonomy: { active_window: null } }))
      .mockResolvedValueOnce(response({ error: "active_window_exists" }, 409))
      .mockResolvedValueOnce(response({ autonomy: { active_window: active } }))
      .mockResolvedValueOnce(response(running))
      .mockResolvedValueOnce(response(running));

    await expect(launchExistingGoal(goal, 2)).resolves.toMatchObject({ window_id: active.id });
    expect(fetchMock).toHaveBeenCalledTimes(6);
    expect(fetchMock.mock.calls[3][0]).toBe(fetchMock.mock.calls[1][0]);
    expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith("/api/windows/activate"))).toHaveLength(1);
    const launch = fetchMock.mock.calls.find(([input]) => String(input).endsWith(`/api/goals/${goal.id}/launch`));
    expect(JSON.parse(String(launch?.[1]?.body))).toEqual({ expected_revision: goal.revision, window_id: active.id });
  });

  it("rejects a refreshed other-repository window before launch", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(template()))
      .mockResolvedValueOnce(response({ autonomy: { active_window: null } }))
      .mockResolvedValueOnce(response({ error: "active_window_exists" }, 409))
      .mockResolvedValueOnce(response({ autonomy: { active_window: { id: "other", repositories: ["other/repository"] } } }));

    await expect(launchExistingGoal(goal, 2)).rejects.toMatchObject({ code: "active_window_repository_conflict" });
    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(fetchMock.mock.calls[3][0]).toBe(fetchMock.mock.calls[1][0]);
  });

  it("rejects same-repository windows with mismatched immutable policy digest", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(template()))
      .mockResolvedValueOnce(response({ autonomy: { active_window: { ...approvedWindow(), canonical_policy_digest: "b".repeat(64) } } }));
    await expect(launchExistingGoal(goal, 2)).rejects.toMatchObject({ code: "active_window_policy_conflict" });
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/activate"))).toBe(false);
  });

  it("does not fabricate activation when no approved host template exists", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response({ available: false, reason: "delegated_policy_authority_unavailable" }));
    await expect(launchExistingGoal(goal, 2)).rejects.toMatchObject({ code: "delegated_policy_authority_unavailable" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("reuses an equivalent offset expiry without creating another window", async () => {
    const approved = template();
    approved.policy.autonomousWindow.expiresAt = "2030-12-31T16:00:00+08:00";
    const active = approvedWindow();
    const running = { ...goal, status: "RUNNING", window_id: active.id };
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(approved))
      .mockResolvedValueOnce(response({ autonomy: { active_window: active } }))
      .mockResolvedValueOnce(response(running))
      .mockResolvedValueOnce(response(running));
    await expect(launchExistingGoal(goal, 2)).resolves.toMatchObject({ window_id: active.id });
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/activate"))).toBe(false);
  });

  it.each(["2030-12-31T08:00:01Z", "not-a-date"])("rejects a changed or invalid stored expiry %s without activation", async (expires_at) => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(template()))
      .mockResolvedValueOnce(response({ autonomy: { active_window: { ...approvedWindow(), expires_at } } }));
    await expect(launchExistingGoal(goal, 2)).rejects.toMatchObject({ code: "active_window_policy_conflict" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/activate"))).toBe(false);
  });

  it("rejects a not-yet-started approved window before any activation", async () => {
    const approved = template();
    approved.policy.autonomousWindow.startsAt = "2030-12-31T07:00:00Z";
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(approved))
      .mockResolvedValueOnce(response({ autonomy: { active_window: approvedWindow() } }));
    await expect(launchExistingGoal(goal, 2)).rejects.toMatchObject({ code: "active_window_policy_conflict" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
