import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { fetchTask } from "@/lib/task-client";

const VALID_STATUSES = new Set(["PASS", "FAIL", "RUNNING", "PENDING"]);

type MockResponse = {
  ok: boolean;
  status: number;
  text: () => Promise<string>;
};

function mockFetch(response: MockResponse) {
  const mockFn: ReturnType<typeof vi.fn> = vi.fn().mockImplementationOnce(
    () => Promise.resolve(response),
  );
  vi.stubGlobal("fetch", mockFn);
  return mockFn;
}

const baseOk = {
  id: "t-001",
  title: "opencode task",
  repository: "dddd2024/reverse-agent",
  execution_id: "exec-001",
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:01Z",
  validation_exit_code: undefined,
  failure_classification: "",
  failure_detail: "",
  validation_command_id: "",
  validation_output_digest: "",
  idempotency_key: "",
  changed_files: [],
  evidence: [],
  events: [],
  frontend_task: undefined,
};

function payload(overrides: Record<string, unknown>) {
  return { ...baseOk, ...overrides };
}

describe("_normalizeTask testStatus derivation", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("OpenCode real-task-shaped success: validation_exit_code=0 yields PASS", async () => {
    mockFetch({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify(
          payload({
            status: "READY_FOR_REVIEW",
            executor_kind: "opencode",
            validation_exit_code: 0,
            frontend_task: {
              id: "t-001",
              title: "opencode task",
              state: "READY_FOR_HUMAN",
              executor: "opencode",
              updatedAt: "2026-08-01T00:00:01Z",
            },
          }),
        ),
    });

    const result = await fetchTask("t-001");
    expect(result.testStatus).toBe("PASS");
    expect(result.executor).toBe("opencode");
    expect(result.validationExitCode).toBe(0);
  });

  it("authoritative override: raw validation_exit_code=0 overrides stale PENDING metadata", async () => {
    mockFetch({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify(
          payload({
            status: "READY_FOR_REVIEW",
            executor_kind: "opencode",
            validation_exit_code: 0,
            frontend_task: {
              id: "t-001",
              title: "opencode task",
              state: "READY_FOR_HUMAN",
              executor: "opencode",
              testStatus: "PENDING",
              updatedAt: "2026-08-01T00:00:01Z",
            },
          }),
        ),
    });

    const result = await fetchTask("t-001");
    expect(result.testStatus).toBe("PASS");
  });

  it("nonzero validation_exit_code yields FAIL", async () => {
    mockFetch({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify(
          payload({
            status: "FAILED",
            executor_kind: "opencode",
            validation_exit_code: 1,
            frontend_task: {
              id: "t-001",
              title: "opencode task",
              state: "FAILED_TERMINAL",
              executor: "opencode",
              testStatus: "PENDING",
              updatedAt: "2026-08-01T00:00:01Z",
            },
          }),
        ),
    });

    const result = await fetchTask("t-001");
    expect(result.testStatus).toBe("FAIL");
  });

  it("VALIDATING status with no validation_exit_code yields RUNNING", async () => {
    mockFetch({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify(
          payload({
            status: "VALIDATING",
            executor_kind: "opencode",
            frontend_task: {
              id: "t-001",
              title: "opencode task",
              state: "RUNNING",
              executor: "opencode",
              updatedAt: "2026-08-01T00:00:01Z",
            },
          }),
        ),
    });

    const result = await fetchTask("t-001");
    expect(result.testStatus).toBe("RUNNING");
  });

  it("not yet validated: no validation_exit_code and not VALIDATING yields PENDING", async () => {
    mockFetch({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify(
          payload({
            status: "QUEUED",
            executor_kind: "opencode",
            frontend_task: {
              id: "t-001",
              title: "opencode task",
              state: "WAITING_FOR_OWNER",
              executor: "opencode",
              updatedAt: "2026-08-01T00:00:01Z",
            },
          }),
        ),
    });

    const result = await fetchTask("t-001");
    expect(result.testStatus).toBe("PENDING");
  });

  it("preserves valid testStatus from frontend_task when no validation_exit_code", async () => {
    mockFetch({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify(
          payload({
            status: "QUEUED",
            executor_kind: "opencode",
            frontend_task: {
              id: "t-001",
              title: "opencode task",
              state: "WAITING_FOR_OWNER",
              executor: "opencode",
              testStatus: "PENDING",
              updatedAt: "2026-08-01T00:00:01Z",
            },
          }),
        ),
    });

    const result = await fetchTask("t-001");
    expect(result.testStatus).toBe("PENDING");
    expect(VALID_STATUSES.has(result.testStatus as string)).toBe(true);
  });

  it("generic RUNNING backend status without VALIDATING does not become validation RUNNING", async () => {
    mockFetch({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify(
          payload({
            status: "RUNNING",
            executor_kind: "opencode",
            frontend_task: {
              id: "t-001",
              title: "opencode task",
              state: "RUNNING",
              executor: "opencode",
              updatedAt: "2026-08-01T00:00:01Z",
            },
          }),
        ),
    });

    const result = await fetchTask("t-001");
    expect(result.testStatus).toBe("PENDING");
  });
});