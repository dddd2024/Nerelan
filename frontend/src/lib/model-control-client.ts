import {
  ModelConnectionResultSchema,
  ModelProfileInputSchema,
  ModelProfileSchema,
  type ModelConnectionResult,
  type ModelProfile,
  type ModelProfileInput,
} from "@/schemas/model-profile";
import {
  ConnectionInputSchema,
  ConnectionSchema,
  ConnectionProbeResultSchema,
  ConnectionModelsResultSchema,
  AccountAuthStatusSchema,
  ExecutorSchema,
  BindingInputSchema,
  BindingSchema,
  CatalogBindingInputSchema,
  CatalogBindingResultSchema,
  ModelSelectionInputSchema,
  ModelSelectionResultSchema,
  type Connection,
  type ConnectionInput,
  type Executor,
  type Binding,
  type BindingInput,
  type ConnectionProbeResult,
  type ConnectionModelsResult,
  type AccountAuthStatus,
  type CatalogBindingInput,
  type CatalogBindingResult,
  type ModelSelectionInput,
  type ModelSelectionResult,
} from "@/schemas/model-access";

/**
 * Loopback default for the Model Control service.
 *
 * This deliberately mirrors the sibling clients (`task-client`,
 * `platform-client`, `repository-client`), which all fall back to an absolute
 * `http://127.0.0.1:<port>` URL. A relative `/api` cannot work here: the Vite
 * dev server has no `/api` proxy, so a bare `/api/bindings` request lands on
 * the frontend origin, misses Vite's HTML fallback (it is not an `text/html`
 * navigation) and returns 404 - the Settings page then renders empty
 * connection/binding/executor lists with no visible explanation. The same is
 * true of any static build, where no server-side `/api` exists either.
 */
export const DEFAULT_MODEL_CONTROL_API_BASE = "http://127.0.0.1:8765/api";

export interface ModelControlClient {
  listProfiles(): Promise<ModelProfile[]>;
  upsertProfile(input: ModelProfileInput): Promise<ModelProfile>;
  deleteProfile(profileId: string): Promise<void>;
  setDefaultProfile(profileId: string): Promise<ModelProfile[]>;
  testProfile(profileId: string, apiKey?: string): Promise<ModelConnectionResult>;

  listConnections(): Promise<Connection[]>;
  upsertConnection(input: ConnectionInput): Promise<Connection>;
  deleteConnection(connectionId: string): Promise<void>;
  testConnection(connectionId: string): Promise<ConnectionProbeResult>;
  listConnectionModels(connectionId: string): Promise<ConnectionModelsResult>;
  selectCatalogBinding(input: CatalogBindingInput): Promise<CatalogBindingResult>;
  recommendModelSelection(input: ModelSelectionInput): Promise<ModelSelectionResult>;
  getAccountAuthStatus(connectionId: string): Promise<AccountAuthStatus>;
  startAccountAuth(connectionId: string): Promise<AccountAuthStatus>;
  completeAccountAuth(connectionId: string, code?: string): Promise<AccountAuthStatus>;
  cancelAccountAuth(connectionId: string): Promise<AccountAuthStatus>;
  logoutAccountAuth(connectionId: string): Promise<AccountAuthStatus>;
  listExecutors(): Promise<Executor[]>;
  listBindings(): Promise<Binding[]>;
  upsertBinding(input: BindingInput): Promise<Binding>;
  deleteBinding(bindingId: string): Promise<void>;
}

const DEFAULT_MOCK_PROFILES: ModelProfile[] = [
  {
    id: "coding-default",
    name: "默认代码模型",
    provider: "litellm-proxy",
    baseUrl: "http://localhost:4000/v1",
    modelId: "coding-default",
    executor: "openhands",
    enabled: true,
    isDefault: true,
    secretStatus: "environment",
  },
];

const DEFAULT_MOCK_CONNECTIONS: Connection[] = [
  {
    connectionId: "coding-connection",
    name: "默认代码连接",
    provider: "litellm-proxy",
    baseUrl: "http://localhost:4000/v1",
    authMethod: "api_key",
    enabled: true,
    credentialConfigured: true,
    secretStatus: "environment",
    externalSessionStatus: "not_applicable",
  },
];

const DEFAULT_MOCK_EXECUTORS: Executor[] = [
  {
    executorId: "opencode",
    name: "OpenCode",
    operational: true,
    capabilities: ["model_selection", "workspace_execution"],
  },
];

const DEFAULT_MOCK_BINDINGS: Binding[] = [
  {
    bindingId: "coding-binding",
    name: "默认代码绑定",
    executorId: "opencode",
    connectionId: "coding-connection",
    modelId: "coding-default",
    enabled: true,
  },
];

