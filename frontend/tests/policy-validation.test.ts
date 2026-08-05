import { describe, it, expect } from "vitest";
import { validatePolicy } from "@/schemas/policy";
import { profileToPolicy } from "@/lib/profile-mapper";
import type { PolicyContract } from "@/types";

function ownerPolicy(): PolicyContract {
  return profileToPolicy("OWNER_CONTROL");
}

describe("policy validation", () => {
  it("accepts the built-in OWNER_CONTROL profile", () => {
    const result = validatePolicy(ownerPolicy());
    expect(result.success).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("rejects merge_pr without allowedRepositories", () => {
    const policy = ownerPolicy();
    policy.mergePolicy.allowedRepositories = [];
    const result = validatePolicy(policy);
    expect(result.success).toBe(false);
    expect(result.errors.some((e) => e.includes("allowedRepositories"))).toBe(true);
  });

  it("rejects deploy_production without allowedEnvironment", () => {
    const policy = profileToPolicy("CUSTOM");
    policy.publicationPolicy.allowedEnvironment = [];
    policy.publicationPolicy.rollbackStrategy = undefined;
    const result = validatePolicy(policy);
    expect(result.success).toBe(false);
    expect(
      result.errors.some((e) => e.includes("deploy_production")),
    ).toBe(true);
  });

  it("rejects an expired autonomous window", () => {
    const policy = ownerPolicy();
    policy.autonomousWindow.enabled = true;
    policy.autonomousWindow.expiresAt = "2020-01-01T00:00:00Z";
    const result = validatePolicy(policy);
    expect(result.success).toBe(false);
    expect(
      result.errors.some((e) => e.includes("future")),
    ).toBe(true);
  });

  it("rejects zero (non-positive) budgets", () => {
    const policy = ownerPolicy();
    policy.budgets.maxMergesToMain = 0;
    const result = validatePolicy(policy);
    expect(result.success).toBe(false);
  });

  it("rejects raw_values secrets access", () => {
    const policy = ownerPolicy();
    policy.resourceAccess.secrets.access = "raw_values";
    const result = validatePolicy(policy);
    expect(result.success).toBe(false);
    expect(result.errors.some((e) => e.includes("raw"))).toBe(true);
  });

  it("push_main is not implied by merge_pr (independent)", () => {
    const policy = ownerPolicy();
    // merge_pr on, push_main off must still be valid (no cross-implication error).
    policy.githubCapabilities = policy.githubCapabilities.filter(
      (c) => c !== "push_main",
    );
    policy.githubCapabilities.push("merge_pr");
    const result = validatePolicy(policy);
    expect(result.success).toBe(true);
  });
});
