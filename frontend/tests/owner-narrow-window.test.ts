import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ensureApprovedWindow } from "@/lib/platform-client";

const json = response;

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
      repositories: [repo], capabilities: ["execute_task"],
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
        repositories: [repo], capabilities: ["execute_task"], max_tasks: 20,
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

// All requests are local fetch fixtures; no service is contacted.
describe("narrow window adversarial readbacks", () => {
  it.each(["foreign repository", "spent", "wrong policy", "wrong revision"])("rejects existing %s authority", async (kind) => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const window = fakeWindow({ policy_id: `owner-ui-${grant.operationId}`, policy_revision: 1,
      repositories: [repo], capabilities: ["execute_task"], max_tasks: 1,
      max_concurrent_tasks: 1, max_retries: 0, expires_at: new Date(Date.now() + 900000).toISOString() });
    const active = { ...window,
      ...(kind === "foreign repository" ? { repositories: ["foreign/repo"] } : {}),
      ...(kind === "spent" ? { tasks_started: 1 } : {}),
      ...(kind === "wrong policy" ? { policy_id: "foreign-policy" } : {}),
      ...(kind === "wrong revision" ? { policy_revision: 2 } : {}),
    };
    const paths: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname; paths.push(path);
      if (path === "/api/windows/policy") return json({ error: "delegated_policy_authority_unavailable" }, 409);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: active } });
      throw new Error("Unexpected mutation " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({ status: 409 });
    expect(paths).toEqual(["/api/windows/policy", "/api/platform/status"]);
  });

  it.each(["active response", "empty response", "still active", "read failure", "missing readback"])("reports stop_unverified for %s despite HTTP success", async (kind) => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const window = fakeWindow({ policy_id: `owner-ui-${grant.operationId}`, policy_revision: 1,
      repositories: [repo], capabilities: ["execute_task"], max_tasks: 1,
      max_concurrent_tasks: 1, max_retries: 0, expires_at: new Date(Date.now() + 900000).toISOString() });
    let reads = 0;
    const paths: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname; paths.push(path);
      if (path === "/api/windows/policy") return json({ error: "delegated_policy_authority_unavailable" }, 409);
      if (path === "/api/platform/status") {
        reads += 1;
        if (reads > 2 && kind === "read failure") throw new Error("read failed");
        if (reads > 2 && kind === "missing readback") return json({ autonomy: {} });
        return json({ autonomy: { active_window: reads === 2 || (reads > 2 && kind === "still active") ? window : null } });
      }
      if (path === "/api/windows/activate") return json({ ...window, max_tasks: 20 }, 201);
      if (path.endsWith("/stop")) return json(kind === "empty response" ? {} : { status: kind === "active response" ? "ACTIVE" : "STOPPED" });
      throw new Error("Unexpected " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({
      code: "owner_window_scope_response_mismatch_stop_unverified", status: 409,
    });
    expect(paths.filter(path => path.endsWith("/stop"))).toHaveLength(1);
    expect(reads).toBe(3);
  });
});

// Commit-before-response fixtures exercise reconciliation, without a live server.
describe("indeterminate activation reconciliation", () => {
  it.each([
    "network", "http 500", "invalid JSON", "null response", "wrong status", "wrong id",
    "still active", "stop active", "status failure", "foreign window", "late commit",
  ])("fails closed after %s", async (kind) => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const window = fakeWindow({ policy_id: `owner-ui-${grant.operationId}`, policy_revision: 1 });
    let committed = false;
    let stopped = false;
    let reads = 0;
    const paths: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname;
      paths.push(path);
      if (path === "/api/windows/policy") return json({ error: "delegated_policy_authority_unavailable" }, 409);
      if (path === "/api/platform/status") {
        reads += 1;
        if (committed && kind === "status failure") throw new Error("status unavailable");
        const active = !committed || kind === "late commit" || (stopped && kind !== "still active") ? null
          : kind === "foreign window" ? { ...window, id: "foreign-window", policy_id: "foreign-policy" } : window;
        return json({ autonomy: { active_window: active } });
      }
      if (path === "/api/windows/activate") {
        committed = true;
        if (kind === "invalid JSON") return new Response("{broken", { status: 201 });
        if (kind === "http 500") return json({ error: "server_failed_after_commit" }, 500);
        if (kind === "null response") return json(null, 201);
        if (kind === "wrong status") return json({ ...window, status: "STOPPED" }, 201);
        if (kind === "wrong id") return json({ ...window, id: "foreign-response-id", status: "BROKEN" }, 201);
        throw new Error("response lost after commit");
      }
      if (path.endsWith("/stop")) {
        expect(path).toBe(`/api/windows/${window.id}/stop`);
        stopped = true;
        return json({ status: kind === "stop active" ? "ACTIVE" : "STOPPED" });
      }
      throw new Error("Unexpected " + path);
    }));
    const malformed = ["null response", "wrong status", "wrong id"].includes(kind);
    const unverified = ["still active", "stop active", "status failure", "foreign window", "late commit"].includes(kind);
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({
      status: 409,
      code: (malformed ? "owner_window_scope_response_mismatch" : "owner_window_activation_indeterminate")
        + (unverified ? "_stop_unverified" : ""),
    });
    expect(stopped).toBe(!["status failure", "foreign window", "late commit"].includes(kind));
    expect(reads).toBe(stopped ? 3 : 2);
    expect(paths.some(path => path.includes("foreign-response-id/stop") || path.includes("foreign-window/stop"))).toBe(false);
  });
});