function normalizeProfile(value: unknown): ModelProfile {
  const raw = value as Record<string, unknown>;
  return ModelProfileSchema.parse({
    id: raw.id,
    name: raw.name,
    provider: raw.provider,
    baseUrl: raw.baseUrl ?? raw.base_url,
    modelId: raw.modelId ?? raw.model_id,
    executor: raw.executor,
    enabled: raw.enabled,
    isDefault: raw.isDefault ?? raw.is_default,
    secretStatus: raw.secretStatus ?? raw.secret_status,
  });
}

function normalizeConnection(value: unknown): Connection {
  const raw = value as Record<string, unknown>;
  const authMethod = raw.authMethod ?? raw.auth_method;
  const credentialConfigured =
    raw.credentialConfigured ?? raw.credential_configured;
  return ConnectionSchema.parse({
    connectionId: raw.connectionId ?? raw.connection_id,
    name: raw.name,
    provider: raw.provider,
    baseUrl: raw.baseUrl ?? raw.base_url,
    authMethod,
    enabled: raw.enabled,
    credentialConfigured:
      credentialConfigured ?? (authMethod === "api_key" ? undefined : false),
    secretStatus: raw.secretStatus ?? raw.secret_status,
    externalSessionStatus: raw.externalSessionStatus ?? raw.external_session_status,
    ...identityFields(raw),
  });
}

function identityFields(raw: Record<string, unknown>) {
  const result: Record<string, unknown> = {};
  for (const [camel, snake] of [
    ["upstreamProviderId", "upstream_provider_id"],
    ["protocolFamily", "protocol_family"],
    ["executorProviderId", "executor_provider_id"],
  ]) {
    if (Object.hasOwn(raw, camel) || Object.hasOwn(raw, snake)) {
      result[camel] = Object.hasOwn(raw, camel) ? raw[camel] : raw[snake];
    }
  }
  return result;
}

export function connectionConfigurationFingerprint(connection: Pick<Connection,
  "connectionId" | "provider" | "baseUrl" | "authMethod" | "enabled"
  | "upstreamProviderId" | "protocolFamily" | "executorProviderId">): string {
  return JSON.stringify([connection.connectionId, connection.provider, connection.baseUrl,
    connection.authMethod, connection.enabled, connection.upstreamProviderId ?? null,
    connection.protocolFamily ?? null, connection.executorProviderId ?? null]);
}

function normalizeCatalog(value: unknown): ConnectionModelsResult {
  const raw = value as Record<string, unknown>;
  const records = raw.modelRecords ?? raw.model_records;
  return ConnectionModelsResultSchema.parse({
    ok: raw.ok, status: raw.status, message: raw.message,
    latencyMs: raw.latencyMs ?? raw.latency_ms ?? null,
    models: raw.models,
    connectionId: raw.connectionId ?? raw.connection_id,
    configurationRevision: raw.configurationRevision ?? raw.configuration_revision,
    catalogRevision: raw.catalogRevision ?? raw.catalog_revision,
    observedAt: raw.observedAt ?? raw.observed_at,
    source: raw.source,
    entitlement: raw.entitlement,
    modelRecords: Array.isArray(records) ? records.map((value) => {
      const record = value as Record<string, unknown>;
      return { modelId: record.modelId ?? record.model_id,
        displayName: record.displayName ?? record.display_name,
        ownedBy: record.ownedBy ?? record.owned_by };
    }) : undefined,
  });
}

function normalizeSelection(value: unknown): ModelSelectionResult {
  const raw = value as Record<string, unknown>;
  function candidate(value: unknown) {
    if (value === null) return null;
    const item = value as Record<string, unknown>;
    return {
      bindingRef: item.bindingRef ?? item.binding_ref,
      connectionId: item.connectionId ?? item.connection_id,
      executorId: item.executorId ?? item.executor_id,
      modelId: item.modelId ?? item.model_id,
      configurationRevision: item.configurationRevision ?? item.configuration_revision ?? null,
      catalogRevision: item.catalogRevision ?? item.catalog_revision ?? null,
      source: item.source, eligible: item.eligible,
      reasonCodes: item.reasonCodes ?? item.reason_codes,
      explanation: item.explanation, availability: item.availability,
      underlyingIdentity: item.underlyingIdentity ?? item.underlying_identity ?? null,
      underlyingIdentityStatus: item.underlyingIdentityStatus ?? item.underlying_identity_status,
      cost: item.cost, quality: item.quality,
    };
  }
  return ModelSelectionResultSchema.parse({
    previewOnly: raw.previewOnly ?? raw.preview_only,
    status: raw.status, message: raw.message, policyId: raw.policyId ?? raw.policy_id,
    recommended: candidate(raw.recommended),
    candidates: Array.isArray(raw.candidates) ? raw.candidates.map(candidate) : raw.candidates,
    evidenceUnknowns: raw.evidenceUnknowns ?? raw.evidence_unknowns,
  });
}

