import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { ExternalLink, Save, Trash2 } from "lucide-react";
import {
  ConnectionInputSchema,
  BindingInputSchema,
  connectionVerificationCapability,
  type AuthMethod,
  type AccountAuthStatus,
  type ConnectionProbeResult,
  type ConnectionModelsResult,
  type ConnectionVerificationCapability,
  type Binding,
  type BindingInput,
  type Connection,
  type ConnectionInput,
  type ConnectionProvider,
  type CatalogBindingInput,
  type CatalogBindingResult,
} from "@/schemas/model-access";
import type { Executor } from "@/schemas/model-access";
import { cn } from "@/lib/cn";
import { connectionConfigurationFingerprint } from "@/lib/model-control-client";

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
  onConnectionTest: (connectionId: string) => Promise<void>;
  onConnectionModelsFetch?: (connectionId: string) => Promise<ConnectionModelsResult>;
  onCatalogBindingSelect?: (input: CatalogBindingInput) => Promise<CatalogBindingResult>;
  connectionProbeResult: ConnectionProbeResult | null;
  connectionProbePending: boolean;
  connectionModelsPending?: boolean;
  accountAuthState?: AccountAuthStatus | null;
  accountAuthPending?: boolean;
  onAccountAuthStart?: (connectionId: string) => Promise<void>;
  onAccountAuthComplete?: (connectionId: string, code?: string) => Promise<void>;
  onAccountAuthCancel?: (connectionId: string) => Promise<void>;
  onAccountAuthLogout?: (connectionId: string) => Promise<void>;
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
  onConnectionTest,
  onConnectionModelsFetch,
  onCatalogBindingSelect,
  connectionProbeResult,
  connectionProbePending,
  connectionModelsPending = false,
  accountAuthState = null,
  accountAuthPending = false,
  onAccountAuthStart,
  onAccountAuthComplete,
  onAccountAuthCancel,
  onAccountAuthLogout,
}: ConnectionBindingEditorProps) {
  const [connDraft, setConnDraft] = useState<ConnectionInput>(EMPTY_CONNECTION);
  const [connApiKey, setConnApiKey] = useState("");
  const [connClearSecret, setConnClearSecret] = useState(false);
  const [connError, setConnError] = useState<string | null>(null);
  const [bindDraft, setBindDraft] = useState<BindingInput>(EMPTY_BINDING);
  const [bindError, setBindError] = useState<string | null>(null);
  const [accountAuthCode, setAccountAuthCode] = useState("");
  const [catalog, setCatalog] = useState<ConnectionModelsResult | null>(null);
  const [catalogStamp, setCatalogStamp] = useState("");
  const [catalogPending, setCatalogPending] = useState(false);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [catalogModelId, setCatalogModelId] = useState("");
  const [catalogExecutorId, setCatalogExecutorId] = useState("");
  const [catalogSelecting, setCatalogSelecting] = useState(false);
  const [catalogSaveEpoch, setCatalogSaveEpoch] = useState(0);
  const [discoveryAfterSave, setDiscoveryAfterSave] = useState<string | null>(null);
  const catalogRequest = useRef(0);
  const catalogObserved = useRef(false);

  const [connSavedDraft, setConnSavedDraft] = useState<ConnectionInput | null>(null);
  const [connSavedApiKey, setConnSavedApiKey] = useState("");

  useEffect(() => {
    if (view === "connection") {
      const draft: ConnectionInput = connection
        ? {
            connectionId: connection.connectionId,
            name: connection.name,
            provider: connection.provider,
            baseUrl: connection.baseUrl,
            authMethod: connection.authMethod,
            enabled: connection.enabled,
            upstreamProviderId: connection.upstreamProviderId,
            protocolFamily: connection.protocolFamily,
            executorProviderId: connection.executorProviderId,
          }
        : EMPTY_CONNECTION;
      setConnDraft(draft);
      setConnApiKey("");
      setConnClearSecret(false);
      setConnSavedDraft(structuredClone(draft));
      setConnSavedApiKey("");
      setConnError(null);
      setAccountAuthCode("");
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

  const connDirty = useMemo(() => {
    if (connSavedDraft === null) return false;
    if (connApiKey !== connSavedApiKey) return true;
    if (connClearSecret) return true;
    return (
      connDraft.connectionId !== connSavedDraft.connectionId ||
      connDraft.name !== connSavedDraft.name ||
      connDraft.provider !== connSavedDraft.provider ||
      connDraft.baseUrl !== connSavedDraft.baseUrl ||
      connDraft.authMethod !== connSavedDraft.authMethod ||
      connDraft.enabled !== connSavedDraft.enabled ||
      connDraft.upstreamProviderId !== connSavedDraft.upstreamProviderId ||
      connDraft.protocolFamily !== connSavedDraft.protocolFamily ||
      connDraft.executorProviderId !== connSavedDraft.executorProviderId
    );
  }, [connDraft, connApiKey, connClearSecret, connSavedDraft, connSavedApiKey]);

  const catalogTarget = view === "connection" ? connection
    : connections.find((item) => item.connectionId === bindDraft.connectionId) ?? null;
  const catalogContext = JSON.stringify([view, creating,
    catalogTarget ? connectionConfigurationFingerprint(catalogTarget) : "",
    view === "connection" ? connectionConfigurationFingerprint(connDraft) : "",
    view === "connection" && connDirty, catalogSaveEpoch]);
  const catalogContextRef = useRef(catalogContext);
  catalogContextRef.current = catalogContext;
  const catalogTargetRef = useRef(catalogTarget);
  catalogTargetRef.current = catalogTarget;
  const fetchModelsRef = useRef(onConnectionModelsFetch);
  fetchModelsRef.current = onConnectionModelsFetch;
  const catalogBlockedRef = useRef(false);
  catalogBlockedRef.current = (view === "connection" && (creating || connDirty)) || !catalogTarget;
  const visibleCatalog = catalogStamp === catalogContext ? catalog : null;
  const connModels = visibleCatalog?.models ?? [];
  const connModelsMessage = visibleCatalog ? localizedModelsMessage(visibleCatalog) : null;

  useEffect(() => {
    catalogRequest.current += 1;
    setCatalog(null);
    setCatalogStamp("");
    setCatalogPending(false);
    setCatalogError(catalogObserved.current ? "连接配置或选择已变化，旧目录已失效。请保存修改或重新获取。" : null);
    catalogObserved.current = false;
    setCatalogModelId("");
    setCatalogSelecting(false);
  }, [catalogContext]);

  const fetchCatalog = useCallback(async () => {
    const target = catalogTargetRef.current;
    const fetchModels = fetchModelsRef.current;
    if (!target || !fetchModels || catalogBlockedRef.current) return;
    const request = ++catalogRequest.current;
    const stamp = catalogContextRef.current;
    setCatalog(null);
    setCatalogError(null);
    setCatalogModelId("");
    setCatalogPending(true);
    try {
      const result = await fetchModels(target.connectionId);
      if (request !== catalogRequest.current || stamp !== catalogContextRef.current) return;
      if (result.connectionId && result.connectionId !== target.connectionId) {
        setCatalogError("模型目录与当前连接不匹配，请重新获取。");
        return;
      }
      setCatalog(result);
      setCatalogStamp(stamp);
      catalogObserved.current = true;
    } catch {
      if (request === catalogRequest.current && stamp === catalogContextRef.current) {
        setCatalogError("获取模型目录失败，请检查连接后重新获取。");
      }
    } finally {
      if (request === catalogRequest.current && stamp === catalogContextRef.current) setCatalogPending(false);
    }
  }, []);

  useEffect(() => {
    if (view !== "connection" || creating || connDirty || !catalogTarget
      || discoveryAfterSave !== catalogTarget.connectionId) return;
    setDiscoveryAfterSave(null);
    void fetchCatalog();
  }, [view, creating, connDirty, catalogTarget, discoveryAfterSave, fetchCatalog]);

  const authorityChanged = useMemo(() => {
    if (!connection || creating || view !== "connection") return false;
    return (
      connDraft.provider !== connection.provider ||
      connDraft.baseUrl !== connection.baseUrl ||
      connDraft.authMethod !== connection.authMethod
    );
  }, [connection, creating, view, connDraft]);

  const discardingConfiguredCredential =
    !!connection &&
    !creating &&
    view === "connection" &&
    connection.authMethod === "api_key" &&
    connection.credentialConfigured &&
    connDraft.authMethod !== "api_key";

  const authorityChangeUnresolved =
    (authorityChanged &&
      connDraft.authMethod === "api_key" &&
      !connApiKey &&
      !connDraft.apiKeyEnv &&
      !connClearSecret) ||
    (discardingConfiguredCredential && !connClearSecret);

  async function handleConnectionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (authorityChangeUnresolved) {
      setConnError(
        discardingConfiguredCredential
          ? "当前连接仍配置了 API Key 凭据。切换到其他认证方式前必须明确勾选“清除已保存密钥”。"
          : "正在修改认证相关配置（Provider / Base URL / 认证方式）。保存前需要：填写新的 API Key 或环境变量引用、勾选“清除已保存密钥”，或还原上述修改。",
      );
      return;
    }
    const parsed = ConnectionInputSchema.safeParse({
      ...connDraft,
      ...(connApiKey ? { apiKey: connApiKey } : {}),
      ...(connClearSecret ? { clearSecret: true } : {}),
    });
    if (!parsed.success) {
      setConnError(parsed.error.issues[0]?.message ?? "连接配置无效");
      return;
    }
    setConnError(null);
    try {
      await onConnectionSave(parsed.data);
    } catch (cause) {
      setConnError(
        cause instanceof Error ? cause.message : "保存连接失败",
      );
      return;
    }
    setConnApiKey("");
    setConnClearSecret(false);
    setConnSavedDraft(structuredClone(connDraft));
    setConnSavedApiKey("");
    catalogRequest.current += 1;
    setCatalogSaveEpoch((value) => value + 1);
    setDiscoveryAfterSave(parsed.data.connectionId);
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

  async function handleFetchModels() {
    await fetchCatalog();
  }

  async function handleCatalogSelection() {
    if (!visibleCatalog?.configurationRevision || !visibleCatalog.catalogRevision
      || !catalogTarget || !catalogModelId || !catalogExecutorId || !onCatalogBindingSelect) return;
    const stamp = catalogContextRef.current;
    const request = ++catalogRequest.current;
    setCatalogSelecting(true);
    setCatalogError(null);
    try {
      await onCatalogBindingSelect({ connectionId: catalogTarget.connectionId,
        configurationRevision: visibleCatalog.configurationRevision,
        catalogRevision: visibleCatalog.catalogRevision,
        executorId: catalogExecutorId, modelId: catalogModelId });
    } catch {
      if (request === catalogRequest.current && stamp === catalogContextRef.current) {
        setCatalog(null);
        setCatalogModelId("");
        setCatalogError("目录绑定未保存。目录可能已过期，请刷新后重新选择；原手动绑定保持不变。");
      }
    } finally {
      if (request === catalogRequest.current && stamp === catalogContextRef.current) setCatalogSelecting(false);
    }
  }

  async function handleTestConnection() {
    const savedId = connSavedId;
    if (!savedId) return;
    await onConnectionTest(savedId);
  }

  const connSavedId = creating && view === "connection" ? null : connection?.connectionId ?? null;
  const bindSavedId = creating && view === "binding" ? null : binding?.bindingId ?? null;
  const verificationCapability = connection
    ? connectionVerificationCapability(connection)
    : null;
  const verificationGuidance = verificationCapability
    ? connectionVerificationGuidance(verificationCapability)
    : null;
  const canVerifyConnection =
    view === "connection" &&
    !!connSavedId &&
    !connDirty &&
    verificationCapability === "supported" &&
    !connectionProbePending &&
    !busy;
  const savedApiKeyStatus =
    connection?.authMethod === "api_key" ? connection.secretStatus : "missing";
  const durableStatusDetail = durableSecretStatusDetail(savedApiKeyStatus);
  const authorityNoticeVisible =
    (authorityChanged && connDraft.authMethod === "api_key") ||
    discardingConfiguredCredential;
  const canManageSavedSecret =
    !creating &&
    !!connection &&
    connection.authMethod === "api_key" &&
    connection.credentialConfigured &&
    connDraft.authMethod === "api_key" &&
    !authorityNoticeVisible;
  const canManageAccountLogin =
    !creating &&
    !!connection &&
    !connDirty &&
    connection.enabled &&
    connection.provider === "openai" &&
    connection.authMethod === "account_login" &&
    connDraft.provider === "openai" &&
    connDraft.authMethod === "account_login";

  const catalogPanel = catalogPending || visibleCatalog || catalogError ? (
    <section data-testid="connection-model-catalog" className="flex flex-col gap-3 rounded-lg border border-ra-border bg-ra-base/30 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-medium text-ra-text">提供方模型目录</h3>
        <button type="button" onClick={handleFetchModels}
          disabled={busy || catalogPending || catalogSelecting || catalogBlockedRef.current}
          className={secondaryButtonClass}>刷新模型目录</button>
      </div>
      <p className="text-xs text-ra-text-tertiary">目录仅代表提供方公布的模型，尚未验证账户使用权限或任务执行可用性。</p>
      {catalogPending ? <p role="status" className="text-sm text-ra-text-secondary">正在获取模型目录…</p> : null}
      {catalogError ? <p role="alert" className="text-sm text-ra-status-error">{catalogError}</p> : null}
      {connModelsMessage ? <p role="status" data-testid="connection-models-message" className="text-sm text-ra-text-secondary">{connModelsMessage}</p> : null}
      {visibleCatalog?.ok && connModels.length > 0 ? (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="提供方公布的模型">
              <select aria-label="提供方公布的模型" className={inputClass} value={catalogModelId}
                onChange={(event) => setCatalogModelId(event.target.value)} disabled={catalogSelecting}>
                <option value="">请选择模型</option>
                {connModels.map((modelId) => {
                  const record = visibleCatalog.modelRecords.find((item) => item.modelId === modelId);
                  return <option key={modelId} value={modelId}>{record?.displayName ? `${record.displayName} · ${modelId}` : modelId}</option>;
                })}
              </select>
            </Field>
            <Field label="目录绑定执行器">
              <select aria-label="目录绑定执行器" className={inputClass} value={catalogExecutorId}
                onChange={(event) => setCatalogExecutorId(event.target.value)} disabled={catalogSelecting}>
                <option value="">请选择执行器</option>
                {executors.filter((item) => item.executorId === "opencode" && catalogTarget?.provider !== "codex")
                  .map((item) => <option key={item.executorId} value={item.executorId} disabled={!item.operational}>{item.name}{!item.operational ? "（未就绪）" : ""}</option>)}
              </select>
            </Field>
          </div>
          {onCatalogBindingSelect ? <button type="button" onClick={handleCatalogSelection}
            disabled={busy || catalogSelecting || !catalogModelId || !catalogExecutorId
              || !visibleCatalog.configurationRevision || !visibleCatalog.catalogRevision}
            className={primaryButtonClass}>{catalogSelecting ? "保存目录绑定中…" : "使用目录模型创建或复用绑定"}</button> : null}
          {!visibleCatalog.configurationRevision || !visibleCatalog.catalogRevision ? <p className="text-xs text-ra-text-tertiary">目录缺少服务端版本，无法安全创建目录绑定；可保留高级手动设置。</p> : null}
          <p className="text-xs text-ra-text-tertiary">已有手动绑定及其启用状态会保留。保存目录绑定不会启动任务、切换默认模型或授予 GPT 调用权限。</p>
        </>
      ) : null}
    </section>
  ) : null;

  return (
    <div data-testid="connection-binding-editor">
      {view === "connection" ? (
        <form
          onSubmit={handleConnectionSubmit}
          className="flex min-w-0 flex-col gap-5 rounded-2xl border border-ra-border bg-ra-workspace p-4 sm:p-5"
          data-testid="connection-editor"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-ra-text">
                {creating ? "新建连接" : connection?.name ?? "选择连接"}
              </h2>
              <p className="mt-1 text-xs text-ra-text-tertiary">
                {executorManagedAuth(connDraft.authMethod)
                  ? "账号授权由执行器管理，无需填写 API 密钥。"
                  : "API Key 只发送到模型控制服务，不写入浏览器存储。"}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-x-4 gap-y-4 md:grid-cols-2">
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
              <input
                aria-label="Provider"
                list="connection-provider-presets"
                value={connDraft.provider}
                onChange={(event) => {
                  setConnDraft((d) => ({
                    ...d,
                    provider: event.target.value as ConnectionProvider,
                    upstreamProviderId: event.target.value === connection?.provider ? connection.upstreamProviderId : undefined,
                    protocolFamily: event.target.value === connection?.provider ? connection.protocolFamily : undefined,
                    executorProviderId: event.target.value === connection?.provider ? connection.executorProviderId : undefined,
                    ...(event.target.value === "codex" ? { authMethod: "external_cli_session" as const, baseUrl: "https://chatgpt.com" } : {}),
                  }));
                  if (event.target.value === "codex") {
                    setConnApiKey("");
                    setConnClearSecret(false);
                  }
                }}
                className={inputClass}
                autoComplete="off"
                placeholder="例如 litellm-proxy 或自定义 provider ID"
              />
              <datalist id="connection-provider-presets">
                <option value="litellm-proxy">LiteLLM Proxy</option>
                <option value="openai-compatible">OpenAI Compatible</option>
                <option value="codex">Codex CLI 登录</option>
              </datalist>
            </Field>
            <Field label="认证方式">
              <select
                aria-label="认证方式"
                value={connDraft.authMethod}
                onChange={(event) => {
                  const authMethod = event.target.value as AuthMethod;
                  setConnDraft((d) => ({ ...d, authMethod }));
                  if (authMethod !== "api_key") {
                    setConnApiKey("");
                  } else {
                    setConnClearSecret(false);
                  }
                }}
                className={inputClass}
              >
                <option value="api_key">API Key</option>
                <option value="account_login">账号登录</option>
                <option value="external_cli_session">外部 CLI 会话</option>
                <option value="none">无认证</option>
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
            {connDraft.authMethod === "api_key" ? (
              <>
                <Field
                  label={`API Key（${apiKeyStatusLabel(savedApiKeyStatus)}）`}
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
                      connection?.credentialConfigured
                        ? "已配置；留空表示不替换"
                        : "尚未配置"
                    }
                  />
                </Field>
                {durableStatusDetail && (
                  <p
                    data-testid="connection-secret-status-detail"
                    className="md:col-span-2 text-xs text-ra-text-tertiary"
                  >
                    {durableStatusDetail}
                  </p>
                )}
                {canManageSavedSecret ? (
                  <div
                    data-testid="connection-secret-management"
                    className="md:col-span-2 rounded-md border border-ra-border bg-ra-tertiary px-3 py-2 text-xs text-ra-text-secondary"
                  >
                    <p>
                      已保存的密钥不会回显到浏览器。替换请在上方输入新 API Key 后保存；
                      移除请勾选下方选项。
                    </p>
                    <label className="mt-2 inline-flex min-h-6 items-center gap-2 text-xs text-ra-text-secondary">
                      <input
                        type="checkbox"
                        checked={connClearSecret}
                        onChange={(event) =>
                          setConnClearSecret(event.target.checked)
                        }
                      />
                      移除已保存密钥（clear_secret）
                    </label>
                  </div>
                ) : null}
              </>
            ) : (
              <div
                data-testid="connection-auth-guidance"
                className="md:col-span-2 rounded-md border border-ra-border bg-ra-tertiary px-3 py-2 text-xs text-ra-text-tertiary"
              >
                <p>{authMethodGuidance(connDraft.authMethod)}</p>
                {executorManagedAuth(connDraft.authMethod) && connection && (
                  <p
                    data-testid="connection-external-session-readiness"
                    className="mt-1"
                  >
                    外部会话状态：{externalSessionStatusLabel(connection.externalSessionStatus)}
                    {connection.externalSessionStatus === "available"
                      ? " · 可信运行时已观察到可用会话"
                      : connection.externalSessionStatus === "missing"
                        ? " · 尚未观察到可用会话"
                        : connection.externalSessionStatus === "executor_managed"
                          ? " · 由执行器管理，前端不单独验证"
                          : ""}
                  </p>
                )}
                {/* Was `rounded-md border border-ra-border bg-ra-secondary p-3`
                    inside a fieldset that is itself `bg-ra-secondary`: an
                    identical surface carrying its own outline, so the only thing
                    the border communicated was that something was nested (#448
                    §12). A top divider groups it without inventing an elevation
                    the surface does not have. */}
                {canManageAccountLogin && onAccountAuthStart && (
                  <div
                    data-testid="connection-account-auth"
                    className="mt-3 border-t border-ra-border/60 pt-3 text-ra-text-secondary"
                  >
                    <p className="font-medium text-ra-text">
                      OpenAI / ChatGPT（GPT）账号登录
                    </p>
                    <p className="mt-1 text-ra-text-tertiary">
                      登录由 OpenCode 官方 OAuth 流程处理；浏览器不会收到 access token 或 refresh token。
                    </p>
                    {accountAuthState?.instructions && (
                      <p className="mt-2" data-testid="account-auth-instructions">
                        {accountAuthState.instructions}
                      </p>
                    )}
                    {accountAuthState?.authorizationUrl && (
                      <a
                        href={accountAuthState.authorizationUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-2 inline-flex items-center gap-1 text-ra-accent underline"
                        data-testid="account-auth-browser-link"
                      >
                        在浏览器中继续登录
                        <ExternalLink className="h-3 w-3" aria-hidden="true" />
                      </a>
                    )}
                    {accountAuthState?.callbackMethod === "code" &&
                      accountAuthState.status === "awaiting_browser" && (
                        <input
                          aria-label="OAuth 授权码"
                          type="password"
                          value={accountAuthCode}
                          onChange={(event) => setAccountAuthCode(event.target.value)}
                          className={cn(inputClass, "mt-2")}
                          autoComplete="off"
                          placeholder="粘贴浏览器返回的授权码"
                        />
                      )}
                    {accountAuthState && (
                      <p className="mt-2" data-testid="account-auth-status">
                        流程状态：{accountAuthStatusLabel(accountAuthState.status)}
                      </p>
                    )}
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={accountAuthPending || busy}
                        onClick={() => onAccountAuthStart(connection.connectionId)}
                        className={secondaryButtonClass}
                        data-testid="account-auth-start"
                      >
                        <ExternalLink className="h-4 w-4" aria-hidden="true" />
                        浏览器登录
                      </button>
                      {accountAuthState?.status === "awaiting_browser" &&
                        onAccountAuthComplete && (
                          <button
                            type="button"
                            disabled={
                              accountAuthPending ||
                              (accountAuthState.callbackMethod === "code" &&
                                !accountAuthCode.trim())
                            }
                            onClick={async () => {
                              try {
                                await onAccountAuthComplete(
                                  connection.connectionId,
                                  accountAuthState.callbackMethod === "code"
                                    ? accountAuthCode
                                    : undefined,
                                );
                                setAccountAuthCode("");
                              } catch {
                                // The parent surfaces the sanitized failure and
                                // the transient code remains available to retry.
                              }
                            }}
                            className={secondaryButtonClass}
                            data-testid="account-auth-complete"
                          >
                            已完成授权
                          </button>
                        )}
                      {accountAuthState?.status === "awaiting_browser" &&
                        onAccountAuthCancel && (
                          <button
                            type="button"
                            disabled={accountAuthPending}
                            onClick={async () => {
                              try {
                                await onAccountAuthCancel(connection.connectionId);
                                setAccountAuthCode("");
                              } catch {
                                // The parent surfaces the sanitized failure.
                              }
                            }}
                            className={secondaryButtonClass}
                            data-testid="account-auth-cancel"
                          >
                            取消
                          </button>
                        )}
                      {onAccountAuthLogout && (
                        <button
                          type="button"
                          disabled={accountAuthPending}
                          onClick={() => onAccountAuthLogout(connection.connectionId)}
                          className={secondaryButtonClass}
                          data-testid="account-auth-logout"
                        >
                          退出说明
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <label className="inline-flex min-h-6 items-center gap-2 text-sm text-ra-text-secondary">
            <input
              type="checkbox"
              checked={connDraft.enabled}
              onChange={(event) =>
                setConnDraft((d) => ({ ...d, enabled: event.target.checked }))
              }
            />
            启用该连接
          </label>

          {authorityNoticeVisible ? (
            <div
              data-testid="connection-authority-change-notice"
              className="rounded-md border border-ra-border bg-ra-tertiary px-3 py-2 text-xs text-ra-text-secondary"
            >
              <p>
                {discardingConfiguredCredential
                  ? "当前认证方式变更会丢弃已配置的 API Key 凭据。保存前必须明确确认清除。"
                  : "正在修改认证相关配置（Provider / Base URL / 认证方式）。保存前需要明确选择："}
              </p>
              <p className="mt-1 text-ra-text-tertiary">
                {discardingConfiguredCredential
                  ? "该确认仅表示允许删除服务端已配置的凭据；浏览器不会读取密钥或环境变量名。"
                  : "填写新的 API Key 或环境变量引用；或勾选下方“清除已保存密钥”；或还原上述修改。留空保存不会沿用旧密钥。"}
              </p>
              <label className="mt-2 inline-flex min-h-6 items-center gap-2 text-xs text-ra-text-secondary">
                <input
                  type="checkbox"
                  checked={connClearSecret}
                  onChange={(event) => setConnClearSecret(event.target.checked)}
                />
                清除已保存密钥（clear_secret）
              </label>
            </div>
          ) : null}

          {connError && (
            <p role="alert" className="text-sm text-ra-status-error">
              {connError}
            </p>
          )}

          {connSavedId &&
            !connDirty &&
            verificationCapability !== null &&
            verificationCapability !== "supported" &&
            verificationGuidance && (
              <p
                data-testid="connection-verification-capability"
                className="text-sm text-ra-text-tertiary"
              >
                {verificationGuidance}
              </p>
            )}

          {connectionProbeResult && !connDirty && (
            <p
              role="status"
              data-testid="connection-probe-result"
              className={`text-sm ${connectionProbeResult.ok ? "text-ra-status-success" : "text-ra-status-error"}`}
            >
              {connectionProbeResult.ok ? "验证成功" : "验证失败"}：
              {localizedProbeMessage(connectionProbeResult)}
              {connectionProbeResult.latencyMs !== null && (
                <span>（{connectionProbeResult.latencyMs} ms）</span>
              )}
            </p>
          )}

          {catalogPanel}

          <div className="flex flex-wrap items-center gap-2 border-t border-ra-border pt-3">
            <button type="submit" disabled={busy} className={primaryButtonClass}>
              <Save className="h-4 w-4" aria-hidden="true" />
              保存连接
            </button>
            <button
              type="button"
              disabled={!canVerifyConnection}
              onClick={handleTestConnection}
              data-testid="test-connection-button"
              title={
                !connSavedId
                  ? "新建连接需先保存"
                  : connDirty
                    ? "当前有未保存的修改，请先保存"
                    : verificationCapability === "supported"
                      ? "验证连接"
                      : verificationGuidance ?? "当前连接不可验证"
              }
              className={cn(
                secondaryButtonClass,
                connectionProbePending && "opacity-60",
              )}
            >
              {connectionProbePending ? "验证中…" : "验证连接"}
            </button>
            <button
              type="button"
              disabled={!connSavedId || busy}
              onClick={() =>
                connSavedId ? onConnectionDelete(connSavedId) : undefined
              }
              className={cn(secondaryButtonClass, "md:ml-auto text-ra-status-error")}
            >
              <Trash2 className="h-4 w-4" aria-hidden="true" />
              删除连接
            </button>
          </div>
        </form>
      ) : (
        <form
          onSubmit={handleBindingSubmit}
          className="flex min-w-0 flex-col gap-5 rounded-2xl border border-ra-border bg-ra-workspace p-4 sm:p-5"
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

          <div className="grid grid-cols-1 gap-x-4 gap-y-4 md:grid-cols-2">
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
                  .map((executor) => (
                    <option key={executor.executorId} value={executor.executorId} disabled={!executor.operational}>
                      {executor.name}{!executor.operational ? "（未就绪）" : ""}
                    </option>
                  ))}
              </select>
              {bindDraft.executorId === "codex" && (
                <p className="mt-2 text-xs text-ra-text-secondary">
                  使用已有 Codex CLI 登录和原生模型名称，仅支持单任务。登录就绪不代表模型额度或执行结果已经验收。
                </p>
              )}
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
              <div className="flex gap-2">
                <input
                  aria-label="Model ID"
                  value={bindDraft.modelId}
                  list="binding-model-id-options"
                  onChange={(event) =>
                    setBindDraft((d) => ({ ...d, modelId: event.target.value }))
                  }
                  className={inputClass}
                  autoComplete="off"
                  placeholder={
                    connModels.length > 0
                      ? "从下方列表选择或输入"
                      : "填写 Model ID 或点击右侧按钮获取列表"
                  }
                />
                {onConnectionModelsFetch ? (
                  <button
                    type="button"
                    onClick={handleFetchModels}
                    disabled={
                      !bindDraft.connectionId || connectionModelsPending || catalogPending || busy
                    }
                    data-testid="fetch-models-button"
                    title={
                      bindDraft.connectionId
                        ? "读取该连接的提供方模型目录；目录不代表执行可用性"
                        : "请先选择连接"
                    }
                    className={cn(
                      secondaryButtonClass,
                      "shrink-0 whitespace-nowrap",
                      connectionModelsPending && "opacity-60",
                    )}
                  >
                    {connectionModelsPending || catalogPending ? "获取中…" : "获取模型列表"}
                  </button>
                ) : null}
              </div>
              <datalist id="binding-model-id-options">
                {connModels.map((modelId) => (
                  <option key={modelId} value={modelId} />
                ))}
              </datalist>
              <p className="text-xs text-ra-text-tertiary">高级手动设置：用于不支持目录的连接，或保留明确指定的模型。获取目录不会改写这里的值。</p>
            </Field>
          </div>

          {catalogTarget && executorManagedAuth(catalogTarget.authMethod) ? <p data-testid="catalog-unsupported-auth" className="text-xs text-ra-text-tertiary">当前执行器登录方式不支持提供方模型目录，请保留高级手动模型设置；登录就绪不代表模型可用。</p> : null}
          {catalogPanel}

          <label className="inline-flex min-h-6 items-center gap-2 text-sm text-ra-text-secondary">
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
            <p role="alert" className="text-sm text-ra-status-error">
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
              className={cn(secondaryButtonClass, "md:ml-auto text-ra-status-error")}
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

export function executorManagedAuth(authMethod: AuthMethod): boolean {
  return authMethod === "account_login" || authMethod === "external_cli_session";
}

export function externalSessionStatusLabel(
  status: Connection["externalSessionStatus"],
): string {
  switch (status) {
    case "available":
      return "可用";
    case "missing":
      return "未观察到可用会话";
    case "executor_managed":
      return "由执行器管理";
    case "not_applicable":
      return "不适用";
  }
}

function connectionVerificationGuidance(
  capability: ConnectionVerificationCapability,
): string | null {
  switch (capability) {
    case "supported":
      return null;
    case "credential_missing":
      return "请先配置并保存 API Key，然后再验证连接。";
    case "executor_managed":
      return "认证由 OpenCode / 外部会话管理；当前连接不支持独立模型端点验证。";
    case "connection_disabled":
      return "连接已禁用；启用并保存后才能验证。";
  }
}

function accountAuthStatusLabel(status: string): string {
  switch (status) {
    case "awaiting_browser":
      return "等待浏览器授权";
    case "authenticated":
      return "已登录";
    case "verification_pending":
      return "授权完成，等待会话复核";
    case "expired":
      return "已超时";
    case "failed":
      return "登录失败，请检查服务端网络后重新登录";
    case "canceled":
      return "已取消";
    case "provider_logout_required":
      return "需在 OpenCode 中退出";
    case "busy":
      return "其他登录正在进行";
    default:
      return "未启动";
  }
}

function localizedModelsMessage(result: ConnectionModelsResult): string {
  switch (result.status) {
    case "advertised":
      return `已读取 ${result.models.length} 个提供方公布的模型，尚未验证执行可用性。`;
    case "empty":
      return "提供方公布的模型目录为空；这不代表账户已通过执行验证。";
    case "stale_configuration":
    case "stale_catalog":
    case "stale":
    case "catalog_changed":
      return "连接配置或目录已变化，请重新获取模型目录。";
    case "connected":
      return "上游未返回可识别的模型列表";
    case "credential_missing":
    case "credential_replacement_required":
      return "API Key 未配置或需要重新输入";
    case "credential_store_locked":
      return "系统凭据库不可用或已锁定，暂时无法读取已保存的密钥";
    case "disabled":
      return "连接已禁用";
    case "live_probe_disabled":
      return "实时模型目录读取未启用，无法读取提供方公布的模型。";
    case "unsupported_auth_method":
      return "当前认证方式不支持获取模型列表";
    case "upstream_http_error":
      return "上游模型端点返回错误";
    case "invalid_upstream_response":
      return "上游模型端点返回了无效响应";
    case "timeout":
      return "获取模型列表超时";
    case "connection_error":
      return "无法连接上游模型端点";
    case "not_found":
      return "连接不存在";
    default:
      return result.ok ? "未获取到模型" : "获取模型列表失败";
  }
}

function localizedProbeMessage(result: ConnectionProbeResult): string {  switch (result.status) {
    case "connected":
      return "连接成功";
    case "credential_missing":
      return "API Key 未配置或需要重新输入";
    case "credential_store_locked":
      return "系统凭据库不可用或已锁定，暂时无法读取已保存的密钥";
    case "disabled":
      return "连接已禁用";
    case "live_probe_disabled":
      return "实时连接验证未启用";
    case "unsupported_auth_method":
      return "当前认证方式不支持独立连接验证";
    case "upstream_http_error":
      return "上游模型端点返回错误";
    case "invalid_upstream_response":
      return "上游模型端点返回了无效响应";
    case "timeout":
      return "连接验证超时";
    case "connection_error":
      return "无法连接上游模型端点";
    case "not_found":
      return "连接不存在";
    default:
      return result.ok ? "连接成功" : "连接验证失败";
  }
}

function authMethodGuidance(authMethod: AuthMethod): string {
  switch (authMethod) {
    case "api_key":
      return "API Key 由可信模型控制服务管理。";
    case "account_login":
      return "账号登录认证由 OpenCode / 外部会话管理；浏览器不会读取或保存会话凭据。";
    case "external_cli_session":
      return "外部 CLI 会话由执行器管理；浏览器不会读取或保存会话凭据。";
    case "none":
      return "此连接不使用凭据。";
  }
}

function apiKeyStatusLabel(status: Connection["secretStatus"]): string {
  switch (status) {
    case "session":
      return "已配置（进程会话）";
    case "environment":
      return "已配置（环境变量）";
    case "stored":
      return "已安全保存（系统凭据库）";
    case "store_locked":
      return "系统凭据库不可用或已锁定";
    case "replacement_required":
      return "需要重新输入 API Key";
    case "missing":
      return "当前不可用";
    case "not_applicable":
      return "不适用";
  }
}

function durableSecretStatusDetail(
  status: Connection["secretStatus"],
): string | null {
  switch (status) {
    case "stored":
      return "密钥已保存在操作系统凭据库中，重启后无需重新输入；浏览器永远不会读取或回显密钥。";
    case "store_locked":
      return "系统凭据库当前不可用或已锁定。保存或替换密钥会失败，执行解析也会安全关闭；请解锁系统凭据库后重试。";
    case "replacement_required":
      return "系统凭据库中的密钥条目已不存在（可能被外部移除）。请重新输入 API Key 以恢复。";
    default:
      return null;
  }
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
    <label className={cn("flex min-w-0 flex-col gap-1.5", className)}>
      <span className="text-xs font-medium text-ra-text-secondary">{label}</span>
      {children}
    </label>
  );
}

const inputClass = cn(
  "min-h-10 w-full min-w-0 rounded-lg border border-ra-border bg-ra-input px-3 py-2 transition-colors",
  "text-sm text-ra-text placeholder:text-ra-text-tertiary",
  "focus:outline-none focus-visible:border-ra-accent focus-visible:ring-2 focus-visible:ring-ra-accent",
  "disabled:cursor-not-allowed disabled:opacity-60",
);

const primaryButtonClass = cn(
  "inline-flex min-h-10 items-center justify-center gap-2 rounded-lg bg-ra-accent px-3.5 py-2 transition-colors hover:bg-ra-accent-hover",
  "text-sm font-medium text-ra-base disabled:cursor-not-allowed disabled:opacity-50",
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent focus-visible:ring-offset-2 focus-visible:ring-offset-ra-workspace",
);

const secondaryButtonClass = cn(
  "inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-ra-border px-3.5 py-2 transition-colors",
  "text-sm text-ra-text-secondary hover:bg-ra-tertiary hover:text-ra-text",
  "disabled:cursor-not-allowed disabled:opacity-50",
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
);
