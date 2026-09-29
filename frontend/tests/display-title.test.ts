import { describe, expect, it } from "vitest";
import { DISPLAY_TITLE_MAX, displayObjective, displayTitle } from "@/lib/display-title";

const PLATFORM_TITLE =
  "[前端密度修复：短标题派生与目标原文折叠] T001 前端密度修复：短标题派生与目标原文折叠\n\n按 objective 要求修改并跑通 typecheck 与 vitest";

describe("displayTitle", () => {
  it("prefers the human-authored bracket goal title over the generated tail", () => {
    expect(displayTitle(PLATFORM_TITLE)).toBe("前端密度修复：短标题派生与目标原文折叠");
  });

  it("strips the English plan boilerplate and the step marker", () => {
    expect(displayTitle("T001 Analyze, implement, and verify the goal: add structured logging")).toBe(
      "add structured logging",
    );
    expect(displayTitle("T012 Analyze, implement, and verify the goal add structured logging")).toBe(
      "add structured logging",
    );
  });

  it("strips the localized plan boilerplate", () => {
    expect(displayTitle("T003 分析、实现并验证目标：修复侧栏红点语义")).toBe("修复侧栏红点语义");
  });

  it("never returns an empty title when only boilerplate was present", () => {
    expect(displayTitle("T001 Analyze, implement, and verify the goal")).toBe(
      "T001 Analyze, implement, and verify the goal",
    );
  });

  it("collapses whitespace and keeps only the first paragraph", () => {
    expect(displayTitle("修复   token   泄漏\n\n第二段不应出现")).toBe("修复 token 泄漏");
  });

  it("bounds long titles at a boundary and marks the truncation", () => {
    const long = `[${"字".repeat(200)}] T001 尾段`;
    const result = displayTitle(long);
    expect(result.length).toBeLessThanOrEqual(DISPLAY_TITLE_MAX + 1);
    expect(result.endsWith("…")).toBe(true);
  });

  it("tolerates empty and missing input", () => {
    expect(displayTitle("")).toBe("");
    expect(displayTitle(null)).toBe("");
    expect(displayTitle(undefined)).toBe("");
  });
});

describe("displayObjective", () => {
  it("removes the bracket wrapper but keeps the objective body for disclosure", () => {
    expect(displayObjective(PLATFORM_TITLE)).toBe(
      "T001 前端密度修复：短标题派生与目标原文折叠\n\n按 objective 要求修改并跑通 typecheck 与 vitest",
    );
  });

  it("returns an empty string for missing input", () => {
    expect(displayObjective(undefined)).toBe("");
  });
});
