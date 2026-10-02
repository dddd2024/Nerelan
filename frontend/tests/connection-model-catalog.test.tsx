import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ConnectionBindingEditor } from "@/components/connection-binding-editor";
import { SettingsPage } from "@/routes/settings";
import { getDefaultModelControlClient, resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import type { Connection, ConnectionModelsResult, Binding, Executor, CatalogBindingInput, CatalogBindingResult } from "@/schemas/model-access";
import { CONNECTIONS_QUERY_KEY } from "@/hooks/use-model-access";
import { makeQueryClient, renderWithProviders } from "./test-utils";

const connection: Connection = {
  connectionId: "catalog-a", name: "Catalog A", provider: "openrouter", baseUrl: "https://catalog.example.test/v1",
  authMethod: "none", enabled: true, credentialConfigured: false, secretStatus: "not_applicable", externalSessionStatus: "not_applicable",
  upstreamProviderId: null, protocolFamily: "openai", executorProviderId: "openrouter",
};
const binding: Binding = { bindingId: "manual-a", name: "Manual A", executorId: "opencode", connectionId: "catalog-a",
  modelId: "openrouter/manual-model", enabled: false };
const executors: Executor[] = [{ executorId: "opencode", name: "OpenCode", operational: true, capabilities: ["workspace_execution"] }];
function catalog(id = "catalog-a", models = ["anthropic/claude-test"]): ConnectionModelsResult {
  return { ok: true, status: models.length ? "advertised" : "empty", message: "synthetic catalog fixture", latencyMs: 1,
    models, modelRecords: models.map((modelId) => ({ modelId, displayName: null, ownedBy: null })), connectionId: id,
    configurationRevision: `configuration-${id}`, catalogRevision: `catalog-${id}`, observedAt: "2026-10-02T00:00:00Z",
    source: "provider_advertised", entitlement: "not_observed" };
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}
function editor(fetchModels: (id: string) => Promise<ConnectionModelsResult>, selected = connection, currentBinding = binding,
  select?: (input: CatalogBindingInput) => Promise<CatalogBindingResult>) {
  return <ConnectionBindingEditor view="binding" connection={null} binding={currentBinding} creating={false}
    connections={[selected]} executors={executors} busy={false} onConnectionSave={async () => undefined}
    onBindingSave={async () => undefined} onConnectionDelete={async () => undefined} onBindingDelete={async () => undefined}
    onConnectionTest={async () => undefined} onConnectionModelsFetch={fetchModels} onCatalogBindingSelect={select}
    connectionProbeResult={null} connectionProbePending={false} />;
}

describe("saved model catalog UI", () => {
  beforeEach(() => resetDefaultModelControlClientForTests());
  afterEach(() => vi.restoreAllMocks());

  it("reads the saved catalog after connection save and creates a versioned binding without typing a model ID", async () => {
    const user = userEvent.setup();
    const client = getDefaultModelControlClient();
    const selectSpy = vi.spyOn(client, "selectCatalogBinding");
    const previewSpy = vi.spyOn(client, "recommendModelSelection");
    const manualSpy = vi.spyOn(client, "upsertBinding");
    const initialBindings = await client.listBindings();
    renderWithProviders(<SettingsPage />);
    await screen.findByTestId("connection-item-coding-connection");
    await user.click(screen.getByRole("button", { name: "新建连接" }));
    await user.type(screen.getByLabelText("连接 ID"), "saved-catalog");
    await user.type(screen.getByLabelText("连接名称"), "Saved Catalog");
    await user.type(screen.getByLabelText("API Key"), "synthetic-ui-key");
    await user.click(screen.getByRole("button", { name: "保存连接" }));
    const modelSelect = await screen.findByLabelText("提供方公布的模型");
    expect(screen.getByTestId("connection-model-catalog")).toHaveTextContent(/尚未验证账户使用权限或任务执行可用性/);
    expect(screen.getByRole("button", { name: "使用目录模型创建或复用绑定" })).toBeDisabled();
    await user.selectOptions(modelSelect, "mock-model-a");
    await user.selectOptions(screen.getByLabelText("目录绑定执行器"), "opencode");
    await user.click(screen.getByRole("button", { name: "使用目录模型创建或复用绑定" }));
    await waitFor(() => expect(selectSpy).toHaveBeenCalledTimes(1));
    expect(selectSpy.mock.calls[0][0]).toMatchObject({ connectionId: "saved-catalog", executorId: "opencode", modelId: "mock-model-a" });
    expect(selectSpy.mock.calls[0][0].configurationRevision).toMatch(/^mock-config-/);
    expect(manualSpy).not.toHaveBeenCalled();
    const preview = await screen.findByTestId("model-selection-preview");
    expect(preview).toHaveTextContent(/执行器就绪性尚未观测/);
    expect(preview).toHaveTextContent(/不会启动任务、切换默认绑定或授予 GPT 调用权限/);
    expect(previewSpy.mock.calls[0][0]).toMatchObject({ selectionMode: "manual", purpose: "development" });
    expect(await client.listBindings()).toEqual(expect.arrayContaining(initialBindings));
    expect(screen.queryByText("synthetic-ui-key")).not.toBeInTheDocument();
    await user.click(screen.getByTestId("connection-item-saved-catalog"));
    expect(screen.queryByTestId("model-selection-preview")).not.toBeInTheDocument();
  });

  it("discards an old connection response after switching the binding connection", async () => {
    const first = deferred<ConnectionModelsResult>();
    const fetchModels = vi.fn((_id: string) => first.promise);
    const { rerender } = renderWithProviders(editor(fetchModels));
    fireEvent.click(screen.getByTestId("fetch-models-button"));
    expect(await screen.findByText("正在获取模型目录…")).toBeInTheDocument();
    const next = { ...connection, connectionId: "catalog-b", name: "Catalog B" };
    rerender(editor(fetchModels, next, { ...binding, connectionId: "catalog-b" }));
    await act(async () => first.resolve(catalog()));
    expect(screen.queryByLabelText("提供方公布的模型")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Model ID")).toHaveValue(binding.modelId);
  });

  it("discards an old same-ID response when public connection configuration changes", async () => {
    const old = deferred<ConnectionModelsResult>();
    const fresh = deferred<ConnectionModelsResult>();
    const fetchModels = vi.fn().mockImplementationOnce(() => old.promise).mockImplementationOnce(() => fresh.promise);
    const { rerender } = renderWithProviders(editor(fetchModels));
    fireEvent.click(screen.getByTestId("fetch-models-button"));
    rerender(editor(fetchModels, { ...connection, baseUrl: "https://changed.example.test/v1" }));
    fireEvent.click(screen.getByTestId("fetch-models-button"));
    await act(async () => fresh.resolve(catalog("catalog-a", ["fresh-model"])));
    expect(await screen.findByLabelText("提供方公布的模型")).toHaveTextContent("fresh-model");
    await act(async () => old.resolve(catalog("catalog-a", ["old-model"])));
    expect(screen.queryByRole("option", { name: "old-model" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("Model ID")).toHaveValue(binding.modelId);
  });

  it.each([
    ["empty", "提供方公布的模型目录为空"],
    ["unsupported_auth_method", "当前认证方式不支持获取模型列表"],
    ["live_probe_disabled", "实时模型目录读取未启用"],
    ["credential_missing", "API Key 未配置或需要重新输入"],
    ["catalog_changed", "连接配置或目录已变化"],
  ])("renders the finite %s state in Chinese without usable choices or raw provider prose", async (status, message) => {
    const fetchModels = vi.fn(async () => ({ ...catalog("catalog-a", []), ok: status === "empty", status,
      message: "RAW_PROVIDER_PROSE_MUST_NOT_RENDER", catalogRevision: null, source: null } as ConnectionModelsResult));
    renderWithProviders(editor(fetchModels));
    fireEvent.click(screen.getByTestId("fetch-models-button"));
    expect(await screen.findByTestId("connection-models-message")).toHaveTextContent(message);
    expect(screen.queryByLabelText("提供方公布的模型")).not.toBeInTheDocument();
    expect(screen.queryByText("RAW_PROVIDER_PROSE_MUST_NOT_RENDER")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Model ID")).toHaveValue(binding.modelId);
  });

  it("keeps Native CLI manual model settings and states that its directory is unsupported", () => {
    const native = { ...connection, provider: "codex", authMethod: "external_cli_session" as const,
      externalSessionStatus: "available" as const, protocolFamily: null, executorProviderId: "codex", upstreamProviderId: "openai" };
    renderWithProviders(editor(vi.fn(), native, { ...binding, executorId: "native", modelId: "manual-native-model" }));
    expect(screen.getByTestId("catalog-unsupported-auth")).toHaveTextContent(/不支持提供方模型目录/);
    expect(screen.getByLabelText("Model ID")).toHaveValue("manual-native-model");
  });

  it("keeps a manual binding unchanged after a catalog CAS conflict and requires explicit refresh", async () => {
    const user = userEvent.setup();
    const fetchModels = vi.fn(async () => catalog());
    const select = vi.fn(async (_input: CatalogBindingInput): Promise<CatalogBindingResult> => { throw new Error("stale_catalog"); });
    renderWithProviders(editor(fetchModels, connection, binding, select));
    await user.click(screen.getByTestId("fetch-models-button"));
    await user.selectOptions(await screen.findByLabelText("提供方公布的模型"), "anthropic/claude-test");
    await user.selectOptions(screen.getByLabelText("目录绑定执行器"), "opencode");
    await user.click(screen.getByRole("button", { name: "使用目录模型创建或复用绑定" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/原手动绑定保持不变/);
    expect(select).toHaveBeenCalledTimes(1);
    expect(fetchModels).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText("Model ID")).toHaveValue(binding.modelId);
    expect(screen.queryByLabelText("提供方公布的模型")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "刷新模型目录" })).toBeEnabled();
  });

  it("discards a recommendation response when the connection public configuration changes", async () => {
    const user = userEvent.setup();
    const client = getDefaultModelControlClient();
    const oldPreview = await client.recommendModelSelection({ selectionMode: "manual", manualBindingRef: "coding-binding" });
    const response = deferred<typeof oldPreview>();
    const recommend = vi.spyOn(client, "recommendModelSelection").mockReturnValue(response.promise);
    const queryClient = makeQueryClient();
    render(<QueryClientProvider client={queryClient}><MemoryRouter><SettingsPage /></MemoryRouter></QueryClientProvider>);
    await screen.findByTestId("binding-item-coding-binding");
    await user.click(screen.getByTestId("binding-item-coding-binding"));
    await user.click(screen.getByRole("button", { name: "保存绑定" }));
    await waitFor(() => expect(recommend).toHaveBeenCalledTimes(1));
    const savedConnections = await client.listConnections();
    await act(async () => {
      queryClient.setQueryData(CONNECTIONS_QUERY_KEY,
        savedConnections.map((item) => ({ ...item, baseUrl: "https://changed.example.test/v1" })));
    });
    await act(async () => response.resolve(oldPreview));
    expect(screen.queryByTestId("model-selection-preview")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Model ID")).toHaveValue("coding-default");
  });
});
