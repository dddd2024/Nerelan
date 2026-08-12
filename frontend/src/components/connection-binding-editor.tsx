import { useEffect, useState, type FormEvent } from "react";
import { Save, Trash2 } from "lucide-react";
import {
  ConnectionInputSchema,
  BindingInputSchema,
  type AuthMethod,
  type Binding,
  type BindingInput,
  type Connection,
  type ConnectionInput,
  type ConnectionProvider,
} from "@/schemas/model-access";
import type { Executor } from "@/schemas/model-access";
import { cn } from "@/lib/cn";

type EditorView = "connection" | "binding";

interface ConnectionBindingEditorProps {
  view: EditorView;
  connection: Connection | null;
  binding: Binding | null;
  creating: boolean;
  connections: Connection[];
  executors: Executor[];
  busy: boolean;
  onConnectionSave: (input: ConnectionInput) => Promise<void>;
  onBindingSave: (input: BindingInput) => Promise<void>;
  onConnectionDelete: (connectionId: string) => Promise<void>;
  onBindingDelete: (bindingId: string) => Promise<void>;
}

const EMPTY_CONNECTION: ConnectionInput = {
  connectionId: "",
  name: "",
  provider: "litellm-proxy",
  baseUrl: "http://localhost:4000/v1",
  authMethod: "api_key",
  enabled: true,
};

const EMPTY_BINDING: BindingInput = {
  bindingId: "",
  name: "",
  executorId: "",
  connectionId: "",
  modelId: "",
  enabled: true,
};

