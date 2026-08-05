import { describe, it, expect } from "vitest";
import {
  serializePolicy,
  deserializePolicy,
  roundTripPolicy,
} from "@/lib/policy-serializer";
import { profileToPolicy } from "@/lib/profile-mapper";
import type { PolicyContract } from "@/types";

describe("policy serialization", () => {
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
