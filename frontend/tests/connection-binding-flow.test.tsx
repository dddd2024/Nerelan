import { screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SettingsPage } from "@/routes/settings";
import { NewTaskComposer } from "@/components/new-task-composer";
import { ConnectionBindingEditor } from "@/components/connection-binding-editor";
import type {
  Connection,
  ConnectionInput,
} from "@/schemas/model-access";
import {
  createHttpModelControlClient,
  getDefaultModelControlClient,
  resetDefaultModelControlClientForTests,
} from "@/lib/model-control-client";
import { renderWithProviders } from "./test-utils";

const DUMMY_SECRET = "issue181-dummy-secret-value";

const FAKE_REPOS = [
  {
    full_name: "dddd2024/reverse-agent",
    html_url: "https://github.com/dddd2024/reverse-agent",
    is_private: false,
    visibility: "public",
    default_branch: "main",
  },
];

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

  it("normalizes configured credential truth without exposing the env reference", async () => {
    const envReference = "SENSITIVE_ENV_REFERENCE_MUST_STAY_SERVER_SIDE";
    const mockFetch = vi.fn(async () =>
      new Response(
        JSON.stringify([
          {
            connection_id: "configured-missing",
            name: "Configured but unavailable",
            provider: "openai-compatible",
            base_url: "https://api.example.test/v1",
            auth_method: "api_key",
            enabled: true,
            credential_configured: true,
            secret_status: "missing",
            external_session_status: "not_applicable",
            api_key_env: envReference,
          },
        ]),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", mockFetch);

    const [connection] = await createHttpModelControlClient().listConnections();

    expect(connection.credentialConfigured).toBe(true);
    expect(connection.secretStatus).toBe("missing");
    expect(JSON.stringify(connection)).not.toContain(envReference);
    expect(connection).not.toHaveProperty("apiKeyEnv");
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
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: Infinity },
    },
  });
  queryClient.setQueryData(["repositories"], FAKE_REPOS);
  return (
    <QueryClientProvider client={queryClient}>
      <NewTaskComposer open={true} onClose={() => undefined} onSubmit={submit} />
    </QueryClientProvider>
  );
}

describe("Connection verify button state", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("Verify button is disabled on new connection create view", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(screen.getByRole("button", { name: "新建连接" }));

    const verifyBtn = screen.getByTestId("test-connection-button");
    expect(verifyBtn).toBeDisabled();
  });

  it("Verify button is enabled for saved clean connection", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    const verifyBtn = screen.getByTestId("test-connection-button");
    expect(verifyBtn).toBeEnabled();
  });

  it("Verify button is disabled after editing Base URL", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    await user.clear(screen.getByLabelText("Base URL"));
    await user.type(screen.getByLabelText("Base URL"), "http://edited.local/v1");

    const verifyBtn = screen.getByTestId("test-connection-button");
    expect(verifyBtn).toBeDisabled();
  });

  it("Verify button is disabled after editing Provider", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    await user.clear(screen.getByLabelText("Provider"));
    await user.type(screen.getByLabelText("Provider"), "openai-compatible");

    const verifyBtn = screen.getByTestId("test-connection-button");
    expect(verifyBtn).toBeDisabled();
  });

  it("Verify button is disabled after editing connection name", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    await user.clear(screen.getByLabelText("连接名称"));
    await user.type(screen.getByLabelText("连接名称"), "X");

    const verifyBtn = screen.getByTestId("test-connection-button");
    expect(verifyBtn).toBeDisabled();
  });

  it("Verify button is disabled after editing enabled checkbox", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    await user.click(screen.getByLabelText("启用该连接"));

    const verifyBtn = screen.getByTestId("test-connection-button");
    expect(verifyBtn).toBeDisabled();
  });

  it("Verify button is disabled when API Key input has a value", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    await user.type(screen.getByLabelText("API Key"), "fresh-input");

    const verifyBtn = screen.getByTestId("test-connection-button");
    expect(verifyBtn).toBeDisabled();
  });

  it("Verify button re-enables after saving a dirty connection", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    await user.clear(screen.getByLabelText("连接名称"));
    await user.type(screen.getByLabelText("连接名称"), "Updated");

    expect(screen.getByTestId("test-connection-button")).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "保存连接" }));
    expect(await screen.findByText("连接已保存")).toBeInTheDocument();

    const verifyBtn = screen.getByTestId("test-connection-button");
    expect(verifyBtn).toBeEnabled();
  });

  it("verify click shows success result with latency", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    await user.click(screen.getByTestId("test-connection-button"));

    const probeResult = await screen.findByTestId("connection-probe-result");
    expect(probeResult.textContent).toContain("验证成功");
    expect(probeResult.textContent).toContain("连接成功");
    expect(probeResult.textContent).toContain("ms");
  });

  it("failed save preserves dirty state, shows error, and keeps Verify disabled", async () => {
    const conn: Connection = {
      connectionId: "coding-connection",
      name: "默认代码连接",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "environment",
      externalSessionStatus: "not_applicable",
    };
    const connections = [conn];
    const executors = [{
      executorId: "opencode",
      name: "OpenCode",
      operational: true,
      capabilities: [],
    }];

    const saveCalls: ConnectionInput[] = [];
    async function onConnectionSave(input: ConnectionInput): Promise<void> {
      saveCalls.push(input);
      await Promise.resolve();
      throw new Error("远端保存失败");
    }
    const user = userEvent.setup();

    renderWithProviders(
      <ConnectionBindingEditor
        view="connection"
        connection={conn}
        binding={null}
        creating={false}
        connections={connections}
        executors={executors}
        busy={false}
        onConnectionSave={onConnectionSave}
        onBindingSave={async () => undefined}
        onConnectionDelete={async () => undefined}
        onBindingDelete={async () => undefined}
        onConnectionTest={async () => undefined}
        connectionProbeResult={null}
        connectionProbePending={false}
      />,
    );

    expect(screen.getByTestId("test-connection-button")).toBeEnabled();

    await user.clear(screen.getByLabelText("连接名称"));
    await user.type(screen.getByLabelText("连接名称"), "FailSave");
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "保存连接" }));

    await waitFor(() => expect(saveCalls).toHaveLength(1));

    expect(
      await screen.findByText("远端保存失败"),
    ).toBeInTheDocument();

    expect(screen.getByTestId("test-connection-button")).toBeDisabled();
    expect(screen.getByLabelText("连接名称")).toHaveValue("FailSave");
  });

  it("failed save does not clear the unsaved API Key as though persisted", async () => {
    const conn: Connection = {
      connectionId: "coding-connection",
      name: "默认代码连接",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "environment",
      externalSessionStatus: "not_applicable",
    };
    const connections = [conn];
    const executors = [{
      executorId: "opencode",
      name: "OpenCode",
      operational: true,
      capabilities: [],
    }];

    const saveCalls: ConnectionInput[] = [];
    function onConnectionSave(input: ConnectionInput): Promise<void> {
      saveCalls.push(input);
      return Promise.reject(new Error("远端保存失败"));
    }

    const user = userEvent.setup();

    renderWithProviders(
      <ConnectionBindingEditor
        view="connection"
        connection={conn}
        binding={null}
        creating={false}
        connections={connections}
        executors={executors}
        busy={false}
        onConnectionSave={onConnectionSave}
        onBindingSave={async () => undefined}
        onConnectionDelete={async () => undefined}
        onBindingDelete={async () => undefined}
        onConnectionTest={async () => undefined}
        connectionProbeResult={null}
        connectionProbePending={false}
      />,
    );

    const apiKeyInput = screen.getByLabelText("API Key") as HTMLInputElement;
    expect(apiKeyInput.value).toBe("");

    await user.type(apiKeyInput, "fresh-key-for-failed-save");
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "保存连接" }));

    await waitFor(() => expect(saveCalls).toHaveLength(1));

    expect(
      await screen.findByText("远端保存失败"),
    ).toBeInTheDocument();

    expect(screen.getByLabelText("API Key")).toHaveValue("fresh-key-for-failed-save");
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();
  });

  it("SettingsPage: real connection save failure propagates rejection, preserves dirty draft and API Key, keeps Verify disabled", async () => {
    resetDefaultModelControlClientForTests();
    const client = getDefaultModelControlClient();
    const originalUpsert = client.upsertConnection.bind(client);
    const saveCalls: ConnectionInput[] = [];
    (client as any).upsertConnection = async (input: ConnectionInput) => {
      saveCalls.push(input);
      throw new Error("远端保存失败");
    };

    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    expect(screen.getByTestId("test-connection-button")).toBeEnabled();

    await user.clear(screen.getByLabelText("连接名称"));
    await user.type(screen.getByLabelText("连接名称"), "FailSave");
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();

    const apiKeyInput = screen.getByLabelText("API Key") as HTMLInputElement;
    await user.type(apiKeyInput, "fresh-key-v5");
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "保存连接" }));

    await waitFor(() => expect(saveCalls).toHaveLength(1));

    expect(
      await screen.findAllByText("远端保存失败"),
    ).toHaveLength(2);
    expect(screen.getByLabelText("连接名称")).toHaveValue("FailSave");
    expect(screen.getByLabelText("API Key")).toHaveValue("fresh-key-v5");
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();
    expect(screen.queryByText("连接已保存")).not.toBeInTheDocument();

    (client as any).upsertConnection = originalUpsert;
  });

  it("prior probe result is hidden while the form is dirty", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    await user.click(screen.getByTestId("test-connection-button"));
    expect(
      await screen.findByTestId("connection-probe-result"),
    ).toHaveTextContent(/验证成功/);

    await user.clear(screen.getByLabelText("Base URL"));
    await user.type(screen.getByLabelText("Base URL"), "http://dirty.local/v1");

    expect(screen.queryByTestId("connection-probe-result")).not.toBeInTheDocument();
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();
  });

  it("a successful save invalidates the previous probe result", async () => {
    const user = userEvent.setup();

    renderWithProviders(<SettingsPage />);

    await user.click(await screen.findByTestId("connection-item-coding-connection"));

    await user.click(screen.getByTestId("test-connection-button"));
    expect(
      await screen.findByTestId("connection-probe-result"),
    ).toHaveTextContent(/验证成功/);

    await user.clear(screen.getByLabelText("连接名称"));
    await user.type(screen.getByLabelText("连接名称"), "Updated After Probe");
    expect(screen.queryByTestId("connection-probe-result")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "保存连接" }));
    expect(await screen.findByText("连接已保存")).toBeInTheDocument();

    expect(screen.queryByTestId("connection-probe-result")).not.toBeInTheDocument();
    expect(screen.getByTestId("test-connection-button")).toBeEnabled();
  });
});

describe("auth-method-aware Connection verification UI", () => {
  const executors = [{
    executorId: "opencode",
    name: "OpenCode",
    operational: true,
    capabilities: [],
  }];

  function renderConnection(
    connection: Connection,
    options: {
      onConnectionSave?: (input: ConnectionInput) => Promise<void>;
      connectionProbeResult?: {
        ok: boolean;
        status: string;
        message: string;
        latencyMs: number | null;
      } | null;
    } = {},
  ) {
    renderWithProviders(
      <ConnectionBindingEditor
        view="connection"
        connection={connection}
        binding={null}
        creating={false}
        connections={[connection]}
        executors={executors}
        busy={false}
        onConnectionSave={options.onConnectionSave ?? (async () => undefined)}
        onBindingSave={async () => undefined}
        onConnectionDelete={async () => undefined}
        onBindingDelete={async () => undefined}
        onConnectionTest={async () => undefined}
        connectionProbeResult={options.connectionProbeResult ?? null}
        connectionProbePending={false}
      />,
    );
  }

  it.each(["account_login", "external_cli_session"] as const)(
    "renders saved %s truthfully and disables generic verification before click",
    (authMethod) => {
      const connection: Connection = {
        connectionId: `${authMethod.replaceAll("_", "-")}-ui`,
        name: authMethod,
        provider: "openai-compatible",
        baseUrl: "https://api.example.com/v1",
        authMethod,
        enabled: true,
        credentialConfigured: false,
        secretStatus: "not_applicable",
        externalSessionStatus: "executor_managed",
      };

      renderConnection(connection);

      expect(screen.getByLabelText("认证方式")).toHaveValue(authMethod);
      expect(screen.queryByLabelText("API Key")).not.toBeInTheDocument();
      expect(screen.getByTestId("test-connection-button")).toBeDisabled();
      expect(
        screen.getByTestId("connection-verification-capability"),
      ).toHaveTextContent(/认证由 OpenCode \/ 外部会话管理/);
    },
  );

  it("keeps saved no-auth Connection independently probeable without an API Key field", () => {
    const connection: Connection = {
      connectionId: "none-ui",
      name: "No Auth",
      provider: "openai-compatible",
      baseUrl: "https://api.example.com/v1",
      authMethod: "none",
      enabled: true,
      credentialConfigured: false,
      secretStatus: "not_applicable",
      externalSessionStatus: "not_applicable",
    };

    renderConnection(connection);

    expect(screen.getByLabelText("认证方式")).toHaveValue("none");
    expect(screen.queryByLabelText("API Key")).not.toBeInTheDocument();
    expect(screen.getByTestId("test-connection-button")).toBeEnabled();
  });

  it("disables verification before click when the saved API Key is missing", () => {
    const connection: Connection = {
      connectionId: "missing-ui",
      name: "Missing Key",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: false,
      secretStatus: "missing",
      externalSessionStatus: "not_applicable",
    };

    renderConnection(connection);

    expect(screen.getByLabelText("认证方式")).toHaveValue("api_key");
    expect(screen.getByLabelText("API Key")).toBeInTheDocument();
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();
    expect(
      screen.getByTestId("connection-verification-capability"),
    ).toHaveTextContent(/请先配置并保存 API Key/);
  });

  it("renders durable stored truth with restart guidance and never echoes a secret", () => {
    const connection: Connection = {
      connectionId: "stored-ui",
      name: "Stored Key",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "stored",
      externalSessionStatus: "not_applicable",
    };

    renderConnection(connection);

    expect(screen.getByLabelText("API Key（已安全保存（系统凭据库））")).toBeInTheDocument();
    expect(
      screen.getByTestId("connection-secret-status-detail"),
    ).toHaveTextContent(/重启后无需重新输入/);
    expect(screen.getByTestId("connection-secret-management")).toBeInTheDocument();
    expect(
      screen.getByTestId("connection-secret-management"),
    ).toHaveTextContent(/不会回显到浏览器/);
    expect(screen.getByLabelText("API Key")).toHaveAttribute(
      "placeholder",
      "已配置；留空表示不替换",
    );
    expect(screen.getByLabelText("API Key")).toHaveValue("");
    expect(screen.getByTestId("test-connection-button")).toBeEnabled();
  });

  it("renders an explicitly locked credential store without fabricating missing state", () => {
    const connection: Connection = {
      connectionId: "locked-ui",
      name: "Locked Store",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "store_locked",
      externalSessionStatus: "not_applicable",
    };

    renderConnection(connection);

    expect(screen.getByLabelText("API Key（系统凭据库不可用或已锁定）")).toBeInTheDocument();
    expect(
      screen.getByTestId("connection-secret-status-detail"),
    ).toHaveTextContent(/保存或替换密钥会失败/);
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();
    expect(
      screen.getByTestId("connection-verification-capability"),
    ).toHaveTextContent(/请先配置并保存 API Key/);
  });

  it("renders replacement-required truth when the stored item was removed externally", () => {
    const connection: Connection = {
      connectionId: "replacement-ui",
      name: "Removed Item",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "replacement_required",
      externalSessionStatus: "not_applicable",
    };

    renderConnection(connection);

    expect(screen.getByLabelText("API Key（需要重新输入 API Key）")).toBeInTheDocument();
    expect(
      screen.getByTestId("connection-secret-status-detail"),
    ).toHaveTextContent(/密钥条目已不存在/);
    expect(screen.getByTestId("test-connection-button")).toBeDisabled();
    expect(
      screen.getByTestId("connection-verification-capability"),
    ).toHaveTextContent(/请先配置并保存 API Key/);
  });

  it("disables verification before click for a disabled Connection", () => {
    const connection: Connection = {
      connectionId: "disabled-ui",
      name: "Disabled",
      provider: "openai-compatible",
      baseUrl: "https://api.example.com/v1",
      authMethod: "none",
      enabled: false,
      credentialConfigured: false,
      secretStatus: "not_applicable",
      externalSessionStatus: "not_applicable",
    };

    renderConnection(connection);

    expect(screen.getByTestId("test-connection-button")).toBeDisabled();
    expect(
      screen.getByTestId("connection-verification-capability"),
    ).toHaveTextContent(/连接已禁用/);
  });

  it("requires explicit clear when configured credential authority is runtime-missing", async () => {
    const connection: Connection = {
      connectionId: "configured-missing-ui",
      name: "Configured Missing",
      provider: "openai-compatible",
      baseUrl: "https://api.example.com/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "missing",
      externalSessionStatus: "not_applicable",
    };
    const save = vi.fn(async (_input: ConnectionInput) => undefined);
    const user = userEvent.setup();

    renderConnection(connection, { onConnectionSave: save });

    expect(screen.getByLabelText("API Key")).toHaveAttribute(
      "placeholder",
      "已配置；留空表示不替换",
    );
    await user.selectOptions(screen.getByLabelText("认证方式"), "none");

    expect(
      screen.getByTestId("connection-authority-change-notice"),
    ).toHaveTextContent(/会丢弃已配置的 API Key 凭据/);
    await user.click(screen.getByRole("button", { name: "保存连接" }));
    expect(
      await screen.findByText(/切换到其他认证方式前必须明确勾选/),
    ).toBeInTheDocument();
    expect(save).not.toHaveBeenCalled();

    await user.click(screen.getByText("清除已保存密钥（clear_secret）"));
    await user.click(screen.getByRole("button", { name: "保存连接" }));

    await waitFor(() => expect(save).toHaveBeenCalledTimes(1));
    expect(save.mock.calls[0][0]).toMatchObject({
      authMethod: "none",
      clearSecret: true,
    });
  });

  it("invalidates a pending destructive clear after reverting to api_key", async () => {
    const connection: Connection = {
      connectionId: "clear-revert-ui",
      name: "Clear Revert",
      provider: "openai-compatible",
      baseUrl: "https://api.example.com/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "missing",
      externalSessionStatus: "not_applicable",
    };
    const save = vi.fn(async (_input: ConnectionInput) => undefined);
    const user = userEvent.setup();

    renderConnection(connection, { onConnectionSave: save });

    await user.selectOptions(screen.getByLabelText("认证方式"), "none");
    await user.click(screen.getByText("清除已保存密钥（clear_secret）"));
    await user.selectOptions(screen.getByLabelText("认证方式"), "api_key");

    expect(
      screen.queryByTestId("connection-authority-change-notice"),
    ).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "保存连接" }));

    await waitFor(() => expect(save).toHaveBeenCalledTimes(1));
    expect(save.mock.calls[0][0].authMethod).toBe("api_key");
    expect(save.mock.calls[0][0].clearSecret).toBeUndefined();
  });

  it("clears an unsaved API Key when auth changes away from api_key", async () => {
    const connection: Connection = {
      connectionId: "clear-hidden-key-ui",
      name: "Clear Hidden Key",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: false,
      secretStatus: "missing",
      externalSessionStatus: "not_applicable",
    };
    const save = vi.fn(async (_input: ConnectionInput) => undefined);
    const user = userEvent.setup();

    renderConnection(connection, { onConnectionSave: save });

    await user.type(screen.getByLabelText("API Key"), "unsaved-hidden-secret");
    await user.selectOptions(screen.getByLabelText("认证方式"), "none");

    expect(screen.queryByLabelText("API Key")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "保存连接" }));
    await waitFor(() => expect(save).toHaveBeenCalledTimes(1));

    const savedInput = save.mock.calls[0][0];
    expect(savedInput.authMethod).toBe("none");
    expect(savedInput.apiKey).toBeUndefined();
  });

  it("localizes backend capability prose instead of rendering raw English", () => {
    const rawEnglish = "Probing this authentication method is not yet supported";
    const connection: Connection = {
      connectionId: "localized-probe-ui",
      name: "Localized Probe",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "environment",
      externalSessionStatus: "not_applicable",
    };

    renderConnection(connection, {
      connectionProbeResult: {
        ok: false,
        status: "unsupported_auth_method",
        message: rawEnglish,
        latencyMs: null,
      },
    });

    const result = screen.getByTestId("connection-probe-result");
    expect(result).toHaveTextContent("当前认证方式不支持独立连接验证");
    expect(result).not.toHaveTextContent(rawEnglish);
  });

  it("renders a saved generic provider ID exactly in the editable provider control", () => {
    const connection: Connection = {
      connectionId: "generic-provider-ui",
      name: "Generic Provider",
      provider: "sensetime",
      baseUrl: "https://api.sensetime.com/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "environment",
      externalSessionStatus: "not_applicable",
    };

    renderConnection(connection);

    const providerInput = screen.getByLabelText("Provider") as HTMLInputElement;
    expect(providerInput.tagName).toBe("INPUT");
    expect(providerInput.value).toBe("sensetime");
    expect(providerInput.list?.id).toBe("connection-provider-presets");
  });

  it("allows editing to another generic safe provider ID and saves it unchanged", async () => {
    const connection: Connection = {
      connectionId: "generic-edit-ui",
      name: "Generic Edit",
      provider: "sensetime",
      baseUrl: "https://api.sensetime.com/v1",
      authMethod: "none",
      enabled: true,
      credentialConfigured: false,
      secretStatus: "not_applicable",
      externalSessionStatus: "not_applicable",
    };
    const save = vi.fn(async (_input: ConnectionInput) => undefined);
    const user = userEvent.setup();

    renderConnection(connection, { onConnectionSave: save });

    await user.clear(screen.getByLabelText("Provider"));
    await user.type(screen.getByLabelText("Provider"), "custom.provider_v2");
    await user.click(screen.getByRole("button", { name: "保存连接" }));

    await waitFor(() => expect(save).toHaveBeenCalledTimes(1));
    expect(save.mock.calls[0][0].provider).toBe("custom.provider_v2");
  });

  it("blocks authority-bearing provider edits without a replacement secret and accepts a replacement key", async () => {
    const connection: Connection = {
      connectionId: "authority-ui",
      name: "Authority",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "environment",
      externalSessionStatus: "not_applicable",
    };
    const save = vi.fn(async (_input: ConnectionInput) => undefined);
    const user = userEvent.setup();

    renderConnection(connection, { onConnectionSave: save });

    expect(
      screen.queryByTestId("connection-authority-change-notice"),
    ).not.toBeInTheDocument();

    await user.clear(screen.getByLabelText("Provider"));
    await user.type(screen.getByLabelText("Provider"), "openai-compatible");

    const notice = screen.getByTestId("connection-authority-change-notice");
    expect(notice).toHaveTextContent(/正在修改认证相关配置/);
    expect(notice).toHaveTextContent(/留空保存不会沿用旧密钥/);

    await user.click(screen.getByRole("button", { name: "保存连接" }));

    expect(
      await screen.findByText(/保存前需要：填写新的 API Key/),
    ).toBeInTheDocument();
    expect(save).not.toHaveBeenCalled();

    await user.type(screen.getByLabelText("API Key"), "replacement-secret");
    await user.click(screen.getByRole("button", { name: "保存连接" }));

    await waitFor(() => expect(save).toHaveBeenCalledTimes(1));
    expect(save.mock.calls[0][0].provider).toBe("openai-compatible");
    expect(save.mock.calls[0][0].apiKey).toBe("replacement-secret");
  });

  it("resolves an authority-bearing edit through the explicit clear-secret choice", async () => {
    const connection: Connection = {
      connectionId: "authority-clear-ui",
      name: "Authority Clear",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "environment",
      externalSessionStatus: "not_applicable",
    };
    const save = vi.fn(async (_input: ConnectionInput) => undefined);
    const user = userEvent.setup();

    renderConnection(connection, { onConnectionSave: save });

    await user.clear(screen.getByLabelText("Base URL"));
    await user.type(screen.getByLabelText("Base URL"), "http://changed.local/v1");

    expect(
      screen.getByTestId("connection-authority-change-notice"),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "保存连接" }));
    expect(save).not.toHaveBeenCalled();

    await user.click(screen.getByText("清除已保存密钥（clear_secret）"));
    await user.click(screen.getByRole("button", { name: "保存连接" }));

    await waitFor(() => expect(save).toHaveBeenCalledTimes(1));
    expect(save.mock.calls[0][0].clearSecret).toBe(true);
  });

  it("hides the authority-change notice when the authority edit is reverted", async () => {
    const connection: Connection = {
      connectionId: "authority-revert-ui",
      name: "Authority Revert",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      credentialConfigured: true,
      secretStatus: "environment",
      externalSessionStatus: "not_applicable",
    };
    const user = userEvent.setup();

    renderConnection(connection);

    await user.clear(screen.getByLabelText("Base URL"));
    await user.type(screen.getByLabelText("Base URL"), "http://changed.local/v1");
    expect(
      screen.getByTestId("connection-authority-change-notice"),
    ).toBeInTheDocument();

    await user.clear(screen.getByLabelText("Base URL"));
    await user.type(screen.getByLabelText("Base URL"), "http://localhost:4000/v1");
    expect(
      screen.queryByTestId("connection-authority-change-notice"),
    ).not.toBeInTheDocument();
  });

  it.each([
    ["available", "可用"],
    ["missing", "未观察到可用会话"],
    ["executor_managed", "由执行器管理"],
  ] as const)(
    "displays sanitized external-session readiness (%s) for executor-managed auth",
    (status, label) => {
      const connection: Connection = {
        connectionId: `session-${status}-ui`,
        name: `Session ${status}`,
        provider: "openai-compatible",
        baseUrl: "https://api.example.com/v1",
        authMethod: "external_cli_session",
        enabled: true,
        credentialConfigured: false,
        secretStatus: "not_applicable",
        externalSessionStatus: status,
      };

      renderConnection(connection);

      const readiness = screen.getByTestId(
        "connection-external-session-readiness",
      );
      expect(readiness).toHaveTextContent(`外部会话状态：${label}`);
    },
  );
});
