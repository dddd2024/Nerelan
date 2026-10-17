import { afterEach, describe, expect, it, vi } from "vitest";
import { ensureApprovedWindow } from "@/lib/platform-client";
import { profileToPolicy } from "@/lib/profile-mapper";

const repo = "dddd2024/Nerelan";
const grant = { autonomyHours: 0.5, operationId: "narrow-delegated-1017" };
function json(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), { status, headers: { "Content-Type": "application/json" } });
}
function fixture(wide = false) {
  const policy = profileToPolicy("ASK_FOR_APPROVAL");
  policy.repository = repo;
  policy.autonomousWindow.startsAt = new Date(Date.now() - 60_000).toISOString();
  policy.autonomousWindow.expiresAt = new Date(Date.now() + (wide ? 120 : 15) * 60_000).toISOString();
  const digest = "a".repeat(64);
  const template = {
    available: true, policy_id: "review-narrow", policy_revision: 1,
    policy_digest: digest, window_id: "window-review", policy,
    confirmation_provenance: { confirmation_mode: "DELEGATED_CONTROLLER", personally_human: false },
    supported_operations: ["execute_task"], validation_command_id: "git_diff_check",
    task_budget: { max_tasks: wide ? 20 : 1, max_concurrent_tasks: wide ? 2 : 1,
      max_retries: wide ? 1 : 0, model_call_limit: 1, provider_call_limit: 1, github_write_limit: 0 },
  };
  const window = { id: "window-review", policy_id: template.policy_id, policy_revision: 1,
    canonical_policy_digest: digest, status: "ACTIVE", expires_at: policy.autonomousWindow.expiresAt,
    repositories: [repo], capabilities: wide ? ["execute_task", "resume_task"] : ["execute_task"],
    max_tasks: wide ? 20 : 1, max_concurrent_tasks: wide ? 2 : 1, max_retries: wide ? 1 : 0,
    tasks_started: 0, tasks_completed: 0 };
  return { template, window };
}
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });
describe("delegated policy cannot silently widen explicitly selected owner grant", () => {
  it("rejects a wider already ACTIVE delegated policy before any window mutation", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const { template, window } = fixture(true);
    const paths: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname; paths.push(path);
      if (path === "/api/windows/policy") return json(template);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: window } });
      throw new Error("Unexpected request: " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({
      code: "owner_window_scope_confirmation_required", status: 409,
    });
    expect(paths).toEqual(["/api/windows/policy"]);
  });
  it("can reuse an exact smaller delegated window", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const { template, window } = fixture();
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname;
      if (path === "/api/windows/policy") return json(template);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: window } });
      throw new Error("Unexpected request: " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).resolves.toMatchObject({ id: "window-review", max_tasks: 1 });
  });
  it("rejects and stops a newly activated delegated window widened by the server", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const { template, window } = fixture();
    let stopped = false;
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname;
      if (path === "/api/windows/policy") return json(template);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: null } });
      if (path === "/api/windows/activate") return json({ ...window, max_tasks: 20 }, 201);
      if (path === "/api/windows/window-review/stop") { stopped = true; return json({ status: "STOPPED" }); }
      throw new Error("Unexpected request: " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({
      code: "owner_window_scope_response_mismatch", status: 409,
    });
    expect(stopped).toBe(true);
  });
  it("never claims safe rollback when the delegated window stop fails", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const { template, window } = fixture();
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname;
      if (path === "/api/windows/policy") return json(template);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: null } });
      if (path === "/api/windows/activate") return json({ ...window, max_tasks: 20 }, 201);
      if (path === "/api/windows/window-review/stop") return json({ error: "window_stop_failed" }, 409);
      throw new Error("Unexpected request: " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({
      code: "owner_window_scope_response_mismatch_stop_unverified", status: 409,
    });
  });
});
