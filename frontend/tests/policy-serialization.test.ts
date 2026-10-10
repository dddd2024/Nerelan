import { describe, it, expect } from "vitest";
import {
  serializePolicy,
  deserializePolicy,
  roundTripPolicy,
} from "@/lib/policy-serializer";
import { profileToPolicy } from "@/lib/profile-mapper";
import type { PolicyContract } from "@/types";

describe("policy serialization", () => {
  it("canonical encoding uses sorted compact JSON and preserves Unicode", () => {
    const policy = profileToPolicy("ASK_FOR_APPROVAL");
    policy.resourceAccess.filesystem.allowedPaths = ["前端/设置.tsx"];
    const json = serializePolicy(policy);
    expect(json).toContain("前端/设置.tsx");
    expect(json).not.toContain("\n");
    expect(json.startsWith('{"autonomousWindow":')).toBe(true);
  });
  it("rejects extra fields on serialization and deserialization", () => {
    const policy = { ...profileToPolicy("ASK_FOR_APPROVAL"), inventedAuthority: true };
    expect(() => serializePolicy(policy)).toThrow();
    expect(() => deserializePolicy(JSON.stringify(policy))).toThrow();
  });
  it("round-trips an OWNER_CONTROL policy", () => {
    const policy = profileToPolicy("OWNER_CONTROL");
    const back = roundTripPolicy(policy);
    expect(back).toEqual(policy);
  });

  it("produces canonical (stable) JSON for identical policies", () => {
    const policy = profileToPolicy("CONTROLLER_REVIEW");
    const a = serializePolicy(policy);
    const b = serializePolicy(policy);
    expect(a).toBe(b);
  });

  it("deserialize throws on invalid JSON", () => {
    expect(() => deserializePolicy("{not json")).toThrow();
  });

  it("serializes the CUSTOM example policy without loss", () => {
    const policy = profileToPolicy("CUSTOM");
    const json = serializePolicy(policy);
    const back = deserializePolicy(json) as PolicyContract;
    expect(back.publicationCapabilities).toEqual(policy.publicationCapabilities);
  });
});
