import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { draftQuickStart, preflightOwnerWindow, PlatformClientError } from "@/lib/platform-client";

beforeEach(() => vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "1"));
afterEach(() => { vi.unstubAllEnvs(); vi.restoreAllMocks(); });

const draftResponse = {
  goals: [{ id: "goal-1", title: "#1350 Fix", status: "PLANNED", tasks: [{ id: "implement" }], publishes_draft_pr: true }],
  preset: "day",
  presets: { day: { hours: 24, max_concurrent: 1, max_retries: 2, max_token_units: 2000000 } },
  request: { goal_ids: ["goal-1"], hours: 24, max_tasks: 6, max_concurrent: 1, max_retries: 2, capabilities: ["execute_task"], max_token_units: 2000000, max_cost_micro_units: 0 },
};

const preflightResponse = {
  ok: true,
  checks: [{ check: "goals", ok: true, reason: "", detail: "1 goals, 2 tasks" }],
  preview: ["implement -> coding-default", "review -> reviewer-default"],
  scope: { repository: "owner/repo", base_sha: "abc", goals: [{ id: "goal-1", objective: "Resolve #1350", mode: "agent_team", tasks: [{ id: "implement", title: "Implement" }] }], pool: [], pool_skipped: [], envelope: {}, paid_api: false },
};

it("drafts quick-start goals with text, repository and optional preset", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify(draftResponse), { status: 201 }));
  const result = await draftQuickStart({ text: "#1350 跑一天", repository: "owner/repo", preset: "day" });
  expect(result).toEqual(draftResponse);
  expect(fetch).toHaveBeenCalledTimes(1);
  const [url, init] = fetch.mock.calls[0];
  expect(url).toBe("http://127.0.0.1:8766/api/quick-start/draft");
  expect(init?.method).toBe("POST");
  expect(JSON.parse(String(init?.body))).toEqual({ text: "#1350 跑一天", repository: "owner/repo", preset: "day" });
});

it("sends an empty preset when none is given", async () => {
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify(draftResponse), { status: 201 }));
  await draftQuickStart({ text: "#1350", repository: "owner/repo" });
  expect(JSON.parse(String(fetch.mock.calls[0][1]?.body))).toEqual({ text: "#1350", repository: "owner/repo", preset: "" });
});

it("passes the host error code through unchanged for draft", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({ error: "quick_start_issue_not_open:1350" }), { status: 409 }));
  await expect(draftQuickStart({ text: "#1350", repository: "owner/repo" })).rejects.toMatchObject(new PlatformClientError(409, "quick_start_issue_not_open:1350"));
});

it("preflights an owner window with the full request envelope", async () => {
  const request = { goal_ids: ["goal-1"], hours: 24, max_tasks: 6, max_concurrent: 1, max_retries: 2, capabilities: ["execute_task"], max_token_units: 2000000, max_cost_micro_units: 0 };
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify(preflightResponse), { status: 200 }));
  const result = await preflightOwnerWindow(request);
  expect(result).toEqual(preflightResponse);
  expect(fetch).toHaveBeenCalledTimes(1);
  const [url, init] = fetch.mock.calls[0];
  expect(url).toBe("http://127.0.0.1:8766/api/owner-window/preflight");
  expect(init?.method).toBe("POST");
  expect(JSON.parse(String(init?.body))).toEqual(request);
});

it("passes the host error code through unchanged for preflight", async () => {
  const request = { goal_ids: ["goal-1"], hours: 24, max_tasks: 6, max_concurrent: 1, max_retries: 2, capabilities: ["execute_task"] };
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({ error: "owner_window_request_invalid" }), { status: 400 }));
  await expect(preflightOwnerWindow(request)).rejects.toMatchObject(new PlatformClientError(400, "owner_window_request_invalid"));
});