function normalizeExecutor(value: unknown): Executor {
  const raw = value as Record<string, unknown>;
  return ExecutorSchema.parse({
    executorId: raw.executorId ?? raw.executor_id,
    name: raw.name,
    operational: raw.operational,
    capabilities: Array.isArray(raw.capabilities) ? raw.capabilities : [],
    readinessStatus: raw.readinessStatus ?? raw.readiness_status,
  });
}

function normalizeBinding(value: unknown): Binding {
  const raw = value as Record<string, unknown>;
  return BindingSchema.parse({
    bindingId: raw.bindingId ?? raw.binding_id,
    name: raw.name,
    executorId: raw.executorId ?? raw.executor_id,
    connectionId: raw.connectionId ?? raw.connection_id,
    modelId: raw.modelId ?? raw.model_id,
    enabled: raw.enabled,
  });
}

function normalizeAccountAuth(value: unknown): AccountAuthStatus {
  const raw = value as Record<string, unknown>;
  return AccountAuthStatusSchema.parse({
    status: raw.status,
    provider: raw.provider,
    externalSessionStatus:
      raw.externalSessionStatus ?? raw.external_session_status,
    authorizationUrl: raw.authorizationUrl ?? raw.authorization_url,
    callbackMethod: raw.callbackMethod ?? raw.callback_method,
    instructions: raw.instructions,
    expiresInSeconds: raw.expiresInSeconds ?? raw.expires_in_seconds,
  });
}

function serializeConnectionInput(input: ConnectionInput) {
  const parsed = ConnectionInputSchema.parse(input);
  const body: Record<string, unknown> = {
    connection_id: parsed.connectionId,
    name: parsed.name,
    provider: parsed.provider,
    base_url: parsed.baseUrl,
    auth_method: parsed.authMethod,
    enabled: parsed.enabled,
  };
  if (parsed.executorProviderId !== undefined) {
    body.executor_provider_id = parsed.executorProviderId;
    body.upstream_provider_id = parsed.upstreamProviderId ?? null;
    body.protocol_family = parsed.protocolFamily ?? null;
  }
  if (parsed.apiKey !== undefined && parsed.apiKey !== "") {
    body.api_key = parsed.apiKey;
  }
  if (parsed.apiKeyEnv !== undefined && parsed.apiKeyEnv !== "") {
    body.api_key_env = parsed.apiKeyEnv;
  }
  if (parsed.clearSecret !== undefined) {
    body.clear_secret = parsed.clearSecret;
  }
  return body;
}

function serializeBindingInput(input: BindingInput) {
  const parsed = BindingInputSchema.parse(input);
  return {
    binding_id: parsed.bindingId,
    name: parsed.name,
    executor_id: parsed.executorId,
    connection_id: parsed.connectionId,
    model_id: parsed.modelId,
    enabled: parsed.enabled,
  };
}

function serializeProfileInput(input: ModelProfileInput) {
  const parsed = ModelProfileInputSchema.parse(input);
  return {
    id: parsed.id,
    name: parsed.name,
    provider: parsed.provider,
    base_url: parsed.baseUrl,
    model_id: parsed.modelId,
    executor: parsed.executor,
    enabled: parsed.enabled,
    is_default: parsed.isDefault,
    ...(parsed.apiKey ? { api_key: parsed.apiKey } : {}),
    ...(parsed.apiKeyEnv ? { api_key_env: parsed.apiKeyEnv } : {}),
  };
}

function messageFromError(error: unknown): string {
  if (error instanceof Error) return error.message;
  return "模型控制服务请求失败";
}

async function requestJson(
  url: string,
  init?: RequestInit,
): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch (error) {
    throw new Error(`无法连接模型控制服务：${messageFromError(error)}`);
  }

  const text = await response.text();
  const payload = text ? safeJson(text) : null;
  if (!response.ok) {
    const detail =
      payload && typeof payload === "object" && "error" in payload
        ? String((payload as { error: unknown }).error)
        : `${response.status} ${response.statusText}`;
    throw new Error(detail);
  }
  return payload;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw new Error("模型控制服务返回了无效 JSON");
  }
}

