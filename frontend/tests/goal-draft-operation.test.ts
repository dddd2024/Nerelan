import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { createGoalDraft, type StartGoalInput } from "@/lib/goal-start-operation";
import type { PlatformGoal } from "@/lib/platform-client";

const input: StartGoalInput = { objective: "Create a reviewable persistent draft", repository: "owner/repo",
  executorKind: "deterministic_fixture", bindingRef: "", autonomyHours: 2, operationId: "draft-operation-001" };
const draft: PlatformGoal = { id: "goal-draft-001", title: input.objective, objective: input.objective,
  repository: input.repository, status: "DRAFT", revision: 1, executor_kind: "deterministic_fixture",
  orchestration_mode: "single", binding_ref: "", spec_markdown: "", plan_markdown: "", tasks: [],
  acceptance_criteria: [], artifact_digest: "", task_links: [], window_id: "", created_at: "now", updated_at: "now" };
const response = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status });

beforeEach(() => { vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1"); localStorage.clear(); });
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllEnvs(); localStorage.clear(); });

it("deduplicates draft creation and never calls plan, approval, status or window endpoints", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(response(draft, 201));
  const first = createGoalDraft(input);
  const second = createGoalDraft(input);
  expect(second).toBe(first);
  expect(await first).toEqual(draft);
  expect(fetch).toHaveBeenCalledTimes(1);
  const [url, options] = fetch.mock.calls[0];
  expect(url).toBe("http://127.0.0.1:8766/api/goals");
  expect(JSON.parse(String(options?.body))).toMatchObject({ idempotency_key: "ui-goal-draft-operation-001", executor_kind: "deterministic_fixture" });
});

it("reuses the server idempotency key after a lost create response and module reload", async () => {
  const keys: string[] = [];
  const fetch = vi.spyOn(globalThis, "fetch").mockImplementation(async (_url, init) => {
    keys.push(JSON.parse(String(init?.body)).idempotency_key);
    if (keys.length === 1) throw new Error("lost create response");
    return response(draft, 201);
  });
  await expect(createGoalDraft(input)).rejects.toThrow("lost create response");
  vi.resetModules();
  const reloaded = await import("@/lib/goal-start-operation");
  expect((await reloaded.createGoalDraft(input)).id).toBe(draft.id);
  expect(keys).toEqual(["ui-goal-draft-operation-001", "ui-goal-draft-operation-001"]);
  expect(fetch).toHaveBeenCalledTimes(2);
});

it.each(["PLANNED", "APPROVED", "RUNNING", "COMPLETED", "BLOCKED", "INVALIDATED"] as const)(
  "reads a recovered %s Goal without repeating any lifecycle action", async (status) => {
    const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(draft, 201));
    await createGoalDraft(input);
    fetch.mockResolvedValueOnce(response({ ...draft, status, revision: 4 }));
    expect((await createGoalDraft(input)).status).toBe(status);
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(fetch.mock.calls[1][0]).toBe(`http://127.0.0.1:8766/api/goals/${draft.id}`);
    expect(fetch.mock.calls[1][1]?.method).toBeUndefined();
  },
);

it("rejects input reuse and mismatched recovered Goal identity", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(draft, 201));
  await createGoalDraft(input);
  await expect(createGoalDraft({ ...input, objective: "Changed with reused operation" })).rejects.toMatchObject({ code: "goal_start_operation_input_mismatch" });
  expect(fetch).toHaveBeenCalledTimes(1);
  fetch.mockResolvedValueOnce(response({ ...draft, id: "unrelated-goal" }));
  await expect(createGoalDraft(input)).rejects.toMatchObject({ code: "goal_start_unexpected_state" });
  expect(fetch).toHaveBeenCalledTimes(2);
});
