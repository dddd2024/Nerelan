import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderWithProviders } from "./test-utils";
import { TaskCard } from "@/components/task-card";
import { TaskInbox } from "@/components/task-inbox";
import { ActivityStream } from "@/components/activity-stream";
import { ChangesPanel } from "@/components/changes-panel";
import { EvidencePanel } from "@/components/evidence-panel";
import { NewTaskComposer } from "@/components/new-task-composer";
import { resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import type { Task } from "@/types";

const FIXTURE_TASK: Task = {
  id: "task-1723000000000-abcdef123456",
  title: "Provider-free fixture task",
  issueNumber: 128,
  state: "READY_FOR_HUMAN",
  riskTier: "R1",
  updatedAt: "2026-08-07T00:00:00Z",
  permissionProfile: "ASK_FOR_APPROVAL",
  branch: "task-1723000000000-abcdef123456",
  repository: "dddd2024/reverse-agent",
  executionId: "exec-task-1723000000000-abcdef123456",
  executor: "fixture/provider-free",
  validationCommandId: "git_diff_check",
  validationExitCode: 0,
  activity: [
    {
      id: "e-discovered",
      type: "DISCOVERED",
      timestamp: "2026-08-07T00:00:00Z",
      title: "Task queued",
      description: "Task created for dddd2024/reverse-agent",
      expanded: false,
    },
    {
      id: "e-workspace",
      type: "WORKSPACE_READY",
      timestamp: "2026-08-07T00:00:01Z",
      title: "Workspace ready",
      description: "Disposable worktree created",
      expanded: false,
    },
    {
      id: "e-executor",
      type: "EXECUTOR_RUNNING",
      timestamp: "2026-08-07T00:00:02Z",
      title: "Executor running",
      description: "Executor deterministic_fixture started",
      expanded: false,
    },
    {
      id: "e-validated",
      type: "VALIDATED",
      timestamp: "2026-08-07T00:00:03Z",
      title: "Validation passed",
      description: "git_diff_check passed",
      expanded: false,
    },
  ],
  changes: [
    {
      path: "fixture.txt",
      status: "modified",
      additions: 1,
      deletions: 0,
      diff: "+deterministic mutation applied",
    },
  ],
  evidence: [
    {
      id: "ev-1",
      category: "Validation",
      label: "git_diff_check",
      value: "0",
      status: "pass",
      detail: "deterministic fixture validation passed",
      rawJson: "deadbeef",
    },
    {
      id: "ev-2",
      category: "Executor",
      label: "executor_kind",
      value: "deterministic_fixture",
      status: "pass",
      detail: "fixture/provider-free executor",
      rawJson: "",
    },
  ],
  authorityStatus: "APPROVED",
  testStatus: "PASS",
  workflowStatus: "PENDING",
};

const BLOCKED_TASK: Task = {
  ...FIXTURE_TASK,
  id: "task-blocked-001",
  title: "Blocked fixture task",
  state: "BLOCKED_EXTERNAL",
  blocker: "workspace_root_required",
  failureClassification: "blocked",
  testStatus: "FAIL",
  workflowStatus: "FAILURE",
  activity: [
    ...FIXTURE_TASK.activity,
    {
      id: "e-failed",
      type: "EXECUTOR_FINISHED",
      timestamp: "2026-08-07T00:00:04Z",
      title: "Executor failed",
      description: "failure_classification=blocked",
      expanded: false,
    },
  ],
  evidence: [
    ...FIXTURE_TASK.evidence,
    {
      id: "ev-3",
      category: "Failure",
      label: "failure_classification",
      value: "blocked",
      status: "fail",
      detail: "workspace_root_required",
    },
  ],
};

describe("provider-free task plane integration", () => {
  it("task-card shows fixture/provider-free executor badge", () => {
    renderWithProviders(<TaskCard task={FIXTURE_TASK} />);
    expect(screen.getByTestId("task-executor-badge")).toBeInTheDocument();
    expect(
      screen.getByText((content) =>
        content.includes("fixture / provider-free") ||
        content.includes("deterministic_fixture"),
      ),
    ).toBeInTheDocument();
  });

  it("task-inbox places ready-for-human tasks in needs-attention", () => {
    renderWithProviders(
      <TaskInbox tasks={[FIXTURE_TASK, BLOCKED_TASK]} isLoading={false} isError={false} />,
    );
    expect(screen.getByTestId("section-needs-attention")).toBeInTheDocument();
    expect(screen.getByTestId(`task-card-${FIXTURE_TASK.id}`)).toBeInTheDocument();
  });

  it("activity-stream renders provider-free lifecycle events", () => {
    renderWithProviders(<ActivityStream events={FIXTURE_TASK.activity} />);
    expect(screen.getByText("Task queued")).toBeInTheDocument();
    expect(screen.getByText("Workspace ready")).toBeInTheDocument();
    expect(screen.getByText("Validation passed")).toBeInTheDocument();
  });

  it("changes-panel shows fixture changed file", () => {
    renderWithProviders(<ChangesPanel changes={FIXTURE_TASK.changes} />);
    expect(screen.getByText("fixture.txt")).toBeInTheDocument();
  });

  it("evidence-panel shows validation + executor categories", () => {
    renderWithProviders(<EvidencePanel evidence={FIXTURE_TASK.evidence} />);
    expect(screen.getByTestId("evidence-panel")).toBeInTheDocument();
    expect(screen.getByText("Validation")).toBeInTheDocument();
    expect(screen.getByText("Executor")).toBeInTheDocument();
  });

  it("blocked task shows blocker and failure evidence", () => {
    renderWithProviders(
      <TaskInbox tasks={[BLOCKED_TASK]} isLoading={false} isError={false} />,
    );
    expect(
      screen.getByText((content) => content.includes("workspace_root_required")),
    ).toBeInTheDocument();
  });

  it("adapter maps provider-free task fields", () => {
    renderWithProviders(
      <TaskCard
        task={{
          id: "task-adapter",
          title: "Adapter task",
          issueNumber: 0,
          state: "WAITING_FOR_OWNER",
          riskTier: "R1",
          updatedAt: "2026-08-07T00:00:00Z",
          permissionProfile: "ASK_FOR_APPROVAL",
          branch: "task-adapter",
          activity: [],
          changes: [],
          evidence: [],
          authorityStatus: "APPROVED",
          testStatus: "PENDING",
          workflowStatus: "PENDING",
          executor: "fixture/provider-free",
          repository: "dddd2024/reverse-agent",
          executionId: "exec-task-adapter",
        }}
      />,
    );
    expect(screen.getByTestId("task-card-task-adapter")).toBeInTheDocument();
    expect(screen.getByTestId("task-executor-badge")).toBeInTheDocument();
  });
});

describe("provider-free HTTP task flow", () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
    vi.stubGlobal("fetch", mockFetch);
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
  });

  afterEach(() => {
    mockFetch.mockClear();
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("create -> execute -> readback sequence uses server state as truth", async () => {
    const mockTaskId = "task-flow-001";

    const createResponse = {
      id: mockTaskId,
      title: "flow task",
      repository: "dddd2024/reverse-agent",
      status: "QUEUED",
      executor_kind: "deterministic_fixture",
      execution_id: "exec-task-flow-001",
      frontend_task: {
        id: mockTaskId,
        title: "flow task",
        state: "WAITING_FOR_OWNER",
        executor: "fixture/provider-free",
      },
    };

    const executeResponse = {
      id: mockTaskId,
      title: "flow task",
      repository: "dddd2024/reverse-agent",
      status: "READY_FOR_REVIEW_FIXTURE",
      executor_kind: "deterministic_fixture",
      execution_id: "exec-task-flow-001",
      validation_command_id: "git_diff_check",
      validation_exit_code: 0,
      changed_files: [
        { path: "fixture.txt", status: "modified", additions: 1, deletions: 0 },
      ],
      evidence: [
        { id: "ev-1", category: "Validation", label: "git_diff_check", value: "0", status: "pass" },
        { id: "ev-2", category: "Executor", label: "executor_kind", value: "deterministic_fixture", status: "pass" },
      ],
      frontend_task: {
        id: mockTaskId,
        title: "flow task",
        state: "READY_FOR_HUMAN",
        executor: "fixture/provider-free",
        activity: [
          { id: "e-1", type: "DISCOVERED", title: "Task queued", expanded: false },
          { id: "e-4", type: "VALIDATED", title: "Validation passed", expanded: false },
        ],
        changes: [{ path: "fixture.txt", status: "modified", additions: 1, deletions: 0, diff: "" }],
        evidence: [
          { id: "ev-1", category: "Validation", label: "git_diff_check", value: "0", status: "pass" },
          { id: "ev-2", category: "Executor", label: "executor_kind", value: "deterministic_fixture", status: "pass" },
        ],
      },
    };

    mockFetch
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 201,
        text: async () => JSON.stringify(createResponse),
      }))
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(executeResponse),
      }));

    const { createTask, executeTask } = await import("@/lib/task-client");

    const created = await createTask({ title: "flow task", idempotency_key: "flow-key-001" });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch.mock.calls[0][0]).toContain("/api/tasks");
    expect(mockFetch.mock.calls[0][1]?.method).toBe("POST");
    expect(created.state).toBe("WAITING_FOR_OWNER");
    expect(created.executor).toBe("fixture/provider-free");

    const executed = await executeTask(mockTaskId);

    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(mockFetch.mock.calls[1][0]).toContain(`/api/tasks/${mockTaskId}/execute`);
    expect(mockFetch.mock.calls[1][1]?.method).toBe("POST");
    expect(executed.state).toBe("READY_FOR_HUMAN");
    expect(executed.executor).toBe("fixture/provider-free");
    expect(executed.changes).toHaveLength(1);
    expect(executed.evidence).toHaveLength(2);
  });

  it("createTask preserves the caller executor_kind and only falls back to fixture when omitted", async () => {
    let capturedBody: Record<string, unknown> | undefined;
    mockFetch
      .mockImplementationOnce(async (_url, opts) => {
        capturedBody = JSON.parse(String((opts as { body?: string }).body ?? "{}"));
        return {
          ok: true,
          status: 201,
          text: async () =>
            JSON.stringify({
              id: "task-passthrough-opencode",
              title: "opencode task",
              repository: "dddd2024/reverse-agent",
              status: "QUEUED",
              executor_kind: "opencode",
              execution_id: "exec-opencode",
              frontend_task: {
                id: "task-passthrough-opencode",
                title: "opencode task",
                state: "WAITING_FOR_OWNER",
                executor: "opencode",
              },
            }),
        };
      })
      .mockImplementationOnce(async (_url, opts) => {
        capturedBody = JSON.parse(String((opts as { body?: string }).body ?? "{}"));
        return {
          ok: true,
          status: 201,
          text: async () =>
            JSON.stringify({
              id: "task-passthrough-fixture",
              title: "fixture task",
              repository: "dddd2024/reverse-agent",
              status: "QUEUED",
              executor_kind: "deterministic_fixture",
              execution_id: "exec-fixture",
              frontend_task: {
                id: "task-passthrough-fixture",
                title: "fixture task",
                state: "WAITING_FOR_OWNER",
                executor: "fixture/provider-free",
              },
            }),
        };
      })
      .mockImplementationOnce(async (_url, opts) => {
        capturedBody = JSON.parse(String((opts as { body?: string }).body ?? "{}"));
        return {
          ok: true,
          status: 201,
          text: async () =>
            JSON.stringify({
              id: "task-passthrough-default",
              title: "default task",
              repository: "dddd2024/reverse-agent",
              status: "QUEUED",
              executor_kind: "deterministic_fixture",
              execution_id: "exec-default",
              frontend_task: {
                id: "task-passthrough-default",
                title: "default task",
                state: "WAITING_FOR_OWNER",
                executor: "fixture/provider-free",
              },
            }),
        };
      });

    const { createTask } = await import("@/lib/task-client");

    await createTask({
      title: "opencode task",
      executor_kind: "opencode",
      model_profile_ref: "",
    });
    expect(capturedBody?.executor_kind).toBe("opencode");
    expect(capturedBody?.model_profile_ref).toBe("");

    await createTask({
      title: "fixture task",
      executor_kind: "deterministic_fixture",
      model_profile_ref: "some-profile",
    });
    expect(capturedBody?.executor_kind).toBe("deterministic_fixture");
    expect(capturedBody?.model_profile_ref).toBe("some-profile");

    await createTask({ title: "default task" });
    expect(capturedBody?.executor_kind).toBe("deterministic_fixture");
  });

  it("executeTask POSTs to /api/tasks/{id}/execute", async () => {
    mockFetch.mockImplementationOnce(async () => ({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          id: "task-exec-001",
          title: "exec task",
          status: "READY_FOR_REVIEW_FIXTURE",
          executor_kind: "deterministic_fixture",
          frontend_task: { state: "READY_FOR_HUMAN", executor: "fixture/provider-free" },
        }),
    }));

    const { executeTask: execTaskClient } = await import("@/lib/task-client");

    const result = await execTaskClient("task-exec-001");

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch.mock.calls[0][0]).toContain("/api/tasks/task-exec-001/execute");
    expect(mockFetch.mock.calls[0][1]?.method).toBe("POST");
    expect(result.state).toBe("READY_FOR_HUMAN");
  });

  it("fetchTask GETs /api/tasks/{id}", async () => {
    mockFetch.mockImplementationOnce(async () => ({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          id: "task-fetch-001",
          title: "detail task",
          status: "READY_FOR_REVIEW_FIXTURE",
          executor_kind: "deterministic_fixture",
          frontend_task: { state: "READY_FOR_HUMAN", executor: "fixture/provider-free" },
        }),
    }));

    const { fetchTask: fetchTaskClient } = await import("@/lib/task-client");

    const result = await fetchTaskClient("task-fetch-001");

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch.mock.calls[0][0]).toContain("/api/tasks/task-fetch-001");
    expect(result.state).toBe("READY_FOR_HUMAN");
  });

  it("useCreateTask mutation returns GET readback truth after POST create -> POST execute -> GET readback", async () => {
    const mockTaskId = "task-flow-readback";
    const executeUpdatedAt = "2026-08-07T00:00:01Z";
    const readbackUpdatedAt = "2026-08-07T00:00:02Z";

    const createResponse = {
      id: mockTaskId,
      title: "flow task",
      repository: "dddd2024/reverse-agent",
      status: "QUEUED",
      executor_kind: "deterministic_fixture",
      execution_id: "exec-task-flow-readback",
      frontend_task: {
        id: mockTaskId,
        title: "flow task",
        state: "WAITING_FOR_OWNER",
        executor: "fixture/provider-free",
        updatedAt: "2026-08-07T00:00:00Z",
      },
    };

    const executeResponse = {
      id: mockTaskId,
      title: "flow task",
      repository: "dddd2024/reverse-agent",
      status: "READY_FOR_REVIEW_FIXTURE",
      executor_kind: "deterministic_fixture",
      execution_id: "exec-task-flow-readback",
      frontend_task: {
        id: mockTaskId,
        title: "flow task",
        state: "READY_FOR_HUMAN",
        executor: "fixture/provider-free",
        updatedAt: executeUpdatedAt,
      },
    };

    const readbackResponse = {
      id: mockTaskId,
      title: "flow task",
      repository: "dddd2024/reverse-agent",
      status: "READY_FOR_REVIEW_FIXTURE",
      executor_kind: "deterministic_fixture",
      execution_id: "exec-task-flow-readback",
      frontend_task: {
        id: mockTaskId,
        title: "flow task",
        state: "READY_FOR_HUMAN",
        executor: "fixture/provider-free",
        updatedAt: readbackUpdatedAt,
        activity: [
          { id: "e-1", type: "DISCOVERED", title: "Task queued", expanded: false },
          { id: "e-2", type: "EXECUTOR_FINISHED", title: "Executor finished", expanded: false },
        ],
      },
    };

    mockFetch
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 201,
        text: async () => JSON.stringify(createResponse),
      }))
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(executeResponse),
      }))
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(readbackResponse),
      }));

    const { useCreateTask } = await import("@/hooks/use-tasks");

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: Infinity },
      },
    });

    let resultTask: Task | undefined;
    function RenderMutation() {
      const mutation = useCreateTask();
      return (
        <button
          data-testid="trigger"
          onClick={() => {
            void mutation.mutateAsync({
              title: "flow task",
              idempotencyKey: "flow-readback-key",
            }).then((r) => {
              resultTask = r;
            });
          }}
        >
          trigger
        </button>
      );
    }

    renderWithProviders(
      <QueryClientProvider client={queryClient}>
        <RenderMutation />
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByTestId("trigger"));
    await waitFor(() => expect(resultTask).toBeDefined(), { timeout: 5000 });

    expect(mockFetch).toHaveBeenCalledTimes(3);

    expect(mockFetch.mock.calls[0][1]?.method).toBe("POST");
    expect(mockFetch.mock.calls[0][0]).toContain("/api/tasks");

    expect(mockFetch.mock.calls[1][1]?.method).toBe("POST");
    expect(mockFetch.mock.calls[1][0]).toContain(`/api/tasks/${mockTaskId}/execute`);

    expect(mockFetch.mock.calls[2][1]?.method).toBe("GET");
    expect(mockFetch.mock.calls[2][0]).toContain(`/api/tasks/${mockTaskId}`);

    expect(resultTask?.updatedAt).toBe(readbackUpdatedAt);
    expect(resultTask?.updatedAt).not.toBe(executeUpdatedAt);
    expect(resultTask?.state).toBe("READY_FOR_HUMAN");
    expect(resultTask?.executor).toBe("fixture/provider-free");
  });
});

