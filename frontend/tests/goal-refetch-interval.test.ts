import { describe, expect, it } from "vitest";
import { goalRefetchInterval } from "@/hooks/use-platform";

describe("goalRefetchInterval", () => {
  it("polls a running goal quickly", () => {
    expect(goalRefetchInterval("RUNNING")).toBe(2_500);
  });

  it("keeps polling a stopped goal, which a retry from elsewhere can resume", () => {
    for (const status of ["BLOCKED", "PLANNED", "APPROVED", undefined]) {
      expect(goalRefetchInterval(status)).toBe(10_000);
    }
  });

  it("stops polling a finished goal", () => {
    for (const status of ["COMPLETED", "SUCCEEDED", "CANCELLED", "FAILED", "ARCHIVED"]) {
      expect(goalRefetchInterval(status)).toBe(false);
    }
  });
});
