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
  ExecutorSchema,
  BindingInputSchema,
  BindingSchema,
  type Connection,
  type ConnectionInput,
  type Executor,
  type Binding,
  type BindingInput,
  type ConnectionProbeResult,
} from "@/schemas/model-access";

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
  return ConnectionSchema.parse({
    connectionId: raw.connectionId ?? raw.connection_id,
    name: raw.name,
    provider: raw.provider,
    baseUrl: raw.baseUrl ?? raw.base_url,
    authMethod: raw.authMethod ?? raw.auth_method,
    enabled: raw.enabled,
    secretStatus: raw.secretStatus ?? raw.secret_status,
    externalSessionStatus: raw.externalSessionStatus ?? raw.external_session_status,
  });
}

function normalizeExecutor(value: unknown): Executor {
  const raw = value as Record<string, unknown>;
  return ExecutorSchema.parse({
    executorId: raw.executorId ?? raw.executor_id,
    name: raw.name,
    operational: raw.operational,
    capabilities: Array.isArray(raw.capabilities) ? raw.capabilities : [],
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
  apiBase = "/api",
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
      const saved: Connection = {
        connectionId: parsed.connectionId,
        name: parsed.name,
        provider: parsed.provider,
        baseUrl: parsed.baseUrl,
        authMethod: parsed.authMethod,
        enabled: parsed.enabled,
        secretStatus: parsed.apiKey
          ? "session"
          : parsed.apiKeyEnv
            ? "environment"
            : (connections.find((c) => c.connectionId === parsed.connectionId)
                ?.secretStatus ?? "missing"),
        externalSessionStatus: "not_applicable",
      };
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
        throw new Error(`Connection not found: ${connectionId}`);
      }
      const usedByBinding = bindings.some(
        (b) => b.connectionId === connectionId,
      );
      if (usedByBinding) {
        throw new Error("connection is referenced by binding");
      }
      connections = connections.filter((c) => c.connectionId !== connectionId);
    },

    async testConnection(connectionId) {
      const connection = connections.find((c) => c.connectionId === connectionId);
      if (!connection) {
        throw new Error(`Connection not found: ${connectionId}`);
      }
      if (!connection.enabled) {
        return {
          ok: false,
          status: "disabled",
          message: "连接已禁用",
          latencyMs: null,
        };
      }
      if (connection.secretStatus === "missing") {
        return {
          ok: false,
          status: "credential_missing",
          message: "API Key 未配置",
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

    async listExecutors() {
      return structuredClone(executors);
    },

    async listBindings() {
      return structuredClone(bindings);
    },

    async upsertBinding(input) {
      const parsed = BindingInputSchema.parse(input);
      if (!connections.some((c) => c.connectionId === parsed.connectionId)) {
        throw new Error(`unknown connection_id: ${parsed.connectionId}`);
      }
      if (!executors.some((e) => e.executorId === parsed.executorId)) {
        throw new Error(`unknown executor_id: ${parsed.executorId}`);
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
          import.meta.env.VITE_MODEL_CONTROL_API_BASE || "/api",
        );
  }
  return defaultClient;
}

export function resetDefaultModelControlClientForTests() {
  defaultClient = createMockModelControlClient();
}
