import {
  ModelConnectionResultSchema,
  ModelProfileInputSchema,
  ModelProfileSchema,
  type ModelConnectionResult,
  type ModelProfile,
  type ModelProfileInput,
} from "@/schemas/model-profile";

export interface ModelControlClient {
  listProfiles(): Promise<ModelProfile[]>;
  upsertProfile(input: ModelProfileInput): Promise<ModelProfile>;
  deleteProfile(profileId: string): Promise<void>;
  setDefaultProfile(profileId: string): Promise<ModelProfile[]>;
  testProfile(profileId: string, apiKey?: string): Promise<ModelConnectionResult>;
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

function serializeInput(input: ModelProfileInput) {
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
  const profilesUrl = `${apiBase.replace(/\/$/, "")}/model-profiles`;
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
          body: JSON.stringify(serializeInput(parsed)),
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
  };
}

export function createMockModelControlClient(
  initialProfiles: ModelProfile[] = DEFAULT_MOCK_PROFILES,
): ModelControlClient {
  let profiles = initialProfiles.map((profile) =>
    ModelProfileSchema.parse(structuredClone(profile)),
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
