import { describe, expect, it } from "vitest";
import { explainStartError } from "@/lib/start-errors";

describe("explainStartError maps known start and activation codes", () => {
  it("gives a Chinese explanation and advice for owner_selection_confirmation_unavailable", () => {
    const e = explainStartError("owner_selection_confirmation_unavailable");
    expect(e.known).toBe(true);
    expect(e.zh).toContain("终端");
    expect(e.advice.length).toBeGreaterThan(0);
    expect(e.code).toBe("owner_selection_confirmation_unavailable");
    expect(e.params).toEqual([]);
  });

  it("handles owner_window_* codes", () => {
    const e1 = explainStartError("owner_window_scope_changed");
    expect(e1.known).toBe(true);
    expect(e1.zh).toContain("范围");
    expect(e1.code).toBe("owner_window_scope_changed");

    const e2 = explainStartError("owner_window_preset_invalid");
    expect(e2.known).toBe(true);
    expect(e2.zh).toContain("预设");

    const e3 = explainStartError("owner_window_confirmation_expired");
    expect(e3.known).toBe(true);
    expect(e3.zh).toContain("过期");
  });

  it("handles quick_start_* codes", () => {
    const e = explainStartError("quick_start_text_invalid");
    expect(e.known).toBe(true);
    expect(e.zh).toContain("文本");
  });

  it("handles native_owner_* codes", () => {
    const e = explainStartError("native_owner_identity_unavailable_or_changed");
    expect(e.known).toBe(true);
    expect(e.zh).toContain("身份");
  });

  it("handles active_window_* codes", () => {
    const e = explainStartError("active_window_repository_conflict");
    expect(e.known).toBe(true);
    expect(e.zh).toContain("仓库");
  });

  it("handles delegated_policy_* codes", () => {
    const e = explainStartError("delegated_policy_authority_unavailable");
    expect(e.known).toBe(true);
    expect(e.zh).toContain("授权");
  });

  it("handles repository_workspace_unconfigured", () => {
    const e = explainStartError("repository_workspace_unconfigured");
    expect(e.known).toBe(true);
    expect(e.zh).toContain("工作区");
  });

  it("handles invalid_autonomy_policy_identity", () => {
    const e = explainStartError("invalid_autonomy_policy_identity");
    expect(e.known).toBe(true);
    expect(e.zh).toContain("身份");
  });
});

describe("explainStartError parses parameterized codes", () => {
  it("extracts numeric parameter from quick_start_issue_not_open", () => {
    const e = explainStartError("quick_start_issue_not_open:1350");
    expect(e.known).toBe(true);
    expect(e.code).toBe("quick_start_issue_not_open");
    expect(e.params).toEqual(["1350"]);
    expect(e.zh).toContain("1350");
    expect(e.zh).toContain("关闭");
  });

  it("extracts parameter from quick_start_issue_unreadable", () => {
    const e = explainStartError("quick_start_issue_unreadable:42");
    expect(e.known).toBe(true);
    expect(e.code).toBe("quick_start_issue_unreadable");
    expect(e.params).toEqual(["42"]);
  });

  it("extracts goal_id from owner_window_goal_not_admissible", () => {
    const e = explainStartError("owner_window_goal_not_admissible:goal-abc123");
    expect(e.known).toBe(true);
    expect(e.code).toBe("owner_window_goal_not_admissible");
    expect(e.params).toEqual(["goal-abc123"]);
    expect(e.zh).toContain("goal-abc123");
  });

  it("handles multiple parameters in owner_window_task_unbound", () => {
    const e = explainStartError("owner_window_task_unbound:goal-1:task-99");
    expect(e.known).toBe(true);
    expect(e.code).toBe("owner_window_task_unbound");
    expect(e.params).toEqual(["goal-1", "task-99"]);
    expect(e.zh).toContain("goal-1");
    expect(e.zh).toContain("task-99");
  });

  it("handles details parameter in owner_window_task_unroutable", () => {
    const e = explainStartError("owner_window_task_unroutable:no_binding");
    expect(e.known).toBe(true);
    expect(e.params).toEqual(["no_binding"]);
  });
});

describe("explainStartError passes unknown codes through as-is", () => {
  it("preserves a completely unknown code", () => {
    const e = explainStartError("some_unknown_code_xyz");
    expect(e.known).toBe(false);
    expect(e.code).toBe("some_unknown_code_xyz");
    expect(e.params).toEqual([]);
    expect(e.zh).toBe("some_unknown_code_xyz");
    expect(e.advice.length).toBeGreaterThan(0);
  });

  it("preserves unknown codes with parameters", () => {
    const e = explainStartError("unknown_family:param1:param2");
    expect(e.known).toBe(false);
    expect(e.code).toBe("unknown_family");
    expect(e.params).toEqual(["param1", "param2"]);
    expect(e.zh).toBe("unknown_family:param1:param2");
  });

  it("handles empty string gracefully", () => {
    const e = explainStartError("");
    expect(e.known).toBe(false);
    expect(e.code).toBe("");
    expect(e.params).toEqual([]);
    expect(e.zh).toBe("");
  });
});
