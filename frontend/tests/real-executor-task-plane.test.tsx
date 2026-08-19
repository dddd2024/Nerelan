import { screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NewTaskComposer } from "@/components/new-task-composer";
import { resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import { renderWithProviders } from "./test-utils";

const FAKE_REPOS = [
  {
    full_name: "dddd2024/reverse-agent",
    html_url: "https://github.com/dddd2024/reverse-agent",
    is_private: false,
    visibility: "public",
    default_branch: "main",
  },
];

function makeQueryClient(repos = FAKE_REPOS) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: Infinity },
    },
  });
  qc.setQueryData(["repositories"], repos);
  return qc;
}

function ComposerMount({
  submit,
  queryClient,
}: {
  submit: (input: unknown) => void;
  queryClient?: QueryClient;
}) {
  const qc = queryClient ?? makeQueryClient();
  return (
    <QueryClientProvider client={qc}>
      <NewTaskComposer open={true} onClose={() => undefined} onSubmit={submit} />
    </QueryClientProvider>
  );
}

describe("real-executor task plane with Connection/Binding architecture", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("Test A: OpenCode submission requires an enabled OpenCode Binding and includes bindingRef and repository", async () => {
    const mockSubmit = vi.fn();
    renderWithProviders(<ComposerMount submit={mockSubmit} />);

    expect(screen.getByTestId("executor-option-opencode")).toBeInTheDocument();
    const notes = screen.getAllByTestId("opencode-model-note");
    expect(notes.length).toBe(1);

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "real opencode task" },
    });

    await waitFor(() => {
      expect((screen.getByTestId("task-opencode-binding-select") as HTMLSelectElement).value).toBe("coding-binding");
    }, { timeout: 3000 });
    await waitFor(() => {
      expect((screen.getByTestId("task-opencode-repository-select") as HTMLSelectElement).value).toBe(
        "https://github.com/dddd2024/reverse-agent",
      );
    }, { timeout: 3000 });

    fireEvent.click(screen.getByTestId("submit-new-task"));

    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(1), {
      timeout: 1000,
    });

    const input = mockSubmit.mock.calls[0][0] as {
      executorKind?: string;
      bindingRef?: string;
      title?: string;
      repository?: string;
    };
    expect(input.title).toBe("real opencode task");
    expect(input.executorKind).toBe("opencode");
    expect(input.bindingRef).toBe("coding-binding");
    expect(input.repository).toBe("https://github.com/dddd2024/reverse-agent");
  });

  it("Test A-API: useCreateTask builds opencode payload with binding_ref and repository, not model_profile_ref", async () => {
    const mockFetch: ReturnType<typeof vi.fn> = vi.fn();
    vi.stubGlobal("fetch", mockFetch);
    vi.stubEnv("VITE_TASK_CLIENT_USE_HTTP", "true");

    let capturedPayload: Record<string, unknown> | undefined;
    mockFetch.mockImplementationOnce(async (_url, opts) => {
      capturedPayload = JSON.parse(String((opts as { body?: string }).body ?? "{}"));
      return {
        ok: true,
        status: 201,
        text: async () =>
          JSON.stringify({
            id: "task-opencode-api-001",
            title: "opencode task",
            repository: "https://github.com/dddd2024/reverse-agent",
            status: "QUEUED",
            executor_kind: "opencode",
            execution_id: "exec-opencode-api-001",
            binding_ref: "coding-binding",
            frontend_task: {
              id: "task-opencode-api-001",
              title: "opencode task",
              state: "WAITING_FOR_OWNER",
              executor: "opencode",
            },
          }),
      };
    });
    mockFetch
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 200,
        text: async () =>
          JSON.stringify({
            id: "task-opencode-api-001",
            title: "opencode task",
            repository: "https://github.com/dddd2024/reverse-agent",
            status: "READY_FOR_REVIEW",
            executor_kind: "opencode",
            execution_id: "exec-opencode-api-001",
            binding_ref: "coding-binding",
            frontend_task: {
              state: "READY_FOR_HUMAN",
              executor: "opencode",
              updatedAt: "2026-08-08T00:00:01Z",
            },
          }),
      }))
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 200,
        text: async () =>
          JSON.stringify({
            id: "task-opencode-api-001",
            title: "opencode task",
            repository: "https://github.com/dddd2024/reverse-agent",
            status: "READY_FOR_REVIEW",
            executor_kind: "opencode",
            execution_id: "exec-opencode-api-001",
            binding_ref: "coding-binding",
            frontend_task: {
              state: "READY_FOR_HUMAN",
              executor: "opencode",
              updatedAt: "2026-08-08T00:00:02Z",
              activity: [
                { id: "e-1", type: "DISCOVERED", title: "Task queued", expanded: false },
                { id: "e-2", type: "EXECUTOR_FINISHED", title: "Executor finished", expanded: false },
              ],
            },
          }),
      }));

    const { useCreateTask } = await import("@/hooks/use-tasks");

    const queryClient = makeQueryClient();

    let resultTask: unknown;
    function RenderMutation() {
      const mutation = useCreateTask();
      return (
        <button
          data-testid="trigger"
          onClick={() => {
            void mutation.mutateAsync({
              title: "opencode task",
              executorKind: "opencode",
              bindingRef: "coding-binding",
              repository: "https://github.com/dddd2024/reverse-agent",
              idempotencyKey: "opencode-key-api-001",
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

    expect(capturedPayload?.executor_kind).toBe("opencode");
    expect(capturedPayload?.binding_ref).toBe("coding-binding");
    expect(capturedPayload?.repository).toBe("https://github.com/dddd2024/reverse-agent");
  });

  it("Test B: OpenCode submit is disabled when no enabled Binding or repository is available", async () => {
    const queryClient = makeQueryClient([]);
    queryClient.setQueryData(["bindings"], []);

    const mockSubmit = vi.fn();
    renderWithProviders(
      <ComposerMount queryClient={queryClient} submit={mockSubmit} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "no binding available" },
    });

    const submitButton = screen.getByTestId("submit-new-task") as HTMLButtonElement;
    expect(submitButton).toBeDisabled();

    fireEvent.click(screen.getByTestId("submit-new-task"));
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it("Test C: explicit fixture selection sends deterministic_fixture without ModelProfile, Binding, or Repository", async () => {
    const mockSubmit = vi.fn();
    renderWithProviders(<ComposerMount submit={mockSubmit} />);

    expect(
      screen.getByTestId("executor-option-deterministic_fixture"),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "fixture mode task" },
    });
    fireEvent.click(screen.getByTestId("executor-option-deterministic_fixture"));

    expect(screen.queryByLabelText("模型配置")).not.toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("submit-new-task")).not.toBeDisabled();
    }, { timeout: 3000 });

    fireEvent.click(screen.getByTestId("submit-new-task"));

    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(1), {
      timeout: 1000,
    });

    const submitted = mockSubmit.mock.calls[0][0] as {
      executorKind?: string;
      modelProfileId?: string;
      bindingRef?: string;
      repository?: string;
      title?: string;
    };
    expect(submitted.executorKind).toBe("deterministic_fixture");
    expect(submitted.modelProfileId).toBeUndefined();
    expect(submitted.bindingRef).toBeUndefined();
    expect(submitted.repository).toBeUndefined();
    expect(submitted.title).toBe("fixture mode task");
  });
});
