import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ConversationPanel } from "@/components/conversation-panel";
import { riskTierStyle } from "@/lib/format";
import { createTask, executeTask, fetchTask } from "@/lib/task-client";

const PANEL_TASK = vi.hoisted(() => ({
  id: "task-no-issue",
  title: "Task without issue metadata",
  issueNumber: null,
  state: "WAITING_FOR_OWNER",
  riskTier: "UNKNOWN",
  updatedAt: "",
  permissionProfile: "ASK_FOR_APPROVAL",
  branch: "owner/task-no-issue",
  activity: [],
  changes: [],
  evidence: [],
  authorityStatus: "MISSING",
  testStatus: "PENDING",
  workflowStatus: "UNKNOWN",
  repository: "dddd2024/Nerelan",
}));

vi.mock("@/hooks/use-tasks", () => ({
  useTasks: () => ({
    data: [PANEL_TASK],
    isLoading: false,
    isError: false,
  }),
}));

type MockResponse = {
  ok: boolean;
  status: number;
  text: () => Promise<string>;
};

function mockFetchJson(payload: Record<string, unknown>) {
  const response: MockResponse = {
    ok: true,
    status: 200,
    text: async () => JSON.stringify(payload),
  };
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(response));
}

function httpTask(overrides: Record<string, unknown> = {}) {
  return {
    id: "task-http",
    title: "HTTP governance task",
    repository: "dddd2024/Nerelan",
    status: "READY_FOR_REVIEW",
    executor_kind: "deterministic_fixture",
    execution_id: "exec-http",
    created_at: "2026-09-04T00:00:00Z",
    updated_at: "2026-09-04T00:00:01Z",
    validation_exit_code: undefined,
    failure_classification: "",
    changed_files: [],
    evidence: [],
    events: [],
    ...overrides,
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("Task governance truth", () => {
  it("fails closed when HTTP governance metadata is absent", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    mockFetchJson(httpTask());

    const result = await fetchTask("task-http");

    expect(result.issueNumber).toBeNull();
    expect(result.riskTier).toBe("UNKNOWN");
    expect(result.authorityStatus).toBe("MISSING");
    expect(result.workflowStatus).toBe("UNKNOWN");
    expect(result.testStatus).toBe("PENDING");
  });

  it("preserves explicit valid frontend governance while testStatus stays evidence-derived", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    mockFetchJson(
      httpTask({
        validation_exit_code: 0,
        frontend_task: {
          id: "task-http",
          title: "HTTP governance task",
          state: "READY_FOR_HUMAN",
          issueNumber: 381,
          riskTier: "R2",
          authorityStatus: "APPROVED",
          workflowStatus: "SUCCESS",
          testStatus: "PENDING",
        },
      }),
    );

    const result = await fetchTask("task-http");

    expect(result.issueNumber).toBe(381);
    expect(result.riskTier).toBe("R2");
    expect(result.authorityStatus).toBe("APPROVED");
    expect(result.workflowStatus).toBe("SUCCESS");
    expect(result.testStatus).toBe("PASS");
  });

  it("preserves explicit valid backend snake_case governance", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    mockFetchJson(
      httpTask({
        issue_number: 607,
        risk_tier: "R3",
        authority_status: "REVOKED",
        workflow_status: "NEUTRALIZED",
      }),
    );

    const result = await fetchTask("task-http");

    expect(result.issueNumber).toBe(607);
    expect(result.riskTier).toBe("R3");
    expect(result.authorityStatus).toBe("REVOKED");
    expect(result.workflowStatus).toBe("NEUTRALIZED");
  });

  it("rejects malformed issue numbers and invalid governance enums", async () => {
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
    mockFetchJson(
      httpTask({
        frontend_task: {
          id: "task-http",
          title: "HTTP governance task",
          state: "READY_FOR_HUMAN",
          issueNumber: "381",
          riskTier: "R9",
          authorityStatus: "YES",
          workflowStatus: "DONE",
        },
      }),
    );

    const result = await fetchTask("task-http");

    expect(result.issueNumber).toBeNull();
    expect(result.riskTier).toBe("UNKNOWN");
    expect(result.authorityStatus).toBe("MISSING");
    expect(result.workflowStatus).toBe("UNKNOWN");
  });

  it("mock create and execute paths fail closed without fabricating governance", async () => {
    const created = await createTask({ title: "mock create" });
    const executed = await executeTask("mock-task");

    for (const result of [created, executed]) {
      expect(result.issueNumber).toBeNull();
      expect(result.riskTier).toBe("UNKNOWN");
      expect(result.authorityStatus).toBe("MISSING");
      expect(result.workflowStatus).toBe("UNKNOWN");
    }
    expect(created.testStatus).toBe("PENDING");
    expect(executed.testStatus).toBe("PASS");
  });

  it("omits absent issue metadata from rendering and search", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ConversationPanel open onClose={() => {}} />
      </MemoryRouter>,
    );

    const panel = screen.getByTestId("conversation-panel");
    expect(panel).not.toHaveTextContent("#0");
    expect(panel).not.toHaveTextContent("#null");

    const input = screen.getByTestId("task-search-input");
    await user.type(input, "#null");
    expect(screen.getByTestId("conversation-panel-empty")).toBeInTheDocument();
    await user.clear(input);
    await user.type(input, "#0");
    expect(screen.getByTestId("conversation-panel-empty")).toBeInTheDocument();
  });

  it("renders UNKNOWN risk with a neutral non-authoritative style", () => {
    const style = riskTierStyle("UNKNOWN");

    expect(style.label).toBe("风险未提供");
    expect(style.badge).toContain("slate");
    expect(style.dot).toContain("slate");
    expect(style.badge).not.toContain("rose");
    expect(style.badge).not.toContain("amber");
  });
});