describe("provider-free idempotency transport", () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
    vi.stubGlobal("fetch", mockFetch);
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");
  });

  afterEach(() => {
    mockFetch.mockClear();
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("NewTaskComposer generates idempotencyKey once at submit boundary and passes it through", async () => {
    resetDefaultModelControlClientForTests();
    const mockSubmit = vi.fn();

    renderWithProviders(
      <NewTaskComposerWrapper submit={mockSubmit} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "idempotency test" },
    });

    await waitFor(() => {
      expect((screen.getByTestId("task-opencode-binding-select") as HTMLSelectElement).value).toBe("coding-binding");
    }, { timeout: 3000 });

    fireEvent.click(screen.getByTestId("submit-new-task"));

    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(1), {
      timeout: 1000,
    });

    const input = mockSubmit.mock.calls[0][0] as { title?: string; idempotencyKey?: string; executorKind?: string; bindingRef?: string };
    expect(input.title).toBe("idempotency test");
    expect(input.executorKind).toBe("opencode");
    expect(input.bindingRef).toBe("coding-binding");
    expect(typeof input.idempotencyKey).toBe("string");
    expect(input.idempotencyKey!.length).toBeGreaterThan(0);

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "idempotency test 2" },
    });
    fireEvent.click(screen.getByTestId("submit-new-task"));
    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(2), {
      timeout: 1000,
    });

    const secondInput = mockSubmit.mock.calls[1][0] as { idempotencyKey?: string };
    expect(secondInput.idempotencyKey).not.toBe(input.idempotencyKey);
  });

  it("fixture executor submission passes the model profile id through", async () => {
    resetDefaultModelControlClientForTests();
    const mockSubmit = vi.fn();

    renderWithProviders(
      <NewTaskComposerWrapper submit={mockSubmit} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "fixture mode" },
    });
    fireEvent.click(screen.getByTestId("executor-option-deterministic_fixture"));

    await waitFor(() => {
      expect(screen.getByTestId("submit-new-task")).not.toBeDisabled();
    }, { timeout: 3000 });

    fireEvent.click(screen.getByTestId("submit-new-task"));

    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(1), {
      timeout: 1000,
    });

    const input = mockSubmit.mock.calls[0][0] as {
      executorKind?: string;
      modelProfileId?: string;
      title?: string;
    };
    expect(input.executorKind).toBe("deterministic_fixture");
    expect(input.modelProfileId).toBe("coding-default");
    expect(input.title).toBe("fixture mode");
  });

  it("fixture submission is disabled when no model profile is selected", async () => {
    resetDefaultModelControlClientForTests();
    const mockSubmit = vi.fn();

    renderWithProviders(
      <NewTaskComposerWrapper submit={mockSubmit} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "no profile" },
    });
    fireEvent.click(screen.getByTestId("executor-option-deterministic_fixture"));

    await waitFor(() => {
      expect(screen.getByLabelText("模型配置")).toBeInTheDocument();
    }, { timeout: 3000 });

    const select = screen.getByLabelText("模型配置") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "" } });

    await waitFor(() => {
      expect(screen.getByTestId("submit-new-task")).toBeDisabled();
    }, { timeout: 1000 });

    fireEvent.click(screen.getByTestId("submit-new-task"));
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it("OpenCode execution failure is not silently retried as deterministic_fixture", async () => {
    mockFetch.mockImplementationOnce(async () => ({
      ok: false,
      status: 500,
      text: async () => JSON.stringify({ error: "opencode unavailable" }),
    }));

    const { createTask } = await import("@/lib/task-client");

    await expect(
      createTask({
        title: "opencode will fail",
        executor_kind: "opencode",
        model_profile_ref: "",
      }),
    ).rejects.toThrow(/500/);

    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it("createTask forwards CreateTaskInput.idempotencyKey verbatim as POST body idempotency_key", async () => {
    const fixedKey = "stable-submit-key-001";

    let firstBody: Record<string, unknown> | undefined;

    mockFetch
      .mockImplementationOnce(async (_url, opts) => {
        firstBody = JSON.parse(String((opts as { body?: string }).body ?? "{}"));
        return {
          ok: true,
          status: 201,
          text: async () =>
            JSON.stringify({
              id: "task-idem-001",
              title: "idem task",
              repository: "dddd2024/reverse-agent",
              status: "QUEUED",
              executor_kind: "deterministic_fixture",
              execution_id: "exec-idem-001",
              frontend_task: {
                id: "task-idem-001",
                title: "idem task",
                state: "WAITING_FOR_OWNER",
                executor: "fixture/provider-free",
              },
            }),
        };
      })
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 200,
        text: async () =>
          JSON.stringify({
            id: "task-idem-001",
            title: "idem task",
            repository: "dddd2024/reverse-agent",
            status: "READY_FOR_REVIEW_FIXTURE",
            executor_kind: "deterministic_fixture",
            execution_id: "exec-idem-001",
            frontend_task: {
              id: "task-idem-001",
              title: "idem task",
              state: "READY_FOR_HUMAN",
              executor: "fixture/provider-free",
              updatedAt: "2026-08-07T00:00:01Z",
            },
          }),
      }))
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 200,
        text: async () =>
          JSON.stringify({
            id: "task-idem-001",
            title: "idem task",
            repository: "dddd2024/reverse-agent",
            status: "READY_FOR_REVIEW_FIXTURE",
            executor_kind: "deterministic_fixture",
            execution_id: "exec-idem-001",
            frontend_task: {
              id: "task-idem-001",
              title: "idem task",
              state: "READY_FOR_HUMAN",
              executor: "fixture/provider-free",
              updatedAt: "2026-08-07T00:00:02Z",
            },
          }),
      }));

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: Infinity },
      },
    });

    const { useCreateTask } = await import("@/hooks/use-tasks");

    const variables = { title: "idem task", idempotencyKey: fixedKey };
    function RenderMutation() {
      const mutation = useCreateTask();
      return (
        <button
          data-testid="trigger"
          onClick={() => {
            void mutation.mutateAsync(variables);
          }}
        >
          trigger
        </button>
      );
    }

    renderWithProviders(
      <QueryClientProvider client={queryClient}>
        <RenderMutation />
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByTestId("trigger"));
    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(3), {
      timeout: 5000,
    });

    expect(firstBody?.idempotency_key).toBe(fixedKey);
  });
});

function NewTaskComposerWrapper({ submit }: { submit: (input: unknown) => void }) {
  return (
    <NewTaskComposer open={true} onClose={() => undefined} onSubmit={submit} />
  );
}