import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  startGoal,
  createGoalDraft,
  type StartGoalInput,
} from "@/lib/goal-start-operation";
import type { PlatformGoal, PlatformWindow } from "@/lib/platform-client";
import { profileToPolicy } from "@/lib/profile-mapper";

function approvedTemplate() {
  const policy = profileToPolicy("ASK_FOR_APPROVAL");
  policy.repository = input.repository;
  policy.autonomousWindow.expiresAt = "2030-12-31T08:00:00Z";
  return { available: true, policy_id: "approved-recovery-fixture", policy_revision: 1, policy_digest: "a".repeat(64),
    window_id: "window-recovery-1", policy, confirmation_provenance: { confirmation_mode: "DELEGATED_CONTROLLER", personally_human: false },
    supported_operations: ["execute_task"], validation_command_id: "git_diff_check" };
}

const input: StartGoalInput = {
  objective: "Recover one durable Goal start operation",
  repository: "dddd2024/Nerelan",
  executorKind: "deterministic_fixture",
  bindingRef: "",
  autonomyHours: 2,
  operationId: "operation-recovery-001",
};

function goal(status: PlatformGoal["status"]): PlatformGoal {
  return {
    id: "goal-recovery-1",
    title: "Recover one durable Goal start operation",
    objective: input.objective,
    repository: input.repository,
    status,
    revision: 1,
    spec_markdown: "",
    plan_markdown: "",
    tasks: [],
    acceptance_criteria: [],
    artifact_digest: "",
    executor_kind: "deterministic_fixture",
    orchestration_mode: "single",
    binding_ref: "",
    window_id: status === "RUNNING" ? "window-recovery-1" : "",
    created_at: "2026-09-10T00:00:00Z",
    updated_at: "2026-09-10T00:00:00Z",
    task_links: [],
  };
}

function windowFor(repository = input.repository): PlatformWindow {
  return {
    id: "window-recovery-1",
    policy_id: "approved-recovery-fixture",
    policy_revision: 1,
    canonical_policy_digest: "a".repeat(64),
    status: "ACTIVE",
    expires_at: "2030-12-31T08:00:00Z",
    repositories: [repository],
    capabilities: [
      "execute_task",
      "resume_task",
      "reconcile_task",
      "validate_task",
      "open_draft_pr",
    ],
    max_tasks: 20,
    tasks_started: 0,
    tasks_completed: 0,
    max_token_units: 0,
    max_cost_micro_units: 0,
    per_task_token_reservation: 0,
    per_task_cost_reservation: 0,
    provider_quota_state: "NOT_CONFIGURED",
    enforcement_class: "USAGE_UNKNOWN",
    observed_token_units: 0,
    observed_cost_micro_units: 0,
    unknown_observation_count: 0,
  };
}

function json(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function pathOf(inputValue: RequestInfo | URL) {
  const raw = inputValue instanceof Request ? inputValue.url : String(inputValue);
  return new URL(raw).pathname;
}

function operationStorageKey(operationId = input.operationId) {
  return `nerelan.goal-start.operation.v1:${operationId}`;
}

describe("resumable Goal start operation", () => {
  it("saves a checker draft without reading policy and binds recovery to its actual key", async () => {
    const draftInput: StartGoalInput = { ...input, operationId: "checker-draft-recovery", executorKind: "opencode", checkerDraft: {
      idempotencyKey: "approved-frozen-checker-goal", executorKind: "opencode", orchestrationMode: "single", bindingRef: "",
    } };
    const bodies: unknown[] = [];
    let attempts = 0;
    const fetchMock = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      expect(pathOf(url)).toBe("/api/goals");
      bodies.push(JSON.parse(String(init?.body)));
      attempts += 1;
      if (attempts === 1) throw new TypeError("lost checker draft response");
      return json(goal("DRAFT"));
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(createGoalDraft(draftInput)).rejects.toThrow("lost checker draft response");
    await expect(createGoalDraft({ ...draftInput, checkerDraft: { ...draftInput.checkerDraft!, idempotencyKey: "different-frozen-key" } })).rejects.toMatchObject({ code: "goal_start_operation_input_mismatch" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await expect(createGoalDraft(draftInput)).resolves.toMatchObject({ status: "DRAFT" });
    expect(bodies).toEqual([expect.objectContaining({ idempotency_key: "approved-frozen-checker-goal", executor_kind: "opencode", orchestration_mode: "single", binding_ref: "" }), expect.objectContaining({ idempotency_key: "approved-frozen-checker-goal", executor_kind: "opencode", orchestration_mode: "single", binding_ref: "" })]);
  });
  it("uses the frozen provider-free Goal identity and explicit checker plan", async () => {
    const approved = { ...approvedTemplate(), supported_operations: ["validate_task"], goal_idempotency_key: "approved-checker-goal", plan_task_id: "CHECK001" };
    const active = windowFor();
    let serverGoal = { ...goal("DRAFT"), executor_kind: "opencode" as const, orchestration_mode: "single" as const };
    const bodies: Record<string, unknown>[] = [];
    const fetchMock = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const path = pathOf(url);
      if (path === "/api/windows/policy") return json(approved);
      if (path === "/api/platform/status") return json({ autonomy: { active_window: active } });
      if (init?.body) bodies.push({ path, ...JSON.parse(String(init.body)) });
      if (path.endsWith("/plan")) serverGoal = { ...serverGoal, status: "PLANNED" };
      if (path.endsWith("/approve")) serverGoal = { ...serverGoal, status: "APPROVED" };
      if (path.endsWith("/launch")) serverGoal = { ...serverGoal, status: "RUNNING" };
      return json(serverGoal);
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(startGoal(input)).resolves.toMatchObject({ status: "RUNNING" });
    expect(bodies.find((body) => body.path === "/api/goals")).toMatchObject({ idempotency_key: approved.goal_idempotency_key, executor_kind: "opencode", orchestration_mode: "single", binding_ref: "" });
    expect(bodies.find((body) => String(body.path).endsWith("/plan"))).toMatchObject({ tasks: [expect.objectContaining({ id: "CHECK001", capability: "validate_task", validation_command_id: "git_diff_check" })] });
    expect(bodies.some((body) => "confirmation" in body || "owner_identity" in body)).toBe(false);
  });
  beforeEach(() => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("coalesces duplicates and reuses one idempotency key after a lost create response", async () => {
    let serverGoal = goal("DRAFT");
    let createAttempts = 0;
    let statusReads = 0;
    const idempotencyKeys: string[] = [];
    const fetchMock = vi.fn(
      async (requestInput: RequestInfo | URL, init?: RequestInit) => {
        const path = pathOf(requestInput);
        if (path === "/api/windows/policy") return json(approvedTemplate());
        if (path === "/api/platform/status") {
          statusReads += 1;
          return json({
            autonomy: {
              active_window: statusReads >= 3 ? windowFor() : null,
            },
          });
        }
        if (path === "/api/goals" && init?.method === "POST") {
          createAttempts += 1;
          const body = JSON.parse(String(init.body)) as {
            idempotency_key: string;
          };
          idempotencyKeys.push(body.idempotency_key);
          if (createAttempts === 1) throw new TypeError("lost_create_response");
          return json(serverGoal);
        }
        if (path === `/api/goals/${serverGoal.id}` && !init?.method) {
          return json(serverGoal);
        }
        if (path.endsWith("/plan")) {
          serverGoal = goal("PLANNED");
          return json(serverGoal);
        }
        if (path.endsWith("/approve")) {
          serverGoal = goal("APPROVED");
          return json(serverGoal);
        }
        if (path.endsWith("/launch")) {
          serverGoal = goal("RUNNING");
          return json(serverGoal);
        }
        throw new Error(`unexpected request ${init?.method ?? "GET"} ${path}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    const first = startGoal(input);
    const duplicate = startGoal(input);
    expect(duplicate).toBe(first);
    await expect(first).rejects.toThrow("lost_create_response");
    expect(createAttempts).toBe(1);

    const stored = JSON.parse(
      window.localStorage.getItem(operationStorageKey()) ?? "{}",
    ) as Record<string, unknown>;
    expect(Object.keys(stored).sort()).toEqual([
      "goal_id",
      "idempotency_key",
      "input_fingerprint",
      "operation_id",
      "stage",
      "version",
    ]);
    expect(stored).not.toHaveProperty("objective");
    expect(stored).not.toHaveProperty("bindingRef");
    expect(stored.goal_id).toBe("");

    const result = await startGoal(input);
    expect(result.status).toBe("RUNNING");
    expect(createAttempts).toBe(2);
    expect(new Set(idempotencyKeys)).toEqual(
      new Set([`ui-goal-${input.operationId}`]),
    );
    expect(
      fetchMock.mock.calls.some(
        ([url, init]) =>
          pathOf(url) === "/api/windows/activate" && init?.method === "POST",
      ),
    ).toBe(false);
    expect(window.localStorage.getItem(operationStorageKey())).toBeNull();
  });

  it("reconciles a known Goal before retry and does not repeat a plan that already committed", async () => {
    let serverGoal = goal("DRAFT");
    let createCalls = 0;
    let planCalls = 0;
    let approveCalls = 0;
    let losePlanResponse = true;
    const paths: string[] = [];
    const fetchMock = vi.fn(
      async (requestInput: RequestInfo | URL, init?: RequestInit) => {
        const path = pathOf(requestInput);
        if (path === "/api/windows/policy") return json(approvedTemplate());
        paths.push(`${init?.method ?? "GET"} ${path}`);
        if (path === "/api/platform/status") {
          return json({ autonomy: { active_window: windowFor() } });
        }
        if (path === "/api/goals" && init?.method === "POST") {
          createCalls += 1;
          return json(serverGoal);
        }
        if (path === `/api/goals/${serverGoal.id}` && !init?.method) {
          return json(serverGoal);
        }
        if (path.endsWith("/plan")) {
          planCalls += 1;
          serverGoal = goal("PLANNED");
          if (losePlanResponse) {
            losePlanResponse = false;
            throw new TypeError("lost_plan_response");
          }
          return json(serverGoal);
        }
        if (path.endsWith("/approve")) {
          approveCalls += 1;
          serverGoal = goal("APPROVED");
          return json(serverGoal);
        }
        if (path.endsWith("/launch")) {
          serverGoal = goal("RUNNING");
          return json(serverGoal);
        }
        throw new Error(`unexpected request ${init?.method ?? "GET"} ${path}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(startGoal(input)).rejects.toThrow("lost_plan_response");
    const journalAfterFailure = JSON.parse(
      window.localStorage.getItem(operationStorageKey()) ?? "{}",
    ) as { goal_id?: string };
    expect(journalAfterFailure.goal_id).toBe(serverGoal.id);

    paths.length = 0;
    const result = await startGoal(input);
    expect(paths[0]).toBe(`GET /api/goals/${serverGoal.id}`);
    expect(result.status).toBe("RUNNING");
    expect(createCalls).toBe(1);
    expect(planCalls).toBe(1);
    expect(approveCalls).toBe(1);
  });

  it("fails before Goal creation when another repository owns the active window", async () => {
    const fetchMock = vi.fn(async (requestInput: RequestInfo | URL) => {
      const path = pathOf(requestInput);
        if (path === "/api/windows/policy") return json(approvedTemplate());
      if (path === "/api/platform/status") {
        return json({
          autonomy: { active_window: windowFor("dddd2024/OtherRepo") },
        });
      }
      throw new Error(`unexpected request ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(startGoal(input)).rejects.toMatchObject({
      code: "active_window_repository_conflict",
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(
      fetchMock.mock.calls.some(([url]) => pathOf(url) === "/api/goals"),
    ).toBe(false);
    expect(
      fetchMock.mock.calls.some(
        ([url]) => pathOf(url) === "/api/windows/activate",
      ),
    ).toBe(false);
  });

  it("rejects malformed recovery metadata without making a network request or trusting invented Goal identity", async () => {
    window.localStorage.setItem(
      operationStorageKey(),
      JSON.stringify({
        version: 1,
        operation_id: input.operationId,
        idempotency_key: `ui-goal-${input.operationId}`,
        input_fingerprint: "deadbeef",
        goal_id: "goal-invented",
        stage: "APPROVED",
        authorization: "must-not-be-accepted",
      }),
    );
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(startGoal(input)).rejects.toMatchObject({
      code: "goal_start_journal_invalid",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
