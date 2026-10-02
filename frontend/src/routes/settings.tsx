import { useEffect, useMemo, useRef, useState } from "react";
import { Plus, Settings } from "lucide-react";
import { ConnectionBindingEditor, executorManagedAuth, externalSessionStatusLabel } from "@/components/connection-binding-editor";
import {
  useBindings,
  useConnections,
  useDeleteBinding,
  useDeleteConnection,
  useExecutors,
  useTestConnection,
  useListConnectionModels,
  useUpsertBinding,
  useUpsertConnection,
  useSelectCatalogBinding,
  useRecommendModelSelection,
} from "@/hooks/use-model-access";
import type {
  AccountAuthStatus,
  Binding,
  Connection,
  ConnectionInput,
  ConnectionProbeResult,
  CatalogBindingInput,
  CatalogBindingResult,
  ModelSelectionResult,
} from "@/schemas/model-access";
import type { BindingInput } from "@/schemas/model-access";
import { cn } from "@/lib/cn";
import { connectionConfigurationFingerprint, getDefaultModelControlClient } from "@/lib/model-control-client";
import { ThemeSelector } from "@/components/theme-selector";

type EditorView = "connection" | "binding";

export function SettingsPage() {
  const connectionsQuery = useConnections();
  const connectionsMutation = useUpsertConnection();
  const deleteConnMutation = useDeleteConnection();
  const executorsQuery = useExecutors();
  const bindingsQuery = useBindings();
  const bindingsMutation = useUpsertBinding();
  const deleteBindingMutation = useDeleteBinding();

  const connections = useMemo(
    () => connectionsQuery.data ?? [],
    [connectionsQuery.data],
  );
  const executors = useMemo(
    () => executorsQuery.data ?? [],
    [executorsQuery.data],
  );
  const bindings = useMemo(
    () => bindingsQuery.data ?? [],
    [bindingsQuery.data],
  );

  const [view, setView] = useState<EditorView>("connection");
  const [selectedConnId, setSelectedConnId] = useState<string | null>(null);
  const [selectedBindId, setSelectedBindId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connProbeResult, setConnProbeResult] = useState<ConnectionProbeResult | null>(null);
  const [accountAuthState, setAccountAuthState] = useState<AccountAuthStatus | null>(null);
  const [accountAuthPending, setAccountAuthPending] = useState(false);

  const testConnectionMutation = useTestConnection();
  const listConnectionModelsMutation = useListConnectionModels();
  const catalogBindingMutation = useSelectCatalogBinding();
  const selectionPreviewMutation = useRecommendModelSelection();
  const [selectionPreview, setSelectionPreview] = useState<{ result: ModelSelectionResult; configurationStamp: string } | null>(null);
  const [selectionPreviewError, setSelectionPreviewError] = useState<string | null>(null);
  const operationEpoch = useRef(0);
  const configurationStamp = JSON.stringify(connections.map(connectionConfigurationFingerprint).sort());
  const configurationStampRef = useRef(configurationStamp);
  configurationStampRef.current = configurationStamp;
  const visibleSelectionPreview = selectionPreview?.configurationStamp === configurationStamp ? selectionPreview.result : null;

  useEffect(() => {
    if (creating) return;
    if (view === "connection") {
      if (selectedConnId && connections.some((c) => c.connectionId === selectedConnId)) return;
      setSelectedConnId(
        connections.find((c) => c.enabled)?.connectionId ?? connections[0]?.connectionId ?? null,
      );
    } else {
      if (selectedBindId && bindings.some((b) => b.bindingId === selectedBindId)) return;
      setSelectedBindId(
        bindings.find((b) => b.enabled)?.bindingId ?? bindings[0]?.bindingId ?? null,
      );
    }
  }, [view, creating, connections, bindings, selectedConnId, selectedBindId]);

  const selectedConnection = useMemo<Connection | null>(
    () => connections.find((c) => c.connectionId === selectedConnId) ?? null,
    [connections, selectedConnId],
  );

  const selectedBinding = useMemo<Binding | null>(
    () => bindings.find((b) => b.bindingId === selectedBindId) ?? null,
    [bindings, selectedBindId],
  );

  const busy =
    connectionsMutation.isPending ||
    deleteConnMutation.isPending ||
    bindingsMutation.isPending ||
    deleteBindingMutation.isPending ||
    testConnectionMutation.isPending || catalogBindingMutation.isPending;

  function clearMessages() {
    operationEpoch.current += 1;
    setStatus(null);
    setError(null);
    setConnProbeResult(null);
    setAccountAuthState(null);
    setSelectionPreview(null);
    setSelectionPreviewError(null);
  }

  /* The three list reads share one failure surface so the page states the
     problem once instead of scattering three separate alerts. */
  const failedReads = [
    connectionsQuery.isError ? "连接" : null,
    executorsQuery.isError ? "执行器" : null,
    bindingsQuery.isError ? "绑定" : null,
  ].filter((value): value is string => value !== null);
  const loadFailureCount = failedReads.length;
  const loadFailureMessage = `无法读取${failedReads.join("、")}；下面显示的不是真实数据。`;

  function retryFailedLoads() {
    if (connectionsQuery.isError) void connectionsQuery.refetch();
    if (executorsQuery.isError) void executorsQuery.refetch();
    if (bindingsQuery.isError) void bindingsQuery.refetch();
  }

  async function handleConnectionSave(input: ConnectionInput) {
    clearMessages();
    const epoch = operationEpoch.current;
    try {
      const saved = await connectionsMutation.mutateAsync(input);
      if (epoch !== operationEpoch.current) return;
      setCreating(false);
      setSelectedConnId(saved.connectionId);
      setConnProbeResult(null);
      setStatus("连接已保存");
    } catch (cause) {
      if (epoch === operationEpoch.current) setError(errorMessage(cause));
      throw cause;
    }
  }

  async function handleConnectionTest(connectionId: string) {
    setStatus(null);
    setError(null);
    setConnProbeResult(null);
    try {
      const result = await testConnectionMutation.mutateAsync(connectionId);
      setConnProbeResult(result);
      if (result.ok) {
        setStatus("连接验证成功");
      }
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  async function handleConnectionModelsFetch(connectionId: string) {
    return listConnectionModelsMutation.mutateAsync(connectionId);
  }

  async function handleAccountAuthStart(connectionId: string) {
    setError(null);
    setStatus(null);
    setAccountAuthState(null);
    setAccountAuthPending(true);
    try {
      const result = await getDefaultModelControlClient().startAccountAuth(connectionId);
      setAccountAuthState(result);
      if (result.authorizationUrl) {
        window.open(result.authorizationUrl, "_blank", "noopener,noreferrer");
      }
    } catch (cause) {
      await reconcileAccountAuthFailure(connectionId, cause);
    } finally {
      setAccountAuthPending(false);
    }
  }

  async function handleAccountAuthComplete(connectionId: string, code?: string) {
    setError(null);
    setStatus(null);
    setAccountAuthPending(true);
    try {
      const result = await getDefaultModelControlClient().completeAccountAuth(
        connectionId,
        code,
      );
      setAccountAuthState(result);
      await connectionsQuery.refetch();
      setStatus(
        result.status === "authenticated"
          ? "OpenAI / ChatGPT（GPT）账号已登录"
          : "授权已完成，正在等待 OpenCode 会话复核",
      );
    } catch (cause) {
      await reconcileAccountAuthFailure(connectionId, cause);
      throw cause;
    } finally {
      setAccountAuthPending(false);
    }
  }

  async function reconcileAccountAuthFailure(connectionId: string, cause: unknown) {
    // Discard stale authorization links even if the status request also fails.
    setAccountAuthState(null);
    try {
      const latest = await getDefaultModelControlClient().getAccountAuthStatus(connectionId);
      setAccountAuthState(latest);
      setError(
        latest.status === "failed"
          ? "账号登录未完成。请检查服务端网络配置，然后重新点击浏览器登录。"
          : errorMessage(cause),
      );
    } catch {
      setError("暂时无法确认登录状态，请稍后重试。浏览器授权成功不代表账号连接已完成。");
    }
    await connectionsQuery.refetch();
  }

  async function handleAccountAuthCancel(connectionId: string) {
    setError(null);
    setAccountAuthPending(true);
    try {
      setAccountAuthState(
        await getDefaultModelControlClient().cancelAccountAuth(connectionId),
      );
    } catch (cause) {
      setError(errorMessage(cause));
      throw cause;
    } finally {
      setAccountAuthPending(false);
    }
  }

  async function handleAccountAuthLogout(connectionId: string) {
    setError(null);
    setAccountAuthPending(true);
    try {
      setAccountAuthState(
        await getDefaultModelControlClient().logoutAccountAuth(connectionId),
      );
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setAccountAuthPending(false);
    }
  }

  async function handleBindingSave(input: BindingInput) {
    clearMessages();
    const epoch = operationEpoch.current;
    try {
      const saved = await bindingsMutation.mutateAsync(input);
      if (epoch !== operationEpoch.current) return;
      setCreating(false);
      setSelectedBindId(saved.bindingId);
      setStatus("绑定已保存");
      await loadSelectionPreview(saved.bindingId, epoch);
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  async function loadSelectionPreview(bindingId: string, epoch: number) {
    const stamp = configurationStampRef.current;
    try {
      const result = await selectionPreviewMutation.mutateAsync({ selectionMode: "manual",
        manualBindingRef: bindingId, purpose: "development",
        requiredCapabilities: ["workspace_execution"], orchestrationMode: "single" });
      if (epoch === operationEpoch.current && stamp === configurationStampRef.current) setSelectionPreview({ result, configurationStamp: stamp });
    } catch {
      if (epoch === operationEpoch.current && stamp === configurationStampRef.current) setSelectionPreviewError("兼容性预览暂时不可用；绑定已保留，执行检查尚未完成。");
    }
  }

  async function handleCatalogBindingSelect(input: CatalogBindingInput): Promise<CatalogBindingResult> {
    clearMessages();
    const epoch = operationEpoch.current;
    const result = await catalogBindingMutation.mutateAsync(input);
    if (epoch !== operationEpoch.current) return result;
    setCreating(false);
    setView("binding");
    setSelectedBindId(result.binding.bindingId);
    setStatus(result.reusedManual
      ? result.binding.enabled ? "已复用现有手动绑定，原配置保持不变。" : "已保留现有手动绑定（禁用），不会隐式启用。"
      : "目录绑定已保存（提供方公布，尚未验证执行可用性）。");
    await loadSelectionPreview(result.binding.bindingId, epoch);
    return result;
  }

  async function handleConnectionDelete(connectionId: string) {
    clearMessages();
    try {
      await deleteConnMutation.mutateAsync(connectionId);
      setCreating(false);
      setSelectedConnId(null);
      setStatus("连接已删除");
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  async function handleBindingDelete(bindingId: string) {
    clearMessages();
    try {
      await deleteBindingMutation.mutateAsync(bindingId);
      setCreating(false);
      setSelectedBindId(null);
      setStatus("绑定已删除");
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  function switchView(next: EditorView) {
    clearMessages();
    setView(next);
    setCreating(true);
    setSelectedConnId(null);
    setSelectedBindId(null);
  }

  const editorBusy = busy || accountAuthPending;

  return (
    <main
      data-testid="settings-page"
      className={cn(
        "h-full overflow-auto bg-ra-workspace px-4 py-4 custom-scrollbar",
        "lg:px-7 lg:py-7",
      )}
    >
      {/*
       * Settings keeps its own compact header on purpose: this surface has its
       * own density contract (see the Settings density test), so it does not
       * adopt the larger shared page-title scale. What it did need fixing was
       * the missing `<main>` landmark, the `bg-transparent` surface that broke
       * the workspace token, and a page title rendered in *secondary* colour
       * as if it were de-emphasised metadata.
       */}
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-ra-text-tertiary" />
              <h1 className="text-lg font-medium text-ra-text">
                连接与绑定
              </h1>
            </div>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-ra-text-secondary">
              {executors.some((executor) => executor.executorId === "codex")
                ? "管理 Model Control 连接与 OpenCode / Codex 绑定。"
                : "管理 Model Control 连接与 OpenCode 绑定。"}API Key 仅通过模型控制服务传输，
              不写入浏览器存储。
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2">
            <button
              type="button"
              onClick={() => switchView("connection")}
              className={cn(
                "inline-flex items-center justify-center gap-2 rounded-md",
                "px-3 py-2 text-sm font-medium",
                view === "connection"
                  ? "bg-ra-accent text-ra-base hover:bg-ra-accent-hover"
                  : "border border-ra-border text-ra-text-secondary hover:bg-ra-tertiary",
              )}
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              新建连接
            </button>
            <button
              type="button"
              onClick={() => switchView("binding")}
              className={cn(
                "inline-flex items-center justify-center gap-2 rounded-md",
                "px-3 py-2 text-sm font-medium",
                view === "binding"
                  ? "bg-ra-accent text-ra-base hover:bg-ra-accent-hover"
                  : "border border-ra-border text-ra-text-secondary hover:bg-ra-tertiary",
              )}
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              新建绑定
            </button>
          </div>
        </header>

        <p
          data-testid="settings-credential-note"
          className="max-w-3xl text-xs leading-5 text-ra-text-tertiary"
        >
          浏览器不会把 API Key 写入 localStorage、sessionStorage 或任务数据。
          绑定只保存执行器、连接和 Model ID 引用，不包含凭据。
        </p>

        {status && (
          <p role="status" className="text-sm text-ra-status-running">
            {status}
          </p>
        )}
        {error && (
          <p role="alert" className="text-sm text-ra-status-error">
            {error}
          </p>
        )}

        {visibleSelectionPreview ? (
          <section data-testid="model-selection-preview" className="rounded-md border border-ra-border bg-ra-base/30 px-3 py-2 text-sm text-ra-text-secondary">
            <h2 className="font-medium">兼容性预览 · 等待执行检查</h2>
            <p className="mt-1">{visibleSelectionPreview.message}</p>
            {visibleSelectionPreview.recommended ? <p className="mt-1">建议：{visibleSelectionPreview.recommended.modelId || "模型标识不可展示"} · {visibleSelectionPreview.recommended.executorId}。{visibleSelectionPreview.recommended.explanation}</p> : null}
            {visibleSelectionPreview.candidates.map((candidate) => <p key={candidate.bindingRef} className="mt-1">{candidate.modelId || "模型标识不可展示"} · {candidate.executorId}：{candidate.explanation}</p>)}
            <p className="mt-2 text-xs text-ra-text-tertiary">费用、质量、任务成功和底层模型身份尚未观测。预览不会启动任务、切换默认绑定或授予 GPT 调用权限。</p>
          </section>
        ) : null}
        {selectionPreviewError ? <p role="status" className="text-sm text-ra-text-tertiary">{selectionPreviewError}</p> : null}

        {/* A failed read must never be rendered as an empty collection: the
            page previously fell straight through to "还没有连接。/ 还没有绑定。",
            which asserts "you have none" when the truth may be "the request
            failed". Failures are stated once, here, with an explicit retry, and
            the two lists below repeat the reason in place of their empty text. */}
        {loadFailureCount > 0 && (
          <div
            data-testid="settings-load-error"
            role="alert"
            className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-md border border-ra-status-error/40 bg-ra-status-error/5 px-3 py-2 text-sm text-ra-status-error"
          >
            <span>{loadFailureMessage}</span>
            <button
              type="button"
              data-testid="settings-load-retry"
              onClick={retryFailedLoads}
              className="inline-flex min-h-6 items-center rounded px-1.5 text-xs font-medium underline underline-offset-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
            >
              重试
            </button>
          </div>
        )}

        <ThemeSelector />

        <div
          data-testid="settings-model-access-layout"
          className="grid min-h-0 grid-cols-1 items-start gap-5 lg:grid-cols-[224px_minmax(0,1fr)]"
        >
          <aside
            data-testid="settings-model-access-index"
            className="flex min-w-0 flex-col gap-1 self-start lg:pr-2"
          >
            <h2 className="px-2 text-xs font-semibold text-ra-text-tertiary">
              连接
            </h2>
            {(connectionsQuery.isLoading || executorsQuery.isLoading) && (
              <p className="px-2 py-2 text-sm text-ra-text-tertiary">正在加载…</p>
            )}
            {connectionsQuery.isError ? (
              <p
                data-testid="settings-connections-error"
                role="alert"
                className="px-2 py-2 text-sm text-ra-status-error"
              >
                无法读取连接：{errorMessage(connectionsQuery.error)}
              </p>
            ) : connections.length === 0 && !connectionsQuery.isLoading ? (
              <p className="px-2 py-2 text-sm text-ra-text-tertiary">
                还没有连接。
              </p>
            ) : (
              connections.map((conn) => (
                <button
                  key={conn.connectionId}
                  type="button"
                  data-testid={`connection-item-${conn.connectionId}`}
                  onClick={() => {
                    clearMessages();
                    setView("connection");
                    setCreating(false);
                    setSelectedConnId(conn.connectionId);
                  }}
                  className={cn(
                    "flex w-full flex-col gap-0.5 rounded-md px-2 py-1.5 text-left transition-colors",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    view === "connection" && !creating && selectedConnId === conn.connectionId
                      ? "bg-ra-tertiary"
                      : "hover:bg-ra-tertiary/70",
                  )}
                >
                  <span className="flex w-full items-center gap-2">
                    <span className="truncate text-sm font-medium text-ra-text">
                      {conn.name}
                    </span>
                    <span className="ml-auto shrink-0 text-[11px] font-medium text-ra-accent">
                      {conn.enabled ? "启用" : "禁用"}
                    </span>
                  </span>
                  <span className="truncate text-xs text-ra-text-tertiary">
                    {conn.provider} · {conn.authMethod}
                  </span>
                  <span className="text-[11px] text-ra-text-tertiary">
                    密钥：{secretStatusLabel(conn.secretStatus)}
                  </span>
                  {executorManagedAuth(conn.authMethod) && (
                    <span
                      className="text-[11px] text-ra-text-tertiary"
                      data-testid={`connection-list-external-session-${conn.connectionId}`}
                    >
                      外部会话：{externalSessionStatusLabel(conn.externalSessionStatus)}
                    </span>
                  )}
                </button>
              ))
            )}

            <h2 className="mt-3 px-2 text-xs font-semibold text-ra-text-tertiary">
              绑定
            </h2>
            {bindingsQuery.isError ? (
              <p
                data-testid="settings-bindings-error"
                role="alert"
                className="px-2 py-2 text-sm text-ra-status-error"
              >
                无法读取绑定：{errorMessage(bindingsQuery.error)}
              </p>
            ) : bindings.length === 0 && !bindingsQuery.isLoading ? (
              <p className="px-2 py-2 text-sm text-ra-text-tertiary">
                还没有绑定。
              </p>
            ) : (
              bindings.map((bind) => (
                <button
                  key={bind.bindingId}
                  type="button"
                  data-testid={`binding-item-${bind.bindingId}`}
                  onClick={() => {
                    clearMessages();
                    setView("binding");
                    setCreating(false);
                    setSelectedBindId(bind.bindingId);
                  }}
                  className={cn(
                    "flex w-full flex-col gap-0.5 rounded-md px-2 py-1.5 text-left transition-colors",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    view === "binding" && !creating && selectedBindId === bind.bindingId
                      ? "bg-ra-tertiary"
                      : "hover:bg-ra-tertiary/70",
                  )}
                >
                  <span className="flex w-full items-center gap-2">
                    <span className="truncate text-sm font-medium text-ra-text">
                      {bind.name}
                    </span>
                    <span className="ml-auto shrink-0 text-[11px] font-medium text-ra-accent">
                      {bind.enabled ? "启用" : "禁用"}
                    </span>
                  </span>
                  <span className="truncate text-xs text-ra-text-tertiary">
                    {bind.executorId} · {bind.modelId}
                  </span>
                  <span className="text-[11px] text-ra-text-tertiary">
                    连接：{bind.connectionId}
                  </span>
                </button>
              ))
            )}
          </aside>

          <ConnectionBindingEditor
            view={view}
            connection={selectedConnection}
            binding={selectedBinding}
            creating={creating}
            connections={connections}
            executors={executors}
            busy={editorBusy}
            onConnectionSave={handleConnectionSave}
            onBindingSave={handleBindingSave}
            onConnectionDelete={handleConnectionDelete}
            onBindingDelete={handleBindingDelete}
            onConnectionTest={handleConnectionTest}
            onConnectionModelsFetch={handleConnectionModelsFetch}
            onCatalogBindingSelect={handleCatalogBindingSelect}
            connectionProbeResult={connProbeResult}
            connectionProbePending={testConnectionMutation.isPending}
            connectionModelsPending={listConnectionModelsMutation.isPending}
            accountAuthState={accountAuthState}
            accountAuthPending={accountAuthPending}
            onAccountAuthStart={handleAccountAuthStart}
            onAccountAuthComplete={handleAccountAuthComplete}
            onAccountAuthCancel={handleAccountAuthCancel}
            onAccountAuthLogout={handleAccountAuthLogout}
          />
        </div>
      </div>
    </main>
  );
}

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : "操作失败";
}

function secretStatusLabel(status: Connection["secretStatus"]): string {
  switch (status) {
    case "environment":
      return "环境变量";
    case "session":
      return "进程会话";
    case "stored":
      return "系统凭据库";
    case "store_locked":
      return "凭据库锁定";
    case "replacement_required":
      return "需重新输入";
    case "missing":
      return "未配置";
    case "not_applicable":
      return "不适用";
  }
}
