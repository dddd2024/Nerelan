import { describe, expect, it } from "vitest";
import {
  createMockModelControlClient,
} from "@/lib/model-control-client";
import {
  ConnectionInputSchema,
  BindingInputSchema,
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
