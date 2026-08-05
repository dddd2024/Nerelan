import { describe, it, expect } from "vitest";
import { summarizePolicy } from "@/lib/policy-summary";
import { profileToPolicy } from "@/lib/profile-mapper";
import type { PolicyContract } from "@/types";

describe("authorization summary", () => {
  it("mentions the repository", () => {
    const policy = profileToPolicy("OWNER_CONTROL");
    const summary = summarizePolicy(policy);
    expect(summary).toContain(policy.repository);
  });

  it("states production deployment is not allowed for OWNER_CONTROL", () => {
    const policy = profileToPolicy("OWNER_CONTROL");
    const summary = summarizePolicy(policy);
    expect(summary).toContain("Production deployment is not allowed");
  });

  it("states production deployment is allowed for CUSTOM", () => {
    const policy = profileToPolicy("CUSTOM");
    const summary = summarizePolicy(policy);
    expect(summary).toContain("Production deployment is allowed");
  });

  it("includes the window expiry time when enabled", () => {
    const policy: PolicyContract = profileToPolicy("OWNER_CONTROL");
    policy.autonomousWindow.enabled = true;
    policy.autonomousWindow.expiresAt = "2026-08-05T08:00:00Z";
    const summary = summarizePolicy(policy);
    expect(summary).toMatch(/Until/);
  });
});