// Definitive denials still require authenticated evidence before reporting safety.
describe("structured activation denial reconciliation", () => {
  it.each([
    "active_window_already_exists:window-concurrent",
    "active_window_already_exists:../../foreign-window/stop",
  ])("keeps owner fallback fail closed for foreign readback after %s", async (error) => {
    let activated = false;
    const paths: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = pathOf(url); paths.push(path);
      if (path === "/api/windows/policy") return json({ error: "delegated_policy_authority_unavailable" }, 409);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: activated
        ? fakeWindow({ policy_id: "foreign-policy", policy_revision: 1, repositories: ["foreign/repo"] }) : null } });
      if (path === "/api/windows/activate") {
        activated = true;
        return json({ error }, 409);
      }
      throw new Error("Unexpected mutation " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({
      status: 409, code: `${error}_stop_unverified`,
    });
    expect(paths).toEqual(["/api/windows/policy", "/api/platform/status", "/api/windows/activate", "/api/platform/status"]);
  });

  it.each([400, 403, 409, 422])("preserves a definitive %s denial with no active window", async (status) => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const paths: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname; paths.push(path);
      if (path === "/api/windows/policy") return json({ error: "delegated_policy_authority_unavailable" }, 409);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: null } });
      if (path === "/api/windows/activate") return json({ error: "repository_workspace_unconfigured" }, status);
      throw new Error("Unexpected mutation " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({ status, code: "repository_workspace_unconfigured" });
    expect(paths).toEqual(["/api/windows/policy", "/api/platform/status", "/api/windows/activate", "/api/platform/status"]);
  });

  it.each(["matching", "foreign", "wrong revision", "read failure", "still active", "stop active"])("reconciles 409 with %s readback", async (kind) => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const window = fakeWindow({ policy_id: `owner-ui-${grant.operationId}`, policy_revision: 1 });
    let activated = false;
    let stopped = false;
    let reads = 0;
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const path = new URL(String(url)).pathname;
      if (path === "/api/windows/policy") return json({ error: "delegated_policy_authority_unavailable" }, 409);
      if (path === "/api/platform/status") {
        reads += 1;
        if (activated && kind === "read failure") throw new Error("status unavailable");
        const active = !activated || (stopped && kind !== "still active") ? null
          : kind === "foreign" ? { ...window, policy_id: "foreign-policy" }
          : kind === "wrong revision" ? { ...window, policy_revision: 2 } : window;
        return json({ autonomy: { active_window: active } });
      }
      if (path === "/api/windows/activate") {
        const payload = JSON.parse(String(init?.body));
        expect(payload).toMatchObject({ policy_id: `owner-ui-${grant.operationId}`, policy_revision: 1 });
        activated = true;
        return json({ error: "repository_workspace_unconfigured" }, 409);
      }
      if (path.endsWith("/stop")) {
        expect(path).toBe(`/api/windows/${window.id}/stop`);
        stopped = true;
        return json({ status: kind === "stop active" ? "ACTIVE" : "STOPPED" });
      }
      throw new Error("Unexpected " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({ status: 409,
      code: "repository_workspace_unconfigured" + (kind === "matching" ? "" : "_stop_unverified") });
    expect(stopped).toBe(["matching", "still active", "stop active"].includes(kind));
    expect(reads).toBe(stopped ? 3 : 2);
  });
});
