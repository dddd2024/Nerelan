import { describe, expect, it } from "vitest";
import {
  createMockModelControlClient,
  type ModelControlClient,
} from "@/lib/model-control-client";
import { ModelProfileInputSchema } from "@/schemas/model-profile";

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
