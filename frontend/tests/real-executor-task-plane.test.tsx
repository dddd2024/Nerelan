import { screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NewTaskComposer } from "@/components/new-task-composer";
import { resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import { renderWithProviders } from "./test-utils";

function ComposerMount({ submit }: { submit: (input: unknown) => void }) {
  return (
    <NewTaskComposer open={true} onClose={() => undefined} onSubmit={submit} />
  );
}

function QueryClientComposerMount({
  queryClient,
  submit,
}: {
  queryClient: QueryClient;
  submit: (input: unknown) => void;
}) {
  return (
    <QueryClientProvider client={queryClient}>
      <ComposerMount submit={submit} />
    </QueryClientProvider>
  );
}

describe("real-executor task plane", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("Test A: normal real-mode submission sends OpenCode; useCreateTask overrides model_profile_ref to empty", async () => {
    const mockSubmit = vi.fn();
    renderWithProviders(<ComposerMount submit={mockSubmit} />);

    expect(screen.getByTestId("executor-option-opencode")).toBeInTheDocument();

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "real opencode task" },
    });
    fireEvent.click(screen.getByTestId("submit-new-task"));

    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(1), {
      timeout: 1000,
    });

    const input = mockSubmit.mock.calls[0][0] as {
      executorKind?: string;
      title?: string;
    };
    expect(input.title).toBe("real opencode task");
    expect(input.executorKind).toBe("opencode");
  });

  it("Test A-API: useCreateTask builds opencode payload with empty model_profile_ref", async () => {
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
            repository: "dddd2024/reverse-agent",
            status: "QUEUED",
            executor_kind: "opencode",
            execution_id: "exec-opencode-api-001",
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
            status: "READY_FOR_REVIEW",
            executor_kind: "opencode",
            execution_id: "exec-opencode-api-001",
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
            status: "READY_FOR_REVIEW",
            executor_kind: "opencode",
            execution_id: "exec-opencode-api-001",
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

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: Infinity },
      },
    });

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
    expect(capturedPayload?.model_profile_ref).toBe("");
  });

  it("Test B: OpenCode submit is not disabled when no model profile is available", async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: Infinity },
      },
    });
    queryClient.setQueryData(["model-profiles"], []);

    const mockSubmit = vi.fn();
    renderWithProviders(
      <QueryClientComposerMount queryClient={queryClient} submit={mockSubmit} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "no profiles available" },
    });

    const submitButton = screen.getByTestId("submit-new-task") as HTMLButtonElement;
    expect(submitButton).not.toBeDisabled();

    fireEvent.click(screen.getByTestId("submit-new-task"));

    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(1), {
      timeout: 1000,
    });

    const input = mockSubmit.mock.calls[0][0] as {
      executorKind?: string;
      modelProfileId?: string;
    };
    expect(input.executorKind).toBe("opencode");
    expect(input.modelProfileId).toBe("");
  });

  it("Test C: explicit fixture selection sends deterministic_fixture with the model profile", async () => {
    const mockSubmit = vi.fn();
    renderWithProviders(<ComposerMount submit={mockSubmit} />);

    expect(
      screen.getByTestId("executor-option-deterministic_fixture"),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "fixture mode task" },
    });
    fireEvent.click(screen.getByTestId("executor-option-deterministic_fixture"));

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
      title?: string;
    };
    expect(submitted.executorKind).toBe("deterministic_fixture");
    expect(submitted.modelProfileId).toBe("coding-default");
    expect(submitted.title).toBe("fixture mode task");
  });
});
