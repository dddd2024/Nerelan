import { screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SettingsPage } from "@/routes/settings";
import { NewTaskComposer } from "@/components/new-task-composer";
import {
  resetDefaultModelControlClientForTests,
} from "@/lib/model-control-client";
import { renderWithProviders } from "./test-utils";

const DUMMY_SECRET = "issue181-dummy-secret-value";

describe("settings Connection + Binding flow", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("renders live-shaped Connection and Binding information", async () => {
    renderWithProviders(<SettingsPage />);

    expect(
      await screen.findByRole("heading", { name: "连接与绑定" }),
    ).toBeInTheDocument();

    expect(
      await screen.findByTestId("connection-item-coding-connection"),
    ).toBeInTheDocument();
    expect(screen.getByText("litellm-proxy · api_key")).toBeInTheDocument();

    expect(
      await screen.findByTestId("binding-item-coding-binding"),
    ).toBeInTheDocument();
    expect(screen.getByText("默认代码绑定")).toBeInTheDocument();
  });

  it("raw API key is never rendered in the settings surface", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    expect(await screen.findByText("默认代码连接")).toBeInTheDocument();

    await user.click(screen.getByText("新建连接"));
    await user.type(screen.getByLabelText("连接 ID"), "raw-key-test");
    await user.type(screen.getByLabelText("连接名称"), "Raw Key 测试");
    await user.type(screen.getByLabelText("API Key"), DUMMY_SECRET);
    await user.click(screen.getByRole("button", { name: "保存连接" }));

    expect(await screen.findByText("连接已保存")).toBeInTheDocument();

    expect(screen.queryByText(DUMMY_SECRET)).not.toBeInTheDocument();
  });

  it("creates a new Connection and a new Binding, neither exposing credentials", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(screen.getByRole("button", { name: "新建连接" }));
    await user.type(screen.getByLabelText("连接 ID"), "new-conn");
    await user.type(screen.getByLabelText("连接名称"), "新建连接");
    await user.type(screen.getByLabelText("Base URL"), "http://test.local/v1");
    await user.type(screen.getByLabelText("API Key"), DUMMY_SECRET);
    await user.click(screen.getByRole("button", { name: "保存连接" }));

    expect(await screen.findByText("连接已保存")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "新建绑定" }));
    await user.type(screen.getByLabelText("绑定 ID"), "new-bind");
    await user.type(screen.getByLabelText("绑定名称"), "新建绑定");
    await user.selectOptions(screen.getByLabelText("执行器"), "opencode");
    await user.selectOptions(screen.getByLabelText("连接"), "new-conn");
    await user.type(screen.getByLabelText("Model ID"), "test-model");
    await user.click(screen.getByRole("button", { name: "保存绑定" }));

    expect(await screen.findByText("绑定已保存")).toBeInTheDocument();

    expect(screen.queryByText(DUMMY_SECRET)).not.toBeInTheDocument();
  });
});

describe("OpenCode Binding selection in NewTaskComposer", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("submits bindingRef for OpenCode executor", async () => {
    const mockSubmit = vi.fn();

    renderWithProviders(
      <NewTaskComposerWrapper submit={mockSubmit} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "opencode binding task" },
    });

    await waitFor(() => {
      expect(screen.getByTestId("task-opencode-binding-select")).toBeInTheDocument();
    }, { timeout: 3000 });

    await waitFor(() => {
      const select = screen.getByTestId("task-opencode-binding-select") as HTMLSelectElement;
      expect(select.value).toBe("coding-binding");
    }, { timeout: 3000 });

    fireEvent.change(screen.getByTestId("task-opencode-binding-select") as HTMLSelectElement, {
      target: { value: "coding-binding" },
    });

    await waitFor(() => {
      expect(screen.getByTestId("submit-new-task")).not.toBeDisabled();
    }, { timeout: 3000 });

    fireEvent.click(screen.getByTestId("submit-new-task"));

    await waitFor(() => expect(mockSubmit).toHaveBeenCalledTimes(1), {
      timeout: 1000,
    });

    const input = mockSubmit.mock.calls[0][0] as {
      title?: string;
      executorKind?: string;
      bindingRef?: string;
      modelProfileId?: string;
    };
    expect(input.executorKind).toBe("opencode");
    expect(input.bindingRef).toBe("coding-binding");
    expect(input.modelProfileId).toBeUndefined();
    expect(input.title).toBe("opencode binding task");
  });

  it("OpenCode composer submit is disabled with no selected Binding", async () => {
    const mockSubmit = vi.fn();

    renderWithProviders(
      <NewTaskComposerWrapper submit={mockSubmit} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "no binding title" },
    });

    await waitFor(() => {
      expect(screen.getByTestId("task-opencode-binding-select")).toBeInTheDocument();
    }, { timeout: 3000 });

    const select = screen.getByTestId("task-opencode-binding-select") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "" } });

    await waitFor(() => {
      expect(screen.getByTestId("submit-new-task")).toBeDisabled();
    }, { timeout: 1000 });

    fireEvent.click(screen.getByTestId("submit-new-task"));
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it("deterministic_fixture submits without ModelProfile or Binding", async () => {
    const mockSubmit = vi.fn();

    renderWithProviders(
      <NewTaskComposerWrapper submit={mockSubmit} />,
    );

    fireEvent.change(screen.getByTestId("task-title-input"), {
      target: { value: "fixture task" },
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

    const input = mockSubmit.mock.calls[0][0] as {
      executorKind?: string;
      modelProfileId?: string;
      bindingRef?: string;
      title?: string;
    };
    expect(input.executorKind).toBe("deterministic_fixture");
    expect(input.modelProfileId).toBeUndefined();
    expect(input.bindingRef).toBeUndefined();
    expect(input.title).toBe("fixture task");
  });
});

