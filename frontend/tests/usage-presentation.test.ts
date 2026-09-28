import { describe, expect, it } from "vitest";
import { deriveUsagePresentation } from "@/lib/usage-presentation";
import type { PlatformUsageSummary, PlatformUsageRole } from "@/lib/platform-client";

function observedRole(overrides: Partial<PlatformUsageRole> = {}): PlatformUsageRole {
  return {
    role: "coder",
    input_units: 1000,
    output_units: 200,
    reasoning_units: 0,
    cache_read_units: 300,
    cache_write_units: 0,
    cost_micro_units: 5000,
    observation_count: 1,
    unknown_observation_count: 0,
    provenance_ids: ["o"],
    ...overrides,
  };
}

function summary(overrides: Partial<PlatformUsageSummary> = {}): PlatformUsageSummary {
  return {
    status: "OBSERVED",
    input_units: 1000,
    output_units: 200,
    reasoning_units: 0,
    cache_read_units: 300,
    cache_write_units: 0,
    cost_micro_units: 5000,
    total_token_units: 1500,
    observation_count: 1,
    unknown_observation_count: 0,
    provenance_ids: ["o"],
    per_role: [],
    ...overrides,
  };
}

describe("deriveUsagePresentation", () => {
  it("classifies fully observed usage with non-zero totals as observed", () => {
    const result = deriveUsagePresentation(summary());
    expect(result.kind).toBe("observed");
    expect(result.show_totals).toBe(true);
    expect(result.total_token_units).toBe(1500);
    expect(result.cost_micro_units).toBe(5000);
    expect(result.observation_count).toBe(1);
    expect(result.unknown_observation_count).toBe(0);
  });

  it("preserves fully observed zero without claiming it is unknown", () => {
    const result = deriveUsagePresentation(
      summary({
        status: "OBSERVED",
        input_units: 0,
        output_units: 0,
        reasoning_units: 0,
        cache_read_units: 0,
        cache_write_units: 0,
        cost_micro_units: 0,
        total_token_units: 0,
        observation_count: 2,
        unknown_observation_count: 0,
        provenance_ids: ["a", "b"],
      }),
    );
    expect(result.kind).toBe("observed-zero");
    expect(result.show_totals).toBe(true);
    expect(result.total_token_units).toBe(0);
  });

  it("classifies no observations as no-observations and hides totals", () => {
    const result = deriveUsagePresentation(
      summary({
        status: "USAGE_UNKNOWN",
        input_units: 0,
        output_units: 0,
        reasoning_units: 0,
        cache_read_units: 0,
        cache_write_units: 0,
        cost_micro_units: 0,
        total_token_units: 0,
        observation_count: 0,
        unknown_observation_count: 0,
        provenance_ids: [],
      }),
    );
    expect(result.kind).toBe("no-observations");
    expect(result.show_totals).toBe(false);
  });

  it("classifies all-unknown observations as all-unknown and hides totals", () => {
    const result = deriveUsagePresentation(
      summary({
        status: "USAGE_UNKNOWN",
        input_units: 0,
        output_units: 0,
        reasoning_units: 0,
        cache_read_units: 0,
        cache_write_units: 0,
        cost_micro_units: 0,
        total_token_units: 0,
        observation_count: 1,
        unknown_observation_count: 1,
        provenance_ids: ["u"],
      }),
    );
    expect(result.kind).toBe("all-unknown");
    expect(result.show_totals).toBe(false);
    expect(result.observation_count).toBe(1);
    expect(result.unknown_observation_count).toBe(1);
  });

  it("classifies mixed observed and unknown as partial and shows observed-only totals", () => {
    const result = deriveUsagePresentation(
      summary({
        status: "USAGE_UNKNOWN",
        total_token_units: 1500,
        cost_micro_units: 5000,
        observation_count: 3,
        unknown_observation_count: 1,
        provenance_ids: ["o1", "o2", "u"],
      }),
    );
    expect(result.kind).toBe("partial");
    expect(result.show_totals).toBe(true);
    expect(result.total_token_units).toBe(1500);
    expect(result.observation_count - result.unknown_observation_count).toBe(2);
  });

  it("derives no-observations from counts even when an inconsistent fixture reports OBSERVED", () => {
    // The backend contract is: observation_count == 0 always means USAGE_UNKNOWN.
    // Some legacy fixtures report status OBSERVED with zero observations, which is
    // internally impossible. The presentation must still tell the truth.
    const result = deriveUsagePresentation(
      summary({
        status: "OBSERVED",
        observation_count: 0,
        unknown_observation_count: 0,
        total_token_units: 0,
        provenance_ids: [],
      }),
    );
    expect(result.kind).toBe("no-observations");
    expect(result.show_totals).toBe(false);
  });

  it("applies consistent per-role treatment for observed, partial, all-unknown and observed-zero roles", () => {
    const result = deriveUsagePresentation(
      summary({
        status: "USAGE_UNKNOWN",
        total_token_units: 1500,
        cost_micro_units: 5000,
        observation_count: 4,
        unknown_observation_count: 2,
        provenance_ids: ["o1", "o2", "u1", "u2"],
        per_role: [
          observedRole({ role: "planner", observation_count: 2, unknown_observation_count: 0, provenance_ids: ["o1", "o2"] }),
          observedRole({ role: "coder", input_units: 0, output_units: 0, reasoning_units: 0, cache_read_units: 0, cache_write_units: 0, cost_micro_units: 0, observation_count: 2, unknown_observation_count: 2, provenance_ids: ["u1", "u2"] }),
          observedRole({ role: "reviewer", observation_count: 2, unknown_observation_count: 1, provenance_ids: ["o1", "u1"] }),
        ],
      }),
    );

    const byRole = Object.fromEntries(result.per_role.map((role) => [role.role, role]));
    expect(byRole.planner.kind).toBe("observed");
    expect(byRole.planner.total_token_units).toBe(1500);
    expect(byRole.coder.kind).toBe("all-unknown");
    expect(byRole.coder.total_token_units).toBe(0);
    expect(byRole.reviewer.kind).toBe("partial");
    expect(byRole.reviewer.unknown_observation_count).toBe(1);
    expect(byRole.reviewer.observation_count).toBe(2);
  });

  it("marks a fully observed role with all-zero metrics as observed-zero", () => {
    const result = deriveUsagePresentation(
      summary({
        per_role: [
          observedRole({
            role: "planner",
            input_units: 0,
            output_units: 0,
            reasoning_units: 0,
            cache_read_units: 0,
            cache_write_units: 0,
            cost_micro_units: 0,
            observation_count: 1,
            unknown_observation_count: 0,
            provenance_ids: ["z"],
          }),
        ],
      }),
    );
    expect(result.per_role[0].kind).toBe("observed-zero");
    expect(result.per_role[0].total_token_units).toBe(0);
  });

  it("never labels a role with zero observations as observed-zero", () => {
    // A role that has produced no observation records has an absence of data,
    // not an observed value of zero. It must be "no-observations".
    const result = deriveUsagePresentation(
      summary({
        observation_count: 2,
        unknown_observation_count: 0,
        per_role: [
          observedRole({
            role: "reviewer",
            input_units: 0,
            output_units: 0,
            reasoning_units: 0,
            cache_read_units: 0,
            cache_write_units: 0,
            cost_micro_units: 0,
            observation_count: 0,
            unknown_observation_count: 0,
            provenance_ids: [],
          }),
        ],
      }),
    );
    expect(result.per_role[0].kind).toBe("no-observations");
    expect(result.per_role[0].kind).not.toBe("observed-zero");
    expect(result.per_role[0].observation_count).toBe(0);
  });
});
