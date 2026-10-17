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

// All requests are local fetch fixtures; no service is contacted.
describe("narrow window adversarial readbacks", () => {
  it.each(["foreign repository", "spent", "wrong policy", "wrong revision"])("rejects existing %s authority", async (kind) => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const { template, window } = fixture();
    const active = { ...window,
      ...(kind === "foreign repository" ? { repositories: ["foreign/repo"] } : {}),
      ...(kind === "spent" ? { tasks_started: 1 } : {}),
      ...(kind === "wrong policy" ? { policy_id: "foreign-policy" } : {}),
      ...(kind === "wrong revision" ? { policy_revision: 2 } : {}),
    };
    const paths: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname; paths.push(path);
      if (path === "/api/windows/policy") return json(template);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: active } });
      throw new Error("Unexpected mutation " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({ status: 409 });
    expect(paths).toEqual(["/api/windows/policy", "/api/platform/status"]);
  });

  it.each(["active response", "empty response", "still active", "read failure", "missing readback"])("reports stop_unverified for %s despite HTTP success", async (kind) => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const { template, window } = fixture();
    let reads = 0;
    const paths: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname; paths.push(path);
      if (path === "/api/windows/policy") return json(template);
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
    const { template, window } = fixture();
    let committed = false;
    let stopped = false;
    let reads = 0;
    const paths: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname;
      paths.push(path);
      if (path === "/api/windows/policy") return json(template);
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
      code: (malformed ? "owner_window_scope_response_mismatch" : "delegated_window_activation_indeterminate")
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
    "active_window_exists",
    "active_window_already_exists:window-concurrent",
    "active_window_already_exists:",
    "active_window_already_exists:../../foreign-window/stop",
    "active_window_already_exists:window-concurrent\n",
    "active_window_already_exists:" + "x".repeat(257),
  ].flatMap(error => ["exact", "foreign", "spent", "wider", "wrong policy", "wrong revision", "wrong digest", "wrong window"]
    .map(kind => ({ error, kind }))))("handles $error with $kind narrow grant without stop or retry", async ({ error, kind }) => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const { template, window } = fixture();
    const active = { ...window,
      ...(kind === "foreign" ? { repositories: ["other/repository"] } : {}),
      ...(kind === "spent" ? { tasks_started: 1 } : {}),
      ...(kind === "wider" ? { max_tasks: 20 } : {}),
      ...(kind === "wrong policy" ? { policy_id: "other-policy" } : {}),
      ...(kind === "wrong revision" ? { policy_revision: 2 } : {}),
      ...(kind === "wrong digest" ? { canonical_policy_digest: "b".repeat(64) } : {}),
      ...(kind === "wrong window" ? { id: "other-window" } : {}),
    };
    const paths: string[] = [];
    let activated = false;
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname; paths.push(path);
      if (path === "/api/windows/policy") return json(template);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: activated ? active : null } });
      if (path === "/api/windows/activate") {
        activated = true;
        return json({ error }, 409);
      }
      throw new Error("Unexpected mutation " + path);
    }));
    const result = ensureApprovedWindow(repo, grant);
    const validConflict = error === "active_window_exists" || error === "active_window_already_exists:window-concurrent";
    if (kind === "exact" && validConflict) await expect(result).resolves.toEqual(active);
    else await expect(result).rejects.toMatchObject({ status: 409,
      code: kind === "foreign" ? "active_window_repository_conflict" : "active_window_policy_conflict" });
    expect(paths).toEqual(["/api/windows/policy", "/api/platform/status", "/api/windows/activate", "/api/platform/status"]);
  });

  it.each([400, 403, 409, 422])("preserves a definitive %s denial with no active window", async (status) => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const { template } = fixture();
    const paths: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const path = new URL(String(url)).pathname; paths.push(path);
      if (path === "/api/windows/policy") return json(template);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: null } });
      if (path === "/api/windows/activate") return json({ error: "repository_workspace_unconfigured" }, status);
      throw new Error("Unexpected mutation " + path);
    }));
    await expect(ensureApprovedWindow(repo, grant)).rejects.toMatchObject({ status, code: "repository_workspace_unconfigured" });
    expect(paths).toEqual(["/api/windows/policy", "/api/platform/status", "/api/windows/activate", "/api/platform/status"]);
  });

  it.each(["matching", "foreign", "wrong revision", "read failure", "still active", "stop active"])("reconciles 409 with %s readback", async (kind) => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1");
    const { template, window } = fixture();
    let activated = false;
    let stopped = false;
    let reads = 0;
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const path = new URL(String(url)).pathname;
      if (path === "/api/windows/policy") return json(template);
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
        expect(payload).toMatchObject({ policy_id: window.policy_id, policy_revision: window.policy_revision });
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
