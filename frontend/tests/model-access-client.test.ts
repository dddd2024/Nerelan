import { describe, expect, it, vi } from "vitest";
import {
  createHttpModelControlClient,
  createMockModelControlClient,
} from "@/lib/model-control-client";
import {
  ConnectionInputSchema,
  BindingInputSchema,
  connectionVerificationCapability,
} from "@/schemas/model-access";

const DUMMY_KEY = "test-secret-should-not-appear";

describe("connection client contract", () => {
  it("serializes api_key on upsert and never returns the raw key", async () => {
    const client = createMockModelControlClient([]);
    const saved = await client.upsertConnection({
      connectionId: "test-conn",
      name: "测试连接",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      apiKey: DUMMY_KEY,
    });

    expect(saved.secretStatus).toBe("session");
    expect(saved).not.toHaveProperty("apiKey");
    expect(saved).not.toHaveProperty("api_key");
    const json = JSON.stringify(saved);
    expect(json).not.toContain(DUMMY_KEY);
    expect(await client.listConnections()).toContainEqual(saved);
  });

  it("public Connection normalization contains secretStatus and externalSessionStatus", async () => {
    const client = createMockModelControlClient([]);
    const saved = await client.upsertConnection({
      connectionId: "env-conn",
      name: "环境变量连接",
      provider: "openai-compatible",
      baseUrl: "https://api.example.com/v1",
      authMethod: "api_key",
      enabled: true,
      apiKeyEnv: "TEST_API_KEY",
    });

    expect(saved.secretStatus).toBe("environment");
    expect(saved.externalSessionStatus).toBe("not_applicable");
    expect(saved.provider).toBe("openai-compatible");
    expect(saved.baseUrl).toBe("https://api.example.com/v1");
    expect(saved.enabled).toBe(true);
  });

  it("rejects connection identifiers and URLs that do not match the schema", () => {
    expect(() =>
      ConnectionInputSchema.parse({
        connectionId: "Invalid ID",
        name: "x",
        provider: "litellm-proxy",
        baseUrl: "not-a-url",
        authMethod: "api_key",
        enabled: true,
      }),
    ).toThrow();
  });

  it("accepts backend-safe generic provider identifiers", () => {
    const provider = "custom.provider_v2";
    expect(() =>
      ConnectionInputSchema.parse({
        connectionId: "generic-conn",
        name: "Generic Provider",
        provider,
        baseUrl: "https://api.example.com/v1",
        authMethod: "external_cli_session",
        enabled: true,
      }),
    ).not.toThrow();
  });

  it("rejects unsafe provider identifiers", () => {
    const invalidProviders = [
      "SenseTime",
      "Invalid Provider",
      "a/b",
      "https://token:secret@api.example.com",
    ];
    for (const provider of invalidProviders) {
      expect(() =>
        ConnectionInputSchema.parse({
          connectionId: "bad-provider-conn",
          name: "Bad Provider",
          provider,
          baseUrl: "https://api.example.com/v1",
          authMethod: "external_cli_session",
          enabled: true,
        }),
      ).toThrow();
    }
  });

  it("keeps secret status from environment variable reference", async () => {
    const client = createMockModelControlClient([]);
    await client.upsertConnection({
      connectionId: "env-only",
      name: "仅环境变量",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      apiKeyEnv: "MY_PROVIDER_KEY",
    });
    const listed = await client.listConnections();
    expect(listed[0].secretStatus).toBe("environment");
    expect(listed[0]).not.toHaveProperty("apiKey");
    expect(listed[0]).not.toHaveProperty("apiKeyEnv");
  });
});

describe("executor client contract", () => {
  it("normalizes executor public data with camelCase fields", async () => {
    const client = createMockModelControlClient();
    const executors = await client.listExecutors();
    expect(executors.length).toBeGreaterThan(0);
    const opencode = executors.find((e) => e.executorId === "opencode");
    expect(opencode).toBeDefined();
    expect(opencode?.name).toBe("OpenCode");
    expect(opencode?.operational).toBe(true);
    expect(Array.isArray(opencode?.capabilities)).toBe(true);
    expect(opencode).not.toHaveProperty("executor_id");
  });
});

describe("binding client contract", () => {
  it("serializes binding with only references, no credential fields", async () => {
    const client = createMockModelControlClient();
    const bindings = await client.listBindings();
    expect(bindings.length).toBeGreaterThan(0);
    const binding = bindings[0];
    expect(binding.bindingId).toBeDefined();
    expect(binding.executorId).toBeDefined();
    expect(binding.connectionId).toBeDefined();
    expect(binding.modelId).toBeDefined();
    expect(binding).not.toHaveProperty("apiKey");
    expect(binding).not.toHaveProperty("api_key");
    expect(binding).not.toHaveProperty("password");
    expect(binding).not.toHaveProperty("secret");
    expect(binding).not.toHaveProperty("token");
    expect(binding).not.toHaveProperty("credential");
    expect(JSON.stringify(binding)).not.toContain(DUMMY_KEY);
  });

  it("rejects binding input with schema validation", () => {
    expect(() =>
      BindingInputSchema.parse({
        bindingId: "Invalid",
        name: "",
        executorId: "",
        connectionId: "",
        modelId: "",
        enabled: true,
      }),
    ).toThrow();
  });

  it("rejects binding with unknown connection reference", async () => {
    const client = createMockModelControlClient();
    await expect(
      client.upsertBinding({
        bindingId: "bad-binding",
        name: "孤立绑定",
        executorId: "opencode",
        connectionId: "nonexistent-connection",
        modelId: "fake-model",
        enabled: true,
      }),
    ).rejects.toThrow();
  });
});

