import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ensureApprovedWindow } from "@/lib/platform-client";

function response(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status, headers: { "Content-Type": "application/json" },
  });
}
function pathOf(value: RequestInfo | URL): string {
  return new URL(value instanceof Request ? value.url : String(value)).pathname;
}
const repo = "dddd2024/Nerelan";
const grant = { autonomyHours: 0.5, operationId: "owner-narrow-1017" };

function fakeWindow(payload: Record<string, any>, widen = false) {
  return {
    ...payload, id: "window-strict-1", status: "ACTIVE",
    max_tasks: widen ? 20 : payload.max_tasks,
    tasks_started: 0, tasks_completed: 0,
  };
}

beforeEach(() => vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1"));
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe("owner-approved 30-minute one-task authorization", () => {
  it("sends a narrow scope and accepts the exact server grant", async () => {
    const seen: Record<string, any>[] = [];
    const fetcher = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const path = pathOf(url);
      if (path === "/api/windows/policy") {
        return response({ error: "delegated_policy_authority_unavailable" }, 409);
      }
      if (path === "/api/platform/status") return response({ autonomy: { active_window: null } });
      if (path === "/api/windows/activate") {
        const payload = JSON.parse(String(init?.body));
        seen.push(payload);
        return response(fakeWindow(payload), 201);
      }
      throw new Error("Unexpected " + path);
    });
    vi.stubGlobal("fetch", fetcher);
    await expect(ensureApprovedWindow(repo, grant)).resolves.toMatchObject({ max_tasks: 1 });
    expect(seen).toHaveLength(1);
    expect(seen[0]).toMatchObject({
      repositories: [repo], capabilities: ["execute_task", "validate_task"],
      max_tasks: 1, max_concurrent_tasks: 1, max_retries: 0,
    });
    const ms = Date.parse(seen[0].expires_at) - Date.parse(seen[0].starts_at);
    expect(ms).toBe(30 * 60 * 1000);
  });

  it("rejects widened server grants and retires the unexpected window", async () => {
    let stopped = false;
    const fetcher = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const path = pathOf(url);
      if (path === "/api/windows/policy") return response({ error: "delegated_policy_authority_unavailable" }, 409);
      if (path === "/api/platform/status") return response({ autonomy: { active_window: null } });
      if (path === "/api/windows/activate") return response(fakeWindow(JSON.parse(String(init?.body)), true), 201);
      if (path === "/api/windows/window-strict-1/stop") {
        stopped = true;
        return response({ status: "STOPPED" });
      }
      throw new Error("Unexpected " + path);
    });
    vi.stubGlobal("fetch", fetcher);
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({
      code: "owner_window_scope_response_mismatch", status: 409,
    });
    expect(stopped).toBe(true);
  });

  it("never reuses an existing 20-task window for a narrow authorization", async () => {
    let activated = false;
    const fetcher = vi.fn(async (url: RequestInfo | URL) => {
      const path = pathOf(url);
      if (path === "/api/windows/policy") return response({ error: "delegated_policy_authority_unavailable" }, 409);
      if (path === "/api/platform/status") return response({ autonomy: { active_window: fakeWindow({
        repositories: [repo], capabilities: ["execute_task", "validate_task"], max_tasks: 20,
        max_concurrent_tasks: 2, max_retries: 1, expires_at: new Date(Date.now() + 3600000).toISOString(),
      }) } });
      if (path === "/api/windows/activate") { activated = true; throw new Error("Unexpected activation"); }
      throw new Error("Unexpected " + path);
    });
    vi.stubGlobal("fetch", fetcher);
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({
      code: "active_window_scope_conflict", status: 409,
    });
    expect(activated).toBe(false);
  });
});
