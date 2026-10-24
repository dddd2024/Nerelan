import { MagpieSettingsEditor } from "@/components/magpie-settings";
import { useEffect, useMemo, useState } from "react";
import { Plus, Settings } from "lucide-react";
import { Link } from "react-router";
import { ConnectionBindingEditor, executorManagedAuth, externalSessionStatusLabel } from "@/components/connection-binding-editor";
import {
  useBindings,
  useConnections,
  useDeleteBinding,
  useDeleteConnection,
  useExecutors,
  useTestConnection,
  useBindConnectionModels,
  useListConnectionModels,
  useUpsertBinding,
  useUpsertConnection,
} from "@/hooks/use-model-access";
import type {
  AccountAuthStatus,
  Binding,
  Connection,
  ConnectionInput,
  ConnectionProbeResult,
} from "@/schemas/model-access";
import type { BindingInput } from "@/schemas/model-access";
import { cn } from "@/lib/cn";
import { getDefaultModelControlClient } from "@/lib/model-control-client";
import { ThemeSelector } from "@/components/theme-selector";
import { AgentTeamEditor } from "@/components/agent-team-editor";
import { ResourceOverview } from "@/components/resource-overview";
import { SettingsMigrationStatus } from "@/components/settings-migration-status";

type EditorView = "connection" | "binding";

/* "all" is the legacy single page kept for direct embedding and its tests.
   The routed subpages narrow it: resources own connections and accounts,
   models own bindings, and advanced keeps the combined raw editor reachable
   while the Magpie route migration is incomplete. */
export type SettingsSection = "all" | "resources" | "models" | "advanced";

const SECTION_HEADINGS: Record<SettingsSection, string> = {
  all: "连接与绑定",
  resources: "AI 资源与账号",
  models: "模型与路由",
  advanced: "高级配置",
};

export function SettingsPage({ section = "all" }: { section?: SettingsSection }) {
  const lockedView: EditorView | null =
    section === "resources" ? "connection" : section === "models" ? "binding" : null;
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

  const [view, setView] = useState<EditorView>(lockedView ?? "connection");
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
  const bindConnectionModelsMutation = useBindConnectionModels();

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
    testConnectionMutation.isPending;

  function clearMessages() {
    setStatus(null);
    setError(null);
    setConnProbeResult(null);
    setAccountAuthState(null);
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
    setStatus(null);
    setError(null);
    try {
      const saved = await connectionsMutation.mutateAsync(input);
      setCreating(false);
      setSelectedConnId(saved.connectionId);
      setConnProbeResult(null);
      setStatus("连接已保存");
    } catch (cause) {
      setError(errorMessage(cause));
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

  async function handleBindAllModels(connectionId: string, modelIds: string[], executorId: string) {
    return bindConnectionModelsMutation.mutateAsync({ connectionId, modelIds, executorId });
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
    try {
      const saved = await bindingsMutation.mutateAsync(input);
      setCreating(false);
      setSelectedBindId(saved.bindingId);
      setStatus("绑定已保存");
    } catch (cause) {
      setError(errorMessage(cause));
    }
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
        {section !== "all" ? (
          <Link to="/settings" className="self-start text-sm text-ra-text-tertiary hover:text-ra-text hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
            ← 返回设置
          </Link>
        ) : null}
        <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-ra-text-tertiary" />
              <h1 className="text-lg font-medium text-ra-text">
                {SECTION_HEADINGS[section]}
              </h1>
            </div>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-ra-text-secondary">
              {executors.some((executor) => executor.executorId === "codex" || executor.executorId === "claude_code")
                ? "管理 Model Control 连接与 OpenCode / Codex / Claude Code 绑定；ChatGPT 与 Claude 账号由各自 CLI 持久登录。"
                : "管理 Model Control 连接与 OpenCode 绑定。"}API Key 仅通过模型控制服务传输，
              不写入浏览器存储。
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2">
            {lockedView !== "binding" ? <button
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
            </button> : null}
            {lockedView !== "connection" ? <button
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
            </button> : null}
          </div>
        </header>

        <p
          data-testid="settings-credential-note"
          className="max-w-3xl text-xs leading-5 text-ra-text-tertiary"
        >
          浏览器不会把 API Key 写入 localStorage、sessionStorage 或任务数据。
          绑定只保存执行器、连接和 Model ID 引用，不包含凭据。
        </p>

        <SectionNote section={section} />

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

        {section === "all" ? <ThemeSelector /> : null}

        <div
          data-testid="settings-model-access-layout"
          className="grid min-h-0 grid-cols-1 items-start gap-5 lg:grid-cols-[224px_minmax(0,1fr)]"
        >
          <aside
            data-testid="settings-model-access-index"
            className="flex min-w-0 flex-col gap-1 self-start lg:pr-2"
          >
            {lockedView !== "binding" ? <>
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

            </> : null}

            {lockedView !== "connection" ? <>
            <h2 className={cn("px-2 text-xs font-semibold text-ra-text-tertiary", lockedView === null && "mt-3")}>
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
            </> : null}
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
            onBindAllModels={handleBindAllModels}
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
        {section === "resources" || section === "advanced" ? (
          <SettingsMigrationStatus connections={connections} connectionsFailed={connectionsQuery.isError} />
        ) : null}
        {section === "all" || section === "resources" ? <MagpieSettingsEditor /> : null}
        {section === "all" ? <ResourceOverview /> : null}
        {section === "all" ? <AgentTeamEditor bindings={bindings} /> : null}
      </div>
    </main>
  );
}

const NOTE_LINK = "text-ra-accent underline underline-offset-2 hover:text-ra-accent-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent";

function SectionNote({ section }: { section: SettingsSection }) {
  if (section === "resources") {
    return (
      <p data-testid="settings-section-note" className="max-w-3xl text-sm leading-6 text-ra-text-secondary">
        这里管理本地连接、账号会话和 Magpie。模型绑定在
        <Link to="/settings/models" className={NOTE_LINK}>模型与路由</Link>
        中管理。
      </p>
    );
  }
  if (section === "models") {
    return (
      <p data-testid="settings-section-note" className="max-w-3xl text-sm leading-6 text-ra-text-secondary">
        绑定把执行器映射到某个连接上的 Model ID，是派发时的配置候选；任务实际使用的模型以运行记录为准，不从这里推断。
        连接和账号登录在<Link to="/settings/resources" className={NOTE_LINK}>AI 资源与账号</Link>中管理。
      </p>
    );
  }
  if (section === "advanced") {
    return (
      <p data-testid="settings-section-note" className="max-w-3xl text-sm leading-6 text-ra-text-secondary">
        旧版连接与绑定的合并编辑器。Magpie 路由迁移完成前，任务仍按这里的本地连接和绑定派发；
        打开此页不会删除凭据、移除绑定或停用本地账号；只有点击对应的删除或保存按钮才会修改。
      </p>
    );
  }
  return null;
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
