import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { saveGoalConfiguration, saveGoalPlan } from "@/lib/goal-continuation-operation";
import type { PlatformGoal } from "@/lib/platform-client";

const goal: PlatformGoal = { id: "goal-review-1", title: "Review", objective: "Original", repository: "owner/old",
  status: "PLANNED", revision: 3, spec_markdown: "Original", plan_markdown: "Plan", acceptance_criteria: ["A"],
  tasks: [{ id: "A", title: "Implement", instruction: "Old instruction", dependencies: [], capability: "execute_task" }],
  artifact_digest: "plan-a", executor_kind: "deterministic_fixture", orchestration_mode: "single", binding_ref: "",
  window_id: "", created_at: "now", updated_at: "now" };
const config = { objective: "Changed", repository: "owner/new", executor_kind: "opencode" as const,
  orchestration_mode: "sequential_team" as const, binding_ref: "coding-selected" };

beforeEach(() => vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1"));
afterEach(() => { vi.unstubAllEnvs(); vi.restoreAllMocks(); });

it("saves explicit configuration on the same Goal/revision without planning or launching", async () => {
  const saved = { ...goal, ...config, status: "DRAFT", revision: 4, artifact_digest: "" };
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(saved)));
  expect(await saveGoalConfiguration(goal, config)).toEqual(saved);
  expect(fetch).toHaveBeenCalledTimes(1);
  const [url, init] = fetch.mock.calls[0];
  expect(url).toBe(`http://127.0.0.1:8766/api/goals/${goal.id}/amend`);
  expect(init?.method).toBe("POST");
  expect(JSON.parse(String(init?.body))).toEqual({ ...config, expected_revision: 3 });
});

it("saves instructions and criteria without dropping task identity/dependencies/capability", async () => {
  const input = { tasks: [{ ...goal.tasks[0], instruction: "Edited instruction" }], acceptance_criteria: ["Edited criterion"] };
  const saved = { ...goal, ...input, revision: 4, artifact_digest: "plan-b" };
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(saved)));
  expect(await saveGoalPlan(goal, input)).toEqual(saved);
  expect(JSON.parse(String(fetch.mock.calls[0][1]?.body))).toEqual({ ...input, expected_revision: 3 });
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("surfaces conflicts once and rejects a mismatched response identity", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({ error: "goal_revision_mismatch" }), { status: 409 }));
  await expect(saveGoalConfiguration(goal, config)).rejects.toMatchObject({ code: "goal_revision_conflict", goalId: goal.id });
  expect(fetch).toHaveBeenCalledTimes(1);
  fetch.mockResolvedValueOnce(new Response(JSON.stringify({ ...goal, id: "other-goal" })));
  await expect(saveGoalPlan(goal, { tasks: goal.tasks, acceptance_criteria: goal.acceptance_criteria })).rejects.toMatchObject({ code: "goal_continuation_failed" });
  expect(fetch).toHaveBeenCalledTimes(2);
});
