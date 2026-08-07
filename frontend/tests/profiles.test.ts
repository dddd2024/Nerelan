import { describe, it, expect } from "vitest";
import {
  profileToPolicy,
  allProfiles,
} from "@/lib/profile-mapper";
import type { PermissionMode, PolicyContract } from "@/types";

const MODES: PermissionMode[] = [
  "ASK_FOR_APPROVAL",
  "CONTROLLER_REVIEW",
  "OWNER_CONTROL",
  "CUSTOM",
];

describe("permission profiles", () => {
  it("maps each of the 4 modes to a policy", () => {
    for (const mode of MODES) {
      const policy = profileToPolicy(mode);
      expect(policy.mode).toBe(mode);
      expect(policy.repository.length).toBeGreaterThan(0);
    }
  });

  it("returns independent deep clones (mutating one does not affect defaults)", () => {
    const a = profileToPolicy("OWNER_CONTROL");
    a.githubCapabilities.push("push_main");
    const b = profileToPolicy("OWNER_CONTROL");
    expect(b.githubCapabilities).not.toContain("push_main");
  });

  it("allProfiles returns one entry per mode", () => {
    const all = allProfiles();
    expect(Object.keys(all).sort()).toEqual([...MODES].sort());
  });

  it("ASK_FOR_APPROVAL does not include merge_pr", () => {
    const policy: PolicyContract = profileToPolicy("ASK_FOR_APPROVAL");
    expect(policy.githubCapabilities).not.toContain("merge_pr");
  });

  it("OWNER_CONTROL includes merge_pr but not push_main", () => {
    const policy = profileToPolicy("OWNER_CONTROL");
    expect(policy.githubCapabilities).toContain("merge_pr");
    expect(policy.githubCapabilities).not.toContain("push_main");
  });
});
