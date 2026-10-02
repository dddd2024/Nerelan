import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createMockModelControlClient,
  createHttpModelControlClient,
  type ModelControlClient,
} from "@/lib/model-control-client";
import { ModelProfileInputSchema } from "@/schemas/model-profile";
import { ModelSelectionInputSchema } from "@/schemas/model-access";

const profileInput = {
  id: "coding-default",
  name: "默认代码模型",
  provider: "litellm-proxy" as const,
  baseUrl: "http://localhost:4000/v1",
  modelId: "coding-default",
  executor: "openhands" as const,
  enabled: true,
  isDefault: true,
};

async function save(client: ModelControlClient, overrides = {}) {
  return client.upsertProfile({ ...profileInput, ...overrides });
}

describe("model profile contract", () => {
  it("rejects invalid profile identifiers and URLs", () => {
    expect(() =>
      ModelProfileInputSchema.parse({
        ...profileInput,
        id: "Invalid ID",
        baseUrl: "not-a-url",
      }),
    ).toThrow();
  });

  it("never returns an API key after saving a profile", async () => {
    const client = createMockModelControlClient([]);
    const saved = await client.upsertProfile({
      ...profileInput,
      apiKey: "top-secret-value",
    });

    expect(saved).not.toHaveProperty("apiKey");
    expect(saved.secretStatus).toBe("session");
    expect(await client.listProfiles()).toEqual([saved]);
    expect(JSON.stringify(await client.listProfiles())).not.toContain(
      "top-secret-value",
    );
  });

  it("keeps exactly one default profile", async () => {
    const client = createMockModelControlClient([]);
    await save(client, { id: "alpha", name: "Alpha" });
    await save(client, { id: "beta", name: "Beta", isDefault: true });

    const profiles = await client.listProfiles();
    expect(profiles.filter((profile) => profile.isDefault)).toHaveLength(1);
    expect(profiles.find((profile) => profile.isDefault)?.id).toBe("beta");
  });

  it("promotes another enabled profile when the default is deleted", async () => {
    const client = createMockModelControlClient([]);
    await save(client, { id: "alpha", name: "Alpha" });
    await save(client, {
      id: "beta",
      name: "Beta",
      isDefault: false,
    });

    await client.deleteProfile("alpha");

    expect((await client.listProfiles())[0]).toMatchObject({
      id: "beta",
      isDefault: true,
    });
  });

  it("returns a deterministic connection result in mock mode", async () => {
    const client = createMockModelControlClient([]);
    await save(client);

    await expect(client.testProfile("coding-default")).resolves.toMatchObject({
      ok: true,
      status: "connected",
    });
  });
});

