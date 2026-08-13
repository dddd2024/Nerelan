import { useEffect, useMemo, useState } from "react";
import { Plus, Settings } from "lucide-react";
import { ConnectionBindingEditor } from "@/components/connection-binding-editor";
import {
  useBindings,
  useConnections,
  useDeleteBinding,
  useDeleteConnection,
  useExecutors,
  useTestConnection,
  useUpsertBinding,
  useUpsertConnection,
} from "@/hooks/use-model-access";
import type {
  Binding,
  Connection,
  ConnectionInput,
  ConnectionProbeResult,
} from "@/schemas/model-access";
import type { BindingInput } from "@/schemas/model-access";
import { cn } from "@/lib/cn";

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

  const testConnectionMutation = useTestConnection();

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
  }

  async function handleConnectionSave(input: ConnectionInput) {
    clearMessages();
    try {
      const saved = await connectionsMutation.mutateAsync(input);
      setCreating(false);
      setSelectedConnId(saved.connectionId);
      setStatus("连接已保存");
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  async function handleConnectionTest(connectionId: string) {
    clearMessages();
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

  const editorBusy = busy;

  return (
    <div
      data-testid="settings-page"
      className={cn(
        "h-full overflow-auto bg-transparent px-4 py-4 custom-scrollbar",
        "lg:px-[42px] lg:py-[42px]",
      )}
    >
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-5">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-ra-text-tertiary" />
              <h1 className="text-lg font-semibold text-ra-text-secondary">
                连接与绑定
              </h1>
            </div>
            <p className="mt-2 max-w-2xl text-sm text-ra-text-tertiary">
              管理 Model Control 连接与 OpenCode 绑定。API Key 仅通过模型控制服务传输，
              不写入浏览器存储。
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => switchView("connection")}
              className={cn(
                "inline-flex items-center justify-center gap-2 rounded-md",
                "px-3 py-2 text-sm font-medium",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-white",
                view === "connection"
                  ? "bg-ra-accent text-ra-base"
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
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-white",
                view === "binding"
                  ? "bg-ra-accent text-ra-base"
                  : "border border-ra-border text-ra-text-secondary hover:bg-ra-tertiary",
              )}
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              新建绑定
            </button>
          </div>
        </header>

        <div className="rounded-lg border border-ra-border bg-ra-secondary px-4 py-3 text-xs text-ra-text-tertiary">
          浏览器不会把 API Key 写入 localStorage、sessionStorage 或任务数据。
          绑定只保存执行器、连接和 Model ID 引用，不包含凭据。
        </div>

        {status && (
          <p role="status" className="text-sm text-green-300">
            {status}
          </p>
        )}
        {error && (
          <p role="alert" className="text-sm text-red-300">
            {error}
          </p>
        )}

        <div className="grid min-h-0 grid-cols-1 gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="flex flex-col gap-2 rounded-xl border border-ra-border bg-ra-secondary p-3">
            <h2 className="px-1 text-xs font-semibold uppercase tracking-wide text-ra-text-tertiary">
              连接
            </h2>
            {(connectionsQuery.isLoading || executorsQuery.isLoading) && (
              <p className="px-1 py-3 text-sm text-ra-text-tertiary">正在加载…</p>
            )}
            {connections.length === 0 && !connectionsQuery.isLoading ? (
              <p className="px-1 py-3 text-sm text-ra-text-tertiary">
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
                    "flex w-full flex-col gap-1 rounded-lg border px-3 py-2 text-left",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    view === "connection" && !creating && selectedConnId === conn.connectionId
                      ? "border-ra-accent bg-ra-tertiary"
                      : "border-transparent hover:border-ra-border hover:bg-ra-tertiary",
                  )}
                >
                  <span className="flex w-full items-center gap-2">
                    <span className="truncate text-sm font-medium text-ra-text">
                      {conn.name}
                    </span>
                    <span className="ml-auto rounded-full bg-ra-accent/15 px-2 py-0.5 text-[10px] text-ra-accent">
                      {conn.enabled ? "启用" : "禁用"}
                    </span>
                  </span>
                  <span className="truncate text-xs text-ra-text-tertiary">
                    {conn.provider} · {conn.authMethod}
                  </span>
                  <span className="text-[10px] text-ra-text-tertiary">
                    密钥：{secretStatusLabel(conn.secretStatus)}
                  </span>
                </button>
              ))
            )}

            <h2 className="mt-3 px-1 text-xs font-semibold uppercase tracking-wide text-ra-text-tertiary">
              绑定
            </h2>
            {bindings.length === 0 && !bindingsQuery.isLoading ? (
              <p className="px-1 py-3 text-sm text-ra-text-tertiary">
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
                    "flex w-full flex-col gap-1 rounded-lg border px-3 py-2 text-left",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    view === "binding" && !creating && selectedBindId === bind.bindingId
                      ? "border-ra-accent bg-ra-tertiary"
                      : "border-transparent hover:border-ra-border hover:bg-ra-tertiary",
                  )}
                >
                  <span className="flex w-full items-center gap-2">
                    <span className="truncate text-sm font-medium text-ra-text">
                      {bind.name}
                    </span>
                    <span className="ml-auto rounded-full bg-ra-accent/15 px-2 py-0.5 text-[10px] text-ra-accent">
                      {bind.enabled ? "启用" : "禁用"}
                    </span>
                  </span>
                  <span className="truncate text-xs text-ra-text-tertiary">
                    {bind.executorId} · {bind.modelId}
                  </span>
                  <span className="text-[10px] text-ra-text-tertiary">
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
            connectionProbeResult={connProbeResult}
            connectionProbePending={testConnectionMutation.isPending}
          />
        </div>
      </div>
    </div>
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
    case "missing":
      return "未配置";
    case "not_applicable":
      return "不适用";
  }
}