describe("Task HTTP JSON contains binding_ref and readback preserves bindingRef", () => {
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

  it("createTask POST body contains binding_ref for OpenCode", async () => {
    let capturedBody: Record<string, unknown> | undefined;

    mockFetch.mockImplementationOnce(async (_url, opts) => {
      capturedBody = JSON.parse(String((opts as { body?: string }).body ?? "{}"));
      return {
        ok: true,
        status: 201,
        text: async () =>
          JSON.stringify({
            id: "task-binding-001",
            title: "binding task",
            repository: "dddd2024/reverse-agent",
            status: "QUEUED",
            executor_kind: "opencode",
            execution_id: "exec-binding-001",
            binding_ref: "issue181-opencode",
            frontend_task: {
              id: "task-binding-001",
              title: "binding task",
              state: "WAITING_FOR_OWNER",
              executor: "opencode",
            },
          }),
      };
    });

    const { createTask } = await import("@/lib/task-client");

    await createTask({
      title: "binding task",
      executor_kind: "opencode",
      binding_ref: "issue181-opencode",
      model_profile_ref: "",
    });

    expect(capturedBody?.binding_ref).toBe("issue181-opencode");
    expect(capturedBody?.executor_kind).toBe("opencode");
  });

  it("Task readback preserves bindingRef from binding_ref", async () => {
    mockFetch.mockImplementationOnce(async () => ({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          id: "task-readback-001",
          title: "readback task",
          status: "READY_FOR_REVIEW",
          executor_kind: "opencode",
          binding_ref: "issue181-opencode",
          frontend_task: {
            id: "task-readback-001",
            title: "readback task",
            state: "READY_FOR_HUMAN",
            executor: "opencode",
          },
        }),
    }));

    const { fetchTask } = await import("@/lib/task-client");

    const result = (await fetchTask("task-readback-001")) as {
      bindingRef?: string;
      executor?: string;
    };

    expect(result.bindingRef).toBe("issue181-opencode");
    expect(result.executor).toBe("opencode");
  });

  it("useCreateTask for OpenCode sends binding_ref and receives bindingRef", async () => {
    let capturedBody: Record<string, unknown> | undefined;
    const mockTaskId = "task-flow-binding";

    mockFetch
      .mockImplementationOnce(async (_url, opts) => {
        capturedBody = JSON.parse(String((opts as { body?: string }).body ?? "{}"));
        return {
          ok: true,
          status: 201,
          text: async () =>
            JSON.stringify({
              id: mockTaskId,
              title: "flow binding",
              repository: "dddd2024/reverse-agent",
              status: "QUEUED",
              executor_kind: "opencode",
              execution_id: "exec-flow-binding",
              binding_ref: "issue181-opencode",
              frontend_task: {
                id: mockTaskId,
                title: "flow binding",
                state: "WAITING_FOR_OWNER",
                executor: "opencode",
              },
            }),
        };
      })
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 200,
        text: async () =>
          JSON.stringify({
            id: mockTaskId,
            title: "flow binding",
            repository: "dddd2024/reverse-agent",
            status: "READY_FOR_REVIEW",
            executor_kind: "opencode",
            execution_id: "exec-flow-binding",
            binding_ref: "issue181-opencode",
            frontend_task: {
              id: mockTaskId,
              title: "flow binding",
              state: "READY_FOR_HUMAN",
              executor: "opencode",
            },
          }),
      }))
      .mockImplementationOnce(async () => ({
        ok: true,
        status: 200,
        text: async () =>
          JSON.stringify({
            id: mockTaskId,
            title: "flow binding",
            repository: "dddd2024/reverse-agent",
            status: "READY_FOR_REVIEW",
            executor_kind: "opencode",
            execution_id: "exec-flow-binding",
            binding_ref: "issue181-opencode",
            frontend_task: {
              id: mockTaskId,
              title: "flow binding",
              state: "READY_FOR_HUMAN",
              executor: "opencode",
              updatedAt: "2026-08-12T00:00:02Z",
            },
          }),
      }));

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0, staleTime: Infinity },
      },
    });

    const { useCreateTask } = await import("@/hooks/use-tasks");

    let resultTask: unknown;
    function RenderMutation() {
      const mutation = useCreateTask();
      return (
        <button
          data-testid="trigger"
          onClick={() => {
            void mutation
              .mutateAsync({
                title: "flow binding",
                executorKind: "opencode",
                bindingRef: "issue181-opencode",
                idempotencyKey: "binding-flow-key",
              })
              .then((r) => {
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
    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(3), {
      timeout: 5000,
    });

    expect(capturedBody?.binding_ref).toBe("issue181-opencode");
    expect(capturedBody?.executor_kind).toBe("opencode");
    expect((resultTask as { bindingRef?: string }).bindingRef).toBe(
      "issue181-opencode",
    );
  });
});

function NewTaskComposerWrapper({ submit }: { submit: (input: unknown) => void }) {
  return (
    <NewTaskComposer open={true} onClose={() => undefined} onSubmit={submit} />
  );
}
