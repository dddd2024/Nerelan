import { webcrypto } from "node:crypto";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { launchExistingGoal } from "@/lib/goal-continuation-operation";
import type { PlatformGoal } from "@/lib/platform-client";

const goal: PlatformGoal = {
  id: "retry-goal", repository: "dddd2024/Nerelan", revision: 7, status: "APPROVED",
  title: "Retry", objective: "Retry the exact launch", spec_markdown: "spec", plan_markdown: "plan",
  tasks: [], acceptance_criteria: [], artifact_digest: "fixture", executor_kind: "deterministic_fixture",
  orchestration_mode: "single", binding_ref: "", window_id: "", created_at: "", updated_at: "",
};

function response(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json" } });
}

function host() {
  let active: Record<string, unknown> | null = null;
  let denied = false;
  const activations: Record<string, unknown>[] = [];
  const launches: Record<string, unknown>[] = [];
  const fetcher = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const path = new URL(String(url)).pathname;
    if (path === "/api/windows/policy") return response({ error: "trusted_policy_unavailable" }, 409);
    if (path === "/api/platform/status") return response({ autonomy: { active_window: active } });
    if (path === "/api/windows/activate") {
      const payload = JSON.parse(String(init?.body));
      activations.push(payload);
      if (denied) return response({ error: "owner_activation_denied" }, 403);
      active = { ...payload, id: "original-window", status: "ACTIVE", tasks_started: 0, tasks_completed: 0 };
      return response(active, 201);
    }
    if (path.endsWith("/launch")) {
      launches.push(JSON.parse(String(init?.body)));
      if (launches.length === 1) return response({ error: "launch_temporarily_failed" }, 503);
      return response({ ...goal, status: "RUNNING", window_id: active?.id });
    }
    if (path === `/api/goals/${goal.id}`) return response({ ...goal, status: "RUNNING", window_id: active?.id });
    throw new Error(`Unexpected request: ${path}`);
  });
  vi.stubGlobal("fetch", fetcher);
  return {
    activations, launches, fetcher,
    get active() { return active!; },
    deny() { denied = true; },
  };
}

beforeEach(() => {
  vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
  vi.stubGlobal("crypto", webcrypto);
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-10-17T12:00:00Z"));
});
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe("existing Goal narrow-window launch retries (local HTTP fixtures only)", () => {
  it("reuses the original unspent window after a failed launch, elapsed time and module reload", async () => {
    const server = host();
    await expect(launchExistingGoal(goal, 0.5)).rejects.toMatchObject({ code: "launch_temporarily_failed" });
    const original = { ...server.active };
    vi.advanceTimersByTime(60_000);
    vi.resetModules();
    const remounted = await import("@/lib/goal-continuation-operation");
    await expect(remounted.launchExistingGoal({ ...goal }, 0.5)).resolves.toMatchObject({ window_id: original.id });
    expect(server.activations).toHaveLength(1);
    expect(server.launches).toEqual([
      { expected_revision: 7, window_id: original.id },
      { expected_revision: 7, window_id: original.id },
    ]);
    expect(server.active).toEqual(original);
    expect(server.activations[0]).toMatchObject({
      repositories: [goal.repository], capabilities: ["execute_task"],
      max_tasks: 1, max_concurrent_tasks: 1, max_retries: 0,
    });
    expect(Date.parse(String(original.expires_at)) - Date.parse(String(original.starts_at))).toBe(30 * 60_000);
  });

  it.each([
    ["different Goal", { ...goal, id: "other-goal" }],
    ["different revision", { ...goal, revision: goal.revision + 1 }],
    ["different repository", { ...goal, repository: "foreign/repository" }],
  ])("does not lend the original window to %s", async (_label, retryGoal) => {
    const server = host();
    await expect(launchExistingGoal(goal, 0.5)).rejects.toMatchObject({ code: "launch_temporarily_failed" });
    vi.advanceTimersByTime(1000);
    await expect(launchExistingGoal(retryGoal, 0.5)).rejects.toMatchObject({ code: "active_window_scope_conflict" });
    expect(server.activations).toHaveLength(1);
    expect(server.launches).toHaveLength(1);
  });

  it.each([
    ["started", { tasks_started: 1 }],
    ["completed", { tasks_completed: 1 }],
    ["expired", { expires_at: "2026-10-17T12:00:00Z" }],
    ["foreign policy", { policy_id: "foreign-policy" }],
    ["foreign policy revision", { policy_revision: 2 }],
    ["widened tasks", { max_tasks: 20 }],
    ["widened capabilities", { capabilities: ["execute_task", "open_draft_pr"] }],
  ])("refuses retry with %s window without activation, launch or stop", async (_label, mutation) => {
    const server = host();
    await expect(launchExistingGoal(goal, 0.5)).rejects.toMatchObject({ code: "launch_temporarily_failed" });
    Object.assign(server.active, mutation);
    const callsBeforeRetry = server.fetcher.mock.calls.length;
    await expect(launchExistingGoal(goal, 0.5)).rejects.toMatchObject({ code: "active_window_scope_conflict" });
    expect(server.fetcher.mock.calls.slice(callsBeforeRetry).map(([url]) => new URL(String(url)).pathname))
      .toEqual(["/api/windows/policy", "/api/platform/status"]);
    expect(server.launches).toHaveLength(1);
    expect(server.activations).toHaveLength(1);
  });

  it("keeps identity stable after denied activation but never launches on denial", async () => {
    const server = host();
    server.deny();
    await expect(launchExistingGoal(goal, 0.5)).rejects.toMatchObject({ code: "owner_activation_denied" });
    vi.advanceTimersByTime(60_000);
    await expect(launchExistingGoal(goal, 0.5)).rejects.toMatchObject({ code: "owner_activation_denied" });
    expect(server.activations).toHaveLength(2);
    expect(server.activations[1].policy_id).toBe(server.activations[0].policy_id);
    expect(server.launches).toHaveLength(0);
  });
});