export function createHttpModelControlClient(
  apiBase = DEFAULT_MODEL_CONTROL_API_BASE,
): ModelControlClient {
  const baseUrl = apiBase.replace(/\/$/, "");
  const profilesUrl = `${baseUrl}/model-profiles`;
  const connectionsUrl = `${baseUrl}/connections`;
  const executorsUrl = `${baseUrl}/executors`;
  const bindingsUrl = `${baseUrl}/bindings`;

  return {
    async listProfiles() {
      const payload = await requestJson(profilesUrl);
      const values = Array.isArray(payload)
        ? payload
        : ((payload as { profiles?: unknown[] } | null)?.profiles ?? []);
      return values.map(normalizeProfile);
    },

    async upsertProfile(input) {
      const parsed = ModelProfileInputSchema.parse(input);
      const payload = await requestJson(
        `${profilesUrl}/${encodeURIComponent(parsed.id)}`,
        {
          method: "PUT",
          body: JSON.stringify(serializeProfileInput(parsed)),
        },
      );
      return normalizeProfile(payload);
    },

    async deleteProfile(profileId) {
      await requestJson(`${profilesUrl}/${encodeURIComponent(profileId)}`, {
        method: "DELETE",
      });
    },

    async setDefaultProfile(profileId) {
      const payload = await requestJson(
        `${profilesUrl}/${encodeURIComponent(profileId)}/default`,
        { method: "POST" },
      );
      const values = Array.isArray(payload)
        ? payload
        : ((payload as { profiles?: unknown[] } | null)?.profiles ?? []);
      return values.map(normalizeProfile);
    },

    async testProfile(profileId, apiKey) {
      const payload = await requestJson(
        `${profilesUrl}/${encodeURIComponent(profileId)}/test`,
        {
          method: "POST",
          body: JSON.stringify(apiKey ? { api_key: apiKey } : {}),
        },
      );
      const raw = payload as Record<string, unknown>;
      return ModelConnectionResultSchema.parse({
        ok: raw.ok,
        status: raw.status,
        message: raw.message,
        latencyMs: raw.latencyMs ?? raw.latency_ms ?? null,
      });
    },

    async listConnections() {
      const payload = await requestJson(connectionsUrl);
      const values = Array.isArray(payload)
        ? payload
        : ((payload as { connections?: unknown[] } | null)?.connections ?? []);
      return values.map(normalizeConnection);
    },

    async upsertConnection(input) {
      const parsed = ConnectionInputSchema.parse(input);
      const payload = await requestJson(
        `${connectionsUrl}/${encodeURIComponent(parsed.connectionId)}`,
        {
          method: "PUT",
          body: JSON.stringify(serializeConnectionInput(parsed)),
        },
      );
      return normalizeConnection(payload);
    },

    async deleteConnection(connectionId) {
      await requestJson(`${connectionsUrl}/${encodeURIComponent(connectionId)}`, {
        method: "DELETE",
      });
    },

    async testConnection(connectionId) {
      const payload = await requestJson(
        `${connectionsUrl}/${encodeURIComponent(connectionId)}/test`,
        {
          method: "POST",
          body: JSON.stringify({}),
        },
      );
      const raw = payload as Record<string, unknown>;
      return ConnectionProbeResultSchema.parse({
        ok: raw.ok,
        status: raw.status,
        message: raw.message,
        latencyMs: raw.latencyMs ?? raw.latency_ms ?? null,
      });
    },

    async listConnectionModels(connectionId) {
      const payload = await requestJson(
        `${connectionsUrl}/${encodeURIComponent(connectionId)}/models`,
        {
          method: "POST",
          body: JSON.stringify({}),
        },
      );
      return normalizeCatalog(payload);
    },

    async selectCatalogBinding(input) {
      const parsed = CatalogBindingInputSchema.parse(input);
      const payload = await requestJson(`${connectionsUrl}/${encodeURIComponent(parsed.connectionId)}/models/bindings`, {
        method: "POST",
        body: JSON.stringify({ configuration_revision: parsed.configurationRevision,
          catalog_revision: parsed.catalogRevision, executor_id: parsed.executorId, model_id: parsed.modelId }),
      });
      const raw = payload as Record<string, unknown>;
      return CatalogBindingResultSchema.parse({
        binding: normalizeBinding(raw.binding), created: raw.created,
        reusedManual: raw.reusedManual ?? raw.reused_manual,
        configurationRevision: raw.configurationRevision ?? raw.configuration_revision,
        catalogRevision: raw.catalogRevision ?? raw.catalog_revision,
        source: raw.source, advertisedModelId: raw.advertisedModelId ?? raw.advertised_model_id,
        availability: raw.availability,
      });
    },

    async recommendModelSelection(input) {
      const parsed = ModelSelectionInputSchema.parse(input);
      return normalizeSelection(await requestJson(`${baseUrl}/model-selections/recommend`, {
        method: "POST", body: JSON.stringify({ selection_mode: parsed.selectionMode,
          ...(parsed.manualBindingRef !== undefined ? { manual_binding_ref: parsed.manualBindingRef } : {}),
          ...(parsed.purpose !== undefined ? { purpose: parsed.purpose } : {}),
          ...(parsed.requiredCapabilities !== undefined ? { required_capabilities: parsed.requiredCapabilities } : {}),
          ...(parsed.orchestrationMode !== undefined ? { orchestration_mode: parsed.orchestrationMode } : {}),
          ...(parsed.executorPreference !== undefined ? { executor_preference: parsed.executorPreference } : {}),
          ...(parsed.preferredBindingRefs !== undefined ? { preferred_binding_refs: parsed.preferredBindingRefs } : {}),
        }),
      }));
    },

    async getAccountAuthStatus(connectionId) {
      const payload = await requestJson(
        `${connectionsUrl}/${encodeURIComponent(connectionId)}/account-auth`,
      );
      return normalizeAccountAuth(payload);
    },

    async startAccountAuth(connectionId) {
      const payload = await requestJson(
        `${connectionsUrl}/${encodeURIComponent(connectionId)}/account-auth/start`,
        { method: "POST", body: JSON.stringify({}) },
      );
      return normalizeAccountAuth(payload);
    },

    async completeAccountAuth(connectionId, code) {
      const payload = await requestJson(
        `${connectionsUrl}/${encodeURIComponent(connectionId)}/account-auth/callback`,
        {
          method: "POST",
          body: JSON.stringify(code ? { code } : {}),
        },
      );
      return normalizeAccountAuth(payload);
    },

    async cancelAccountAuth(connectionId) {
      const payload = await requestJson(
        `${connectionsUrl}/${encodeURIComponent(connectionId)}/account-auth/cancel`,
        { method: "POST", body: JSON.stringify({}) },
      );
      return normalizeAccountAuth(payload);
    },

    async logoutAccountAuth(connectionId) {
      const payload = await requestJson(
        `${connectionsUrl}/${encodeURIComponent(connectionId)}/account-auth/logout`,
        { method: "POST", body: JSON.stringify({}) },
      );
      return normalizeAccountAuth(payload);
    },

    async listExecutors() {
      const payload = await requestJson(executorsUrl);
      const values = Array.isArray(payload)
        ? payload
        : ((payload as { executors?: unknown[] } | null)?.executors ?? []);
      return values.map(normalizeExecutor);
    },

    async listBindings() {
      const payload = await requestJson(bindingsUrl);
      const values = Array.isArray(payload)
        ? payload
        : ((payload as { bindings?: unknown[] } | null)?.bindings ?? []);
      return values.map(normalizeBinding);
    },

    async upsertBinding(input) {
      const parsed = BindingInputSchema.parse(input);
      const payload = await requestJson(
        `${bindingsUrl}/${encodeURIComponent(parsed.bindingId)}`,
        {
          method: "PUT",
          body: JSON.stringify(serializeBindingInput(parsed)),
        },
      );
      return normalizeBinding(payload);
    },

    async deleteBinding(bindingId) {
      await requestJson(`${bindingsUrl}/${encodeURIComponent(bindingId)}`, {
        method: "DELETE",
      });
    },
  };
}