describe("model control client backward compatibility", () => {
  it("still supports profile operations", async () => {
    const client = createMockModelControlClient([]);
    const saved = await client.upsertProfile({
      id: "compat-profile",
      name: "兼容配置",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      modelId: "test-model",
      executor: "openhands",
      enabled: true,
      isDefault: true,
    });
    expect(saved.id).toBe("compat-profile");
    expect(saved.secretStatus).toBe("missing");
    expect(await client.listProfiles()).toHaveLength(1);
  });
});

describe("connection probe client contract", () => {
  it("mock testConnection returns deterministic sanitized result", async () => {
    const client = createMockModelControlClient([]);
    await client.upsertConnection({
      connectionId: "probe-conn",
      name: "Probe Test",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      apiKey: DUMMY_KEY,
    });
    const result = await client.testConnection("probe-conn");
    expect(result.ok).toBe(true);
    expect(result.status).toBe("connected");
    expect(result.latencyMs).toBe(18);
    expect(JSON.stringify(result)).not.toContain(DUMMY_KEY);
    expect(result).toHaveProperty("message");
  });

  it("mock testConnection disabled connection returns disabled", async () => {
    const client = createMockModelControlClient([]);
    await client.upsertConnection({
      connectionId: "disabled-conn",
      name: "Disabled",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: false,
    });
    const result = await client.testConnection("disabled-conn");
    expect(result.ok).toBe(false);
    expect(result.status).toBe("disabled");
    expect(result.latencyMs).toBe(null);
  });

  it("mock testConnection missing secret returns credential_missing", async () => {
    const client = createMockModelControlClient([]);
    await client.upsertConnection({
      connectionId: "no-key-conn",
      name: "No Key",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
    });
    const result = await client.testConnection("no-key-conn");
    expect(result.ok).toBe(false);
    expect(result.status).toBe("credential_missing");
    expect(result.latencyMs).toBe(null);
  });

  it("mock no-auth connection is probeable without a secret", async () => {
    const client = createMockModelControlClient([]);
    const saved = await client.upsertConnection({
      connectionId: "no-auth-conn",
      name: "No Auth",
      provider: "openai-compatible",
      baseUrl: "https://api.example.com/v1",
      authMethod: "none",
      enabled: true,
    });

    expect(saved.secretStatus).toBe("not_applicable");
    expect(saved.externalSessionStatus).toBe("not_applicable");
    expect(connectionVerificationCapability(saved)).toBe("supported");

    const result = await client.testConnection(saved.connectionId);
    expect(result.ok).toBe(true);
    expect(result.status).toBe("connected");
  });

  it.each(["account_login", "external_cli_session"] as const)(
    "mock %s connection is executor-managed and never fabricates probe success",
    async (authMethod) => {
      const client = createMockModelControlClient([]);
      const saved = await client.upsertConnection({
        connectionId: `${authMethod.replaceAll("_", "-")}-conn`,
        name: authMethod,
        provider: "custom.provider",
        baseUrl: "https://api.example.com/v1",
        authMethod,
        enabled: true,
      });

      expect(saved.secretStatus).toBe("not_applicable");
      expect(saved.externalSessionStatus).toBe("executor_managed");
      expect(connectionVerificationCapability(saved)).toBe("executor_managed");

      const result = await client.testConnection(saved.connectionId);
      expect(result.ok).toBe(false);
      expect(result.status).toBe("unsupported_auth_method");
    },
  );

  it("typed capability distinguishes missing credential and disabled state", async () => {
    const client = createMockModelControlClient([]);
    const missing = await client.upsertConnection({
      connectionId: "missing-capability",
      name: "Missing",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
    });
    const disabled = await client.upsertConnection({
      connectionId: "disabled-capability",
      name: "Disabled",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "none",
      enabled: false,
    });

    expect(connectionVerificationCapability(missing)).toBe("credential_missing");
    expect(connectionVerificationCapability(disabled)).toBe("connection_disabled");
  });

  it("switching mock connection away from api_key removes public secret applicability", async () => {
    const client = createMockModelControlClient([]);
    await client.upsertConnection({
      connectionId: "switch-auth",
      name: "Switch Auth",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "api_key",
      enabled: true,
      apiKey: DUMMY_KEY,
    });
    const saved = await client.upsertConnection({
      connectionId: "switch-auth",
      name: "Switch Auth",
      provider: "litellm-proxy",
      baseUrl: "http://localhost:4000/v1",
      authMethod: "none",
      enabled: true,
    });

    expect(saved.secretStatus).toBe("not_applicable");
    expect(JSON.stringify(saved)).not.toContain(DUMMY_KEY);
  });

  it("mock testConnection not found throws", async () => {
    const client = createMockModelControlClient([]);
    await expect(client.testConnection("nonexistent")).rejects.toThrow();
  });

  it("http client sends POST to saved connection endpoint with empty body", async () => {
    let capturedUrl: string | undefined;
    let capturedBody: string | undefined;
    let capturedMethod: string | undefined;

    const mockFetch = vi.fn(async (url, opts) => {
      capturedUrl = String(url);
      capturedMethod = (opts as { method?: string })?.method;
      capturedBody = String((opts as { body?: string })?.body ?? "");
      return {
        ok: true,
        text: async () =>
          JSON.stringify({
            ok: true,
            status: "connected",
            message: "Connection succeeded",
            latency_ms: 22,
          }),
      };
    });
    vi.stubGlobal("fetch", mockFetch);

    try {
      const client = createHttpModelControlClient("/api");
      await client.testConnection("my-conn");

      expect(capturedMethod).toBe("POST");
      expect(capturedUrl).toBe("/api/connections/my-conn/test");
      expect(capturedBody).toBe("{}");
      const parsed = JSON.parse(capturedBody!);
      expect(parsed).not.toHaveProperty("api_key");
      expect(parsed).not.toHaveProperty("apiKey");
      expect(parsed).not.toHaveProperty("base_url");
      expect(parsed).not.toHaveProperty("baseUrl");
      expect(parsed).not.toHaveProperty("provider");
      expect(parsed).not.toHaveProperty("auth_method");
      expect(parsed).not.toHaveProperty("authMethod");
      expect(parsed).not.toHaveProperty("model_id");
      expect(parsed).not.toHaveProperty("modelId");
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("executor-managed external session regressions", () => {
  it("http GET /connections snake_case parses executor_managed sensetime provider", async () => {
    const snakePayload = {
      connection_id: "sensetime-ext",
      name: "SenseTime External",
      provider: "sensetime",
      base_url: "https://api.sensenova.cn/v1",
      auth_method: "external_cli_session",
      enabled: true,
      secret_status: "not_applicable",
      external_session_status: "executor_managed",
    };

    const mockFetch = vi.fn(async () => ({
      ok: true,
      text: async () => JSON.stringify([snakePayload]),
    }));
    vi.stubGlobal("fetch", mockFetch);

    try {
      const client = createHttpModelControlClient("/api");
      const connections = await client.listConnections();
      expect(connections.length).toBe(1);
      expect(connections[0].provider).toBe("sensetime");
      expect(connections[0].authMethod).toBe("external_cli_session");
      expect(connections[0].externalSessionStatus).toBe("executor_managed");
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("accepts backend-safe generic provider identifier via upsert input", () => {
    expect(() =>
      ConnectionInputSchema.parse({
        connectionId: "sensetime-conn",
        name: "SenseTime",
        provider: "sensetime",
        baseUrl: "https://api.sensenova.cn/v1",
        authMethod: "external_cli_session",
        enabled: true,
      }),
    ).not.toThrow();
  });

  it("rejects invalid provider identifiers including empty, uppercase, slash, url, and over-80", () => {
    const invalid = [
      "SenseTime",
      "Invalid Provider",
      "a/b",
      "https://token:secret@example.com",
      "a".repeat(81),
    ];
    for (const provider of invalid) {
      expect(() =>
        ConnectionInputSchema.parse({
          connectionId: "bad-conn",
          name: "Bad",
          provider,
          baseUrl: "https://api.example.com/v1",
          authMethod: "external_cli_session",
          enabled: true,
        }),
      ).toThrow();
    }
  });

  it("http upsert request body never contains derived secret or external session status", async () => {
    let capturedBodyStr: string | undefined;
    const mockFetch = vi.fn(async () => ({
      ok: true,
      text: async () =>
        JSON.stringify({
          connection_id: "sensetime-conn",
          name: "SenseTime",
          provider: "sensetime",
          base_url: "https://api.sensenova.cn/v1",
          auth_method: "external_cli_session",
          enabled: true,
          secret_status: "not_applicable",
          external_session_status: "executor_managed",
        }),
    }));
    vi.stubGlobal("fetch", mockFetch);

    try {
      const client = createHttpModelControlClient("/api");
      await client.upsertConnection({
        connectionId: "sensetime-conn",
        name: "SenseTime",
        provider: "sensetime",
        baseUrl: "https://api.sensenova.cn/v1",
        authMethod: "external_cli_session",
        enabled: true,
      });
      const call = mockFetch.mock.calls[0] as unknown[];
      capturedBodyStr = String((call[1] as { body?: string })?.body ?? "");
      const parsed = JSON.parse(capturedBodyStr!);
      expect(parsed).not.toHaveProperty("secret_status");
      expect(parsed).not.toHaveProperty("secretStatus");
      expect(parsed).not.toHaveProperty("external_session_status");
      expect(parsed).not.toHaveProperty("externalSessionStatus");
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