describe("saved catalog and selection preview contracts", () => {
  afterEach(() => vi.unstubAllGlobals());

  const connectionInput = {
    connectionId: "catalog-connection", name: "Catalog connection", provider: "openrouter",
    baseUrl: "https://catalog.example.test/v1", authMethod: "none" as const, enabled: true,
    upstreamProviderId: null, protocolFamily: "openai", executorProviderId: "openrouter",
  };

  it("preserves all three provider identity axes in HTTP read and save while projecting out credential fields", async () => {
    const response = { connection_id: connectionInput.connectionId, name: connectionInput.name,
      provider: connectionInput.provider, base_url: connectionInput.baseUrl, auth_method: "none", enabled: true,
      upstream_provider_id: null, protocol_family: "openai", executor_provider_id: "openrouter",
      credential_configured: false, secret_status: "not_applicable", external_session_status: "not_applicable",
      api_key: "synthetic-secret-must-not-return", api_key_env: "SYNTHETIC_PRIVATE_ENV" };
    const fetchMock = vi.fn(async (_url: string, _init?: RequestInit) => new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const saved = await createHttpModelControlClient().upsertConnection(connectionInput);
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toMatchObject({
      upstream_provider_id: null, protocol_family: "openai", executor_provider_id: "openrouter",
    });
    expect(saved).toMatchObject({ upstreamProviderId: null, protocolFamily: "openai", executorProviderId: "openrouter" });
    expect(JSON.stringify(saved)).not.toMatch(/synthetic-secret|SYNTHETIC_PRIVATE_ENV|api_key/);
  });

  it("uses the real models and versioned binding endpoints with exactly the server CAS fields", async () => {
    const publicBinding = { binding_id: "selected-model", name: "Selected", executor_id: "opencode",
      connection_id: "catalog-connection", model_id: "openrouter/anthropic/claude-test", enabled: false };
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) => new Response(JSON.stringify(
      init?.body === "{}" ? {
        ok: true, status: "advertised", message: "提供方公布，尚未验证", latency_ms: 4,
        models: ["anthropic/claude-test"], connection_id: "catalog-connection",
        configuration_revision: "opaque-generation", catalog_revision: "opaque-catalog",
        observed_at: "2026-10-02T00:00:00Z", source: "provider_advertised", entitlement: "not_observed",
        model_records: [{ model_id: "anthropic/claude-test", display_name: "Claude Test", owned_by: null }],
      } : { binding: publicBinding, created: false, reused_manual: true, configuration_revision: "opaque-generation",
        catalog_revision: "opaque-catalog", source: "manual", advertised_model_id: "anthropic/claude-test",
        availability: "advertised_unverified" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const client = createHttpModelControlClient();
    const catalog = await client.listConnectionModels("catalog-connection");
    expect(fetchMock.mock.calls[0]?.[0]).toBe("http://127.0.0.1:8765/api/connections/catalog-connection/models");
    expect(catalog).toMatchObject({ configurationRevision: "opaque-generation", catalogRevision: "opaque-catalog",
      modelRecords: [{ modelId: "anthropic/claude-test", displayName: "Claude Test", ownedBy: null }], entitlement: "not_observed" });
    const result = await client.selectCatalogBinding({ connectionId: "catalog-connection", executorId: "opencode",
      modelId: catalog.models[0], configurationRevision: catalog.configurationRevision!, catalogRevision: catalog.catalogRevision! });
    expect(fetchMock.mock.calls[1]?.[0]).toBe("http://127.0.0.1:8765/api/connections/catalog-connection/models/bindings");
    expect(JSON.parse(String(fetchMock.mock.calls[1]?.[1]?.body))).toEqual({
      configuration_revision: "opaque-generation", catalog_revision: "opaque-catalog", executor_id: "opencode", model_id: "anthropic/claude-test",
    });
    expect(result).toMatchObject({ reusedManual: true, binding: { enabled: false, modelId: "openrouter/anthropic/claude-test" } });
  });

  it("preserves a server-redacted empty model ID and unknown evidence without sending permission flags", async () => {
    const candidate = { binding_ref: "manual-invalid", connection_id: "catalog-connection", executor_id: "opencode",
      model_id: "", configuration_revision: null, catalog_revision: null, source: "manual", eligible: false,
      reason_codes: ["model_invalid"], explanation: "模型标识无法安全展示，请检查手动绑定。", availability: "not_observed",
      underlying_identity: null, underlying_identity_status: "not_observed", cost: null, quality: null };
    const fetchMock = vi.fn(async (_url: string, _init?: RequestInit) => new Response(JSON.stringify({ preview_only: true,
      status: "manual_blocked", message: "尚未通过执行检查", policy_id: "catalog-preview-v1", recommended: null,
      candidates: [candidate], evidence_unknowns: ["cost", "quality", "task_success", "underlying_model_identity"] }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const result = await createHttpModelControlClient().recommendModelSelection({ selectionMode: "manual", manualBindingRef: "manual-invalid" });
    expect(result.candidates[0]).toMatchObject({ modelId: "", underlyingIdentity: null, eligible: false, cost: null, quality: null });
    expect(fetchMock.mock.calls[0]?.[0]).toBe("http://127.0.0.1:8765/api/model-selections/recommend");
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toEqual({ selection_mode: "manual", manual_binding_ref: "manual-invalid" });
    expect(ModelSelectionInputSchema.safeParse({ selectionMode: "automatic", requiredCapabilities: Array(17).fill("workspace_execution") }).success).toBe(false);
    expect(ModelSelectionInputSchema.safeParse({ selectionMode: "automatic", preferredBindingRefs: Array(33).fill("manual-invalid") }).success).toBe(false);
  });

  it("preserves a disabled manual tuple, invalidates secret replacement, and reuses at most one generated tuple per generation", async () => {
    const client = createMockModelControlClient();
    await client.upsertConnection(connectionInput);
    let catalog = await client.listConnectionModels(connectionInput.connectionId);
    const select = () => client.selectCatalogBinding({ connectionId: connectionInput.connectionId, executorId: "opencode",
      modelId: "mock-model-a", configurationRevision: catalog.configurationRevision!, catalogRevision: catalog.catalogRevision! });
    const first = await select();
    expect((await select()).binding.bindingId).toBe(first.binding.bindingId);
    await client.upsertBinding({ bindingId: "protected-manual", name: "Protected", executorId: "opencode", connectionId: connectionInput.connectionId,
      modelId: "openrouter/mock-model-a", enabled: false });
    expect(await select()).toMatchObject({ reusedManual: true, created: false, binding: { bindingId: "protected-manual", enabled: false } });
    await client.upsertConnection({ ...connectionInput, name: "Renamed" });
    expect((await client.listConnectionModels(connectionInput.connectionId)).configurationRevision).toBe(catalog.configurationRevision);
    await client.upsertConnection({ ...connectionInput, authMethod: "api_key", apiKey: "synthetic-key-one" });
    await expect(select()).rejects.toThrow(/过期/);
    catalog = await client.listConnectionModels(connectionInput.connectionId);
    await client.upsertConnection({ ...connectionInput, authMethod: "api_key", apiKey: "synthetic-key-two" });
    await expect(select()).rejects.toThrow(/过期/);
    expect(JSON.stringify(await client.listConnections())).not.toMatch(/synthetic-key-one|synthetic-key-two/);
  });

  it("returns finite unsupported and credential missing states instead of a mock success catalog", async () => {
    const client = createMockModelControlClient();
    await client.upsertConnection({ ...connectionInput, authMethod: "api_key" });
    expect(await client.listConnectionModels(connectionInput.connectionId)).toMatchObject({ ok: false, status: "credential_missing", models: [], catalogRevision: null });
    await client.upsertConnection({ ...connectionInput, authMethod: "external_cli_session" });
    expect(await client.listConnectionModels(connectionInput.connectionId)).toMatchObject({ ok: false, status: "unsupported_auth_method", models: [] });
  });
});