export function createMockModelControlClient(
  initialProfiles: ModelProfile[] = DEFAULT_MOCK_PROFILES,
): ModelControlClient {
  let profiles = initialProfiles.map((profile) =>
    ModelProfileSchema.parse(structuredClone(profile)),
  );

  let connections = DEFAULT_MOCK_CONNECTIONS.map((c) =>
    ConnectionSchema.parse(structuredClone(c)),
  );

  const executors = DEFAULT_MOCK_EXECUTORS.map((e) =>
    ExecutorSchema.parse(structuredClone(e)),
  );

  let bindings = DEFAULT_MOCK_BINDINGS.map((b) =>
    BindingSchema.parse(structuredClone(b)),
  );
  let generation = 0;
  let generatedCount = 0;
  const revisions = new Map(connections.map((connection) => [connection.connectionId, `mock-config-${++generation}`]));
  const catalogs = new Map<string, ConnectionModelsResult>();
  const generated = new Map<string, { configurationRevision: string; catalogRevision: string; advertisedModelId: string }>();

  function normalizeDefaults(next: ModelProfile[]): ModelProfile[] {
    const requestedDefault = next.find((profile) => profile.isDefault);
    const fallback = requestedDefault ?? next.find((profile) => profile.enabled);
    return next.map((profile) => ({
      ...profile,
      isDefault: fallback ? profile.id === fallback.id : false,
    }));
  }

  return {
    async listProfiles() {
      return structuredClone(profiles);
    },

    async upsertProfile(input) {
      const parsed = ModelProfileInputSchema.parse(input);
      const existing = profiles.find((profile) => profile.id === parsed.id);
      const saved: ModelProfile = {
        id: parsed.id,
        name: parsed.name,
        provider: parsed.provider,
        baseUrl: parsed.baseUrl,
        modelId: parsed.modelId,
        executor: parsed.executor,
        enabled: parsed.enabled,
        isDefault: parsed.isDefault,
        secretStatus: parsed.apiKey
          ? "session"
          : parsed.apiKeyEnv
            ? "environment"
            : (existing?.secretStatus ?? "missing"),
      };
      profiles = normalizeDefaults([
        ...profiles.filter((profile) => profile.id !== saved.id).map((profile) =>
          saved.isDefault ? { ...profile, isDefault: false } : profile,
        ),
        saved,
      ]);
      return structuredClone(
        profiles.find((profile) => profile.id === saved.id) as ModelProfile,
      );
    },

    async deleteProfile(profileId) {
      const deletedWasDefault = profiles.some(
        (profile) => profile.id === profileId && profile.isDefault,
      );
      profiles = profiles.filter((profile) => profile.id !== profileId);
      if (deletedWasDefault) profiles = normalizeDefaults(profiles);
    },

    async setDefaultProfile(profileId) {
      if (!profiles.some((profile) => profile.id === profileId)) {
        throw new Error(`Model profile not found: ${profileId}`);
      }
      profiles = profiles.map((profile) => ({
        ...profile,
        isDefault: profile.id === profileId,
      }));
      return structuredClone(profiles);
    },

    async testProfile(profileId) {
      const profile = profiles.find((item) => item.id === profileId);
      if (!profile) throw new Error(`Model profile not found: ${profileId}`);
      if (!profile.enabled) {
        return {
          ok: false,
          status: "disabled",
          message: "配置已禁用",
          latencyMs: null,
        };
      }
      return {
        ok: true,
        status: "connected",
        message: "连接成功",
        latencyMs: 12,
      };
    },

    async listConnections() {
      return structuredClone(connections);
    },

    async upsertConnection(input) {
      const parsed = ConnectionInputSchema.parse(input);
      const existing = connections.find(
        (connection) => connection.connectionId === parsed.connectionId,
      );
      const apiKeyAuth = parsed.authMethod === "api_key";
      const executorManagedAuth =
        parsed.authMethod === "account_login" ||
        parsed.authMethod === "external_cli_session";
      const credentialConfigured = apiKeyAuth
        ? parsed.clearSecret
          ? false
          : !!parsed.apiKey ||
            !!parsed.apiKeyEnv ||
            (existing?.authMethod === "api_key" &&
              existing.credentialConfigured)
        : false;
      const saved: Connection = {
        connectionId: parsed.connectionId,
        name: parsed.name,
        provider: parsed.provider,
        baseUrl: parsed.baseUrl,
        authMethod: parsed.authMethod,
        enabled: parsed.enabled,
        credentialConfigured,
        secretStatus: apiKeyAuth
          ? parsed.clearSecret
            ? "missing"
            : parsed.apiKey
              ? "session"
              : parsed.apiKeyEnv
                ? "environment"
                : existing?.authMethod === "api_key"
                  ? existing.secretStatus
                  : "missing"
          : "not_applicable",
        externalSessionStatus: executorManagedAuth
          ? "executor_managed"
          : "not_applicable",
        ...identityFields(parsed as Record<string, unknown>),
      };
      if (!existing || connectionConfigurationFingerprint(existing) !== connectionConfigurationFingerprint(saved)
        || parsed.apiKey || parsed.apiKeyEnv || parsed.clearSecret) {
        revisions.set(saved.connectionId, `mock-config-${++generation}`);
        catalogs.delete(saved.connectionId);
      }
      connections = [
        ...connections.filter((c) => c.connectionId !== saved.connectionId),
        saved,
      ];
      return structuredClone(
        connections.find((c) => c.connectionId === saved.connectionId) as Connection,
      );
    },

    async deleteConnection(connectionId) {
      if (!connections.some((c) => c.connectionId === connectionId)) {
        throw new Error(`未找到该连接（${connectionId}）。`);
      }
      const usedByBinding = bindings.some(
        (b) => b.connectionId === connectionId,
      );
      if (usedByBinding) {
        throw new Error("该连接仍被一个绑定引用，请先删除绑定。");
      }
      connections = connections.filter((c) => c.connectionId !== connectionId);
      revisions.delete(connectionId);
      catalogs.delete(connectionId);
    },

    async testConnection(connectionId) {
      const connection = connections.find((c) => c.connectionId === connectionId);
      if (!connection) {
        throw new Error(`未找到该连接（${connectionId}）。`);
      }
      if (!connection.enabled) {
        return {
          ok: false,
          status: "disabled",
          message: "连接已禁用",
          latencyMs: null,
        };
      }
      if (connection.authMethod === "api_key") {
        if (connection.secretStatus === "missing") {
          return {
            ok: false,
            status: "credential_missing",
            message: "API Key 未配置",
            latencyMs: null,
          };
        }
      } else if (connection.authMethod !== "none") {
        return {
          ok: false,
          status: "unsupported_auth_method",
          message: "认证由执行器管理，当前不支持独立连接验证",
          latencyMs: null,
        };
      }
      return {
        ok: true,
        status: "connected",
        message: "连接成功",
        latencyMs: 18,
      };
    },

    async listConnectionModels(connectionId) {
      const connection = connections.find((c) => c.connectionId === connectionId);
      if (!connection) {
        throw new Error(`未找到该连接（${connectionId}）。`);
      }
      catalogs.delete(connectionId);
      const unavailable = (status: string, message: string): ConnectionModelsResult => ({
        ok: false, status, message, latencyMs: null, models: [], modelRecords: [],
        connectionId, configurationRevision: revisions.get(connectionId) ?? null,
        catalogRevision: null, observedAt: null, source: null, entitlement: "not_observed",
      });
      if (!connection.enabled) {
        return unavailable("disabled", "连接已禁用");
      }
      if (connection.authMethod !== "api_key" && connection.authMethod !== "none") {
        return unavailable("unsupported_auth_method", "认证由执行器管理，当前不支持获取模型列表");
      }
      if (connection.authMethod === "api_key" && !["session", "environment", "stored"].includes(connection.secretStatus)) {
        return unavailable(connection.secretStatus === "store_locked" ? "credential_store_locked"
          : connection.secretStatus === "replacement_required" ? "credential_replacement_required" : "credential_missing",
          "当前凭据不可用，无法读取模型目录");
      }
      const result: ConnectionModelsResult = {
        ok: true,
        status: "advertised",
        message: "已读取提供方公布的模型目录，尚未验证执行可用性",
        latencyMs: 18,
        models: ["mock-model-a", "mock-model-b"],
        modelRecords: ["mock-model-a", "mock-model-b"].map((modelId) => ({ modelId, displayName: null, ownedBy: null })),
        connectionId, configurationRevision: revisions.get(connectionId)!,
        catalogRevision: `mock-catalog-${revisions.get(connectionId)}`,
        observedAt: "2026-01-01T00:00:00Z", source: "provider_advertised", entitlement: "not_observed",
      };
      catalogs.set(connectionId, result);
      return structuredClone(result);
    },

    async selectCatalogBinding(input) {
      const parsed = CatalogBindingInputSchema.parse(input);
      const connection = connections.find((item) => item.connectionId === parsed.connectionId);
      const catalog = catalogs.get(parsed.connectionId);
      if (!connection || !catalog || revisions.get(parsed.connectionId) !== parsed.configurationRevision
        || catalog.catalogRevision !== parsed.catalogRevision) throw new Error("模型目录已过期，请重新获取。");
      if (!catalog.models.includes(parsed.modelId)) throw new Error("模型不在当前目录中。");
      if (parsed.executorId !== "opencode" || connection.provider === "codex") throw new Error("当前目录与执行器不兼容。");
      const namespace = connection.executorProviderId ?? connection.provider;
      const modelId = `${namespace}/${parsed.modelId}`;
      const matches = bindings.filter((item) => item.connectionId === parsed.connectionId
        && item.executorId === parsed.executorId
        && (item.modelId === modelId || (!parsed.modelId.includes("/") && item.modelId === parsed.modelId)));
      const previous = matches.find((item) => !generated.has(item.bindingId))
        ?? matches.find((item) => generated.get(item.bindingId)?.configurationRevision === parsed.configurationRevision);
      const provenance = previous ? generated.get(previous.bindingId) : undefined;
      const reusableGenerated = provenance?.configurationRevision === parsed.configurationRevision;
      const saved = previous && (!provenance || reusableGenerated) ? previous : {
        bindingId: `catalog-binding-${++generatedCount}`, name: `${parsed.modelId} · 目录绑定`,
        executorId: parsed.executorId, connectionId: parsed.connectionId, modelId, enabled: true,
      };
      const created = saved !== previous;
      if (created) {
        bindings.push(saved);
        generated.set(saved.bindingId, { configurationRevision: parsed.configurationRevision,
          catalogRevision: parsed.catalogRevision, advertisedModelId: parsed.modelId });
      }
      return CatalogBindingResultSchema.parse({ binding: structuredClone(saved), created,
        reusedManual: !!previous && !provenance,
        configurationRevision: parsed.configurationRevision, catalogRevision: parsed.catalogRevision,
        source: generated.has(saved.bindingId) ? "discovered" : "manual",
        advertisedModelId: parsed.modelId, availability: "advertised_unverified" });
    },

    async recommendModelSelection(input) {
      const parsed = ModelSelectionInputSchema.parse(input);
      const selected = parsed.selectionMode === "manual"
        ? bindings.filter((item) => item.bindingId === parsed.manualBindingRef) : bindings;
      return ModelSelectionResultSchema.parse({ previewOnly: true,
        status: parsed.selectionMode === "manual" ? "manual_blocked" : "no_eligible_pairing",
        message: "当前执行器就绪性尚未观测；推荐仅供预览，尚未通过执行检查。",
        policyId: "catalog-preview-v1", recommended: null,
        evidenceUnknowns: ["cost", "quality", "task_success", "underlying_model_identity"],
        candidates: selected.map((binding) => {
          const provenance = generated.get(binding.bindingId);
          return { bindingRef: binding.bindingId, connectionId: binding.connectionId,
            executorId: binding.executorId, modelId: binding.modelId,
            configurationRevision: revisions.get(binding.connectionId) ?? null,
            catalogRevision: provenance?.catalogRevision ?? null,
            source: provenance ? "discovered" : "manual", eligible: false,
            reasonCodes: ["executor_readiness_not_observed"], explanation: "执行器就绪性尚未观测。",
            availability: provenance ? "advertised_unverified" : "not_observed",
            underlyingIdentity: null, underlyingIdentityStatus: "not_observed", cost: null, quality: null };
        }) });
    },

    async getAccountAuthStatus(connectionId) {
      const connection = connections.find((c) => c.connectionId === connectionId);
      if (!connection) throw new Error(`未找到该连接（${connectionId}）。`);
      return {
        status: "idle",
        provider: "openai",
        externalSessionStatus: connection.externalSessionStatus,
      };
    },

    async startAccountAuth(connectionId) {
      const connection = connections.find((c) => c.connectionId === connectionId);
      if (!connection || connection.authMethod !== "account_login") {
        throw new Error("该连接不使用账号登录方式，无法发起登录。");
      }
      return {
        status: "awaiting_browser",
        provider: "openai",
        authorizationUrl: "https://auth.example.test/authorize",
        callbackMethod: "code",
        instructions: "在浏览器中完成授权。",
        expiresInSeconds: 300,
      };
    },

    async completeAccountAuth(connectionId) {
      connections = connections.map((connection) =>
        connection.connectionId === connectionId
          ? { ...connection, externalSessionStatus: "available" }
          : connection,
      );
      return {
        status: "authenticated",
        provider: "openai",
        externalSessionStatus: "available",
      };
    },

    async cancelAccountAuth(connectionId) {
      const connection = connections.find((c) => c.connectionId === connectionId);
      if (!connection) throw new Error(`未找到该连接（${connectionId}）。`);
      return {
        status: "canceled",
        provider: "openai",
        externalSessionStatus: connection.externalSessionStatus,
      };
    },

    async logoutAccountAuth(connectionId) {
      const connection = connections.find((c) => c.connectionId === connectionId);
      if (!connection) throw new Error(`未找到该连接（${connectionId}）。`);
      return {
        status: "provider_logout_required",
        provider: "openai",
        externalSessionStatus: connection.externalSessionStatus,
        instructions: "Use OpenCode `auth logout` to remove the provider-owned session.",
      };
    },

    async listExecutors() {
      return structuredClone(executors);
    },

    async listBindings() {
      return structuredClone(bindings);
    },

    async upsertBinding(input) {
      const parsed = BindingInputSchema.parse(input);
      if (!connections.some((c) => c.connectionId === parsed.connectionId)) {
        throw new Error(`未知的连接（${parsed.connectionId}）。`);
      }
      if (!executors.some((e) => e.executorId === parsed.executorId)) {
        throw new Error(`未知的执行器（${parsed.executorId}）。`);
      }
      const saved: Binding = {
        bindingId: parsed.bindingId,
        name: parsed.name,
        executorId: parsed.executorId,
        connectionId: parsed.connectionId,
        modelId: parsed.modelId,
        enabled: parsed.enabled,
      };
      bindings = [
        ...bindings.filter((b) => b.bindingId !== saved.bindingId),
        saved,
      ];
      generated.delete(saved.bindingId);
      return structuredClone(
        bindings.find((b) => b.bindingId === saved.bindingId) as Binding,
      );
    },

    async deleteBinding(bindingId) {
      if (!bindings.some((b) => b.bindingId === bindingId)) {
        throw new Error(`Binding not found: ${bindingId}`);
      }
      bindings = bindings.filter((b) => b.bindingId !== bindingId);
    },
  };
}

let defaultClient: ModelControlClient | undefined;

export function getDefaultModelControlClient(): ModelControlClient {
  if (!defaultClient) {
    const useMock =
      import.meta.env.MODE === "test" ||
      import.meta.env.VITE_MODEL_CONTROL_MODE === "mock";
    defaultClient = useMock
      ? createMockModelControlClient()
      : createHttpModelControlClient(
          import.meta.env.VITE_MODEL_CONTROL_API_BASE ||
            DEFAULT_MODEL_CONTROL_API_BASE,
        );
  }
  return defaultClient;
}

export function resetDefaultModelControlClientForTests() {
  defaultClient = createMockModelControlClient();
}