export function ConnectionBindingEditor({
  view,
  connection,
  binding,
  creating,
  connections,
  executors,
  busy,
  onConnectionSave,
  onBindingSave,
  onConnectionDelete,
  onBindingDelete,
}: ConnectionBindingEditorProps) {
  const [connDraft, setConnDraft] = useState<ConnectionInput>(EMPTY_CONNECTION);
  const [connApiKey, setConnApiKey] = useState("");
  const [connError, setConnError] = useState<string | null>(null);
  const [bindDraft, setBindDraft] = useState<BindingInput>(EMPTY_BINDING);
  const [bindError, setBindError] = useState<string | null>(null);

  useEffect(() => {
    if (view === "connection") {
      setConnDraft(
        connection
          ? {
              connectionId: connection.connectionId,
              name: connection.name,
              provider: connection.provider,
              baseUrl: connection.baseUrl,
              authMethod: connection.authMethod,
              enabled: connection.enabled,
            }
          : EMPTY_CONNECTION,
      );
      setConnApiKey("");
      setConnError(null);
    } else {
      setBindDraft(
        binding
          ? {
              bindingId: binding.bindingId,
              name: binding.name,
              executorId: binding.executorId,
              connectionId: binding.connectionId,
              modelId: binding.modelId,
              enabled: binding.enabled,
            }
          : EMPTY_BINDING,
      );
      setBindError(null);
    }
  }, [view, connection, binding, creating]);

  async function handleConnectionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = ConnectionInputSchema.safeParse({
      ...connDraft,
      ...(connApiKey ? { apiKey: connApiKey } : {}),
    });
    if (!parsed.success) {
      setConnError(parsed.error.issues[0]?.message ?? "连接配置无效");
      return;
    }
    setConnError(null);
    await onConnectionSave(parsed.data);
    setConnApiKey("");
  }

  async function handleBindingSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = BindingInputSchema.safeParse(bindDraft);
    if (!parsed.success) {
      setBindError(parsed.error.issues[0]?.message ?? "绑定配置无效");
      return;
    }
    setBindError(null);
    await onBindingSave(parsed.data);
  }

  const connSavedId = creating && view === "connection" ? null : connection?.connectionId ?? null;
  const bindSavedId = creating && view === "binding" ? null : binding?.bindingId ?? null;

  return (
    <div data-testid="connection-binding-editor">
      {view === "connection" ? (
        <form
          onSubmit={handleConnectionSubmit}
          className="flex flex-col gap-4 rounded-xl border border-ra-border bg-ra-secondary p-4"
          data-testid="connection-editor"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-ra-text">
                {creating ? "新建连接" : connection?.name ?? "选择连接"}
              </h2>
              <p className="mt-1 text-xs text-ra-text-tertiary">
                API Key 只发送到模型控制服务，不写入浏览器存储。
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <Field label="连接 ID">
              <input
                aria-label="连接 ID"
                value={connDraft.connectionId}
                disabled={!creating}
                onChange={(event) =>
                  setConnDraft((d) => ({ ...d, connectionId: event.target.value }))
                }
                className={inputClass}
                autoComplete="off"
              />
            </Field>
            <Field label="连接名称">
              <input
                aria-label="连接名称"
                value={connDraft.name}
                onChange={(event) =>
                  setConnDraft((d) => ({ ...d, name: event.target.value }))
                }
                className={inputClass}
                autoComplete="off"
              />
            </Field>
            <Field label="Provider">
              <select
                aria-label="Provider"
                value={connDraft.provider}
                onChange={(event) =>
                  setConnDraft((d) => ({
                    ...d,
                    provider: event.target.value as ConnectionProvider,
                  }))
                }
                className={inputClass}
              >
                <option value="litellm-proxy">LiteLLM Proxy</option>
                <option value="openai-compatible">OpenAI Compatible</option>
              </select>
            </Field>
            <Field label="认证方式">
              <select
                aria-label="认证方式"
                value={connDraft.authMethod}
                onChange={(event) =>
                  setConnDraft((d) => ({
                    ...d,
                    authMethod: event.target.value as AuthMethod,
                  }))
                }
                className={inputClass}
              >
                <option value="api_key">API Key</option>
              </select>
            </Field>
            <Field label="Base URL" className="md:col-span-2">
              <input
                aria-label="Base URL"
                value={connDraft.baseUrl}
                onChange={(event) =>
                  setConnDraft((d) => ({ ...d, baseUrl: event.target.value }))
                }
                className={inputClass}
                inputMode="url"
                autoComplete="url"
              />
            </Field>
            <Field
              label={`API Key（${connection?.secretStatus === "session" ? "已配置（进程会话）" : connection?.secretStatus === "environment" ? "已配置（环境变量）" : "仅本次提交"}）`}
              className="md:col-span-2"
            >
              <input
                aria-label="API Key"
                type="password"
                value={connApiKey}
                onChange={(event) => setConnApiKey(event.target.value)}
                className={inputClass}
                autoComplete="new-password"
                placeholder={
                  connection?.secretStatus === "missing"
                    ? "尚未配置"
                    : "已配置；留空表示不替换"
                }
              />
            </Field>
          </div>

          <label className="inline-flex items-center gap-2 text-sm text-ra-text-secondary">
            <input
              type="checkbox"
              checked={connDraft.enabled}
              onChange={(event) =>
                setConnDraft((d) => ({ ...d, enabled: event.target.checked }))
              }
            />
            启用该连接
          </label>

          {connError && (
            <p role="alert" className="text-sm text-red-300">
              {connError}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-2 border-t border-ra-border pt-3">
            <button type="submit" disabled={busy} className={primaryButtonClass}>
              <Save className="h-4 w-4" aria-hidden="true" />
              保存连接
            </button>
            <button
              type="button"
              disabled={!connSavedId || busy}
              onClick={() =>
                connSavedId ? onConnectionDelete(connSavedId) : undefined
              }
              className={cn(secondaryButtonClass, "md:ml-auto text-red-300")}
            >
              <Trash2 className="h-4 w-4" aria-hidden="true" />
              删除连接
            </button>
          </div>
        </form>
      ) : (
        <form
          onSubmit={handleBindingSubmit}
          className="flex flex-col gap-4 rounded-xl border border-ra-border bg-ra-secondary p-4"
          data-testid="binding-editor"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-ra-text">
                {creating ? "新建绑定" : binding?.name ?? "选择绑定"}
              </h2>
              <p className="mt-1 text-xs text-ra-text-tertiary">
                绑定关联执行器、连接和 Model ID，不包含任何凭据。
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <Field label="绑定 ID">
              <input
                aria-label="绑定 ID"
                value={bindDraft.bindingId}
                disabled={!creating}
                onChange={(event) =>
                  setBindDraft((d) => ({ ...d, bindingId: event.target.value }))
                }
                className={inputClass}
                autoComplete="off"
              />
            </Field>
            <Field label="绑定名称">
              <input
                aria-label="绑定名称"
                value={bindDraft.name}
                onChange={(event) =>
                  setBindDraft((d) => ({ ...d, name: event.target.value }))
                }
                className={inputClass}
                autoComplete="off"
              />
            </Field>
            <Field label="执行器">
              <select
                aria-label="执行器"
                value={bindDraft.executorId}
                onChange={(event) =>
                  setBindDraft((d) => ({ ...d, executorId: event.target.value }))
                }
                className={inputClass}
                disabled={executors.filter((e) => e.operational).length === 0}
              >
                <option value="">请选择执行器</option>
                {executors
                  .filter((e) => e.operational)
                  .map((executor) => (
                    <option key={executor.executorId} value={executor.executorId}>
                      {executor.name}
                    </option>
                  ))}
              </select>
            </Field>
            <Field label="连接">
              <select
                aria-label="连接"
                value={bindDraft.connectionId}
                onChange={(event) =>
                  setBindDraft((d) => ({ ...d, connectionId: event.target.value }))
                }
                className={inputClass}
                disabled={connections.filter((c) => c.enabled).length === 0}
              >
                <option value="">请选择连接</option>
                {connections
                  .filter((c) => c.enabled)
                  .map((conn) => (
                    <option key={conn.connectionId} value={conn.connectionId}>
                      {conn.name} · {conn.provider}
                    </option>
                  ))}
              </select>
            </Field>
            <Field label="Model ID" className="md:col-span-2">
              <input
                aria-label="Model ID"
                value={bindDraft.modelId}
                onChange={(event) =>
                  setBindDraft((d) => ({ ...d, modelId: event.target.value }))
                }
                className={inputClass}
                autoComplete="off"
              />
            </Field>
          </div>

          <label className="inline-flex items-center gap-2 text-sm text-ra-text-secondary">
            <input
              type="checkbox"
              checked={bindDraft.enabled}
              onChange={(event) =>
                setBindDraft((d) => ({ ...d, enabled: event.target.checked }))
              }
            />
            启用该绑定
          </label>

          {bindError && (
            <p role="alert" className="text-sm text-red-300">
              {bindError}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-2 border-t border-ra-border pt-3">
            <button type="submit" disabled={busy} className={primaryButtonClass}>
              <Save className="h-4 w-4" aria-hidden="true" />
              保存绑定
            </button>
            <button
              type="button"
              disabled={!bindSavedId || busy}
              onClick={() =>
                bindSavedId ? onBindingDelete(bindSavedId) : undefined
              }
              className={cn(secondaryButtonClass, "md:ml-auto text-red-300")}
            >
              <Trash2 className="h-4 w-4" aria-hidden="true" />
              删除绑定
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

function Field({
  label,
  className,
  children,
}: {
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <label className={cn("flex flex-col gap-1", className)}>
      <span className="text-xs font-medium text-ra-text-tertiary">{label}</span>
      {children}
    </label>
  );
}

const inputClass = cn(
  "w-full rounded-md border border-ra-border bg-ra-input px-3 py-2",
  "text-sm text-ra-text placeholder:text-ra-text-tertiary",
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
  "disabled:cursor-not-allowed disabled:opacity-60",
);

const primaryButtonClass = cn(
  "inline-flex items-center gap-2 rounded-md bg-ra-accent px-3 py-2",
  "text-sm font-medium text-ra-base disabled:cursor-not-allowed disabled:opacity-50",
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-white",
);

const secondaryButtonClass = cn(
  "inline-flex items-center gap-2 rounded-md border border-ra-border px-3 py-2",
  "text-sm text-ra-text-secondary hover:bg-ra-tertiary hover:text-ra-text",
  "disabled:cursor-not-allowed disabled:opacity-50",
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
);
