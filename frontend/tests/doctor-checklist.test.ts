import { describe, expect, it } from "vitest";
import { doctorChecklist } from "@/lib/doctor-checklist";
import type { DoctorCheck, DoctorReport } from "@/lib/platform-client";

function check(id: string, state: DoctorCheck["state"] = "READY", required = true, component = "test"): DoctorCheck {
  return { id, state, required, component, summary: "raw message", reason_code: "test", remediation_id: "none" };
}

function report(checks: DoctorCheck[]): DoctorReport {
  return { schema_version: 1, state: "UNKNOWN", checks };
}

describe("doctor checklist mapping", () => {
  it("maps every real check id into Chinese guidance", () => {
    const ids = ["task_api_reachable", "task_store_readable", "task_store_storage_path",
      "runtime_status_available", "repository_workspace_readiness", "executor_readiness",
      "connection_binding_readiness", "desktop_lifecycle_readiness", "executor_opencode",
      "executor_codex", "executor_claude_code"];
    for (const id of ids) {
      const item = doctorChecklist(report([check(id, "BLOCKED")])).items[0];
      expect(item.name).not.toBe(id);
      expect(item.message).toMatch(/请/);
      expect(item.state).toBe("需要处理");
    }
  });

  it("preserves unknown ids and messages", () => {
    expect(doctorChecklist(report([check("future_check", "UNKNOWN")])).items[0])
      .toMatchObject({ name: "future_check", message: "raw message", blocking: true });
  });

  it("does not block on optional failures and does block on required uncertainty", () => {
    expect(doctorChecklist(report([check("optional", "BLOCKED", false)])).needsAttention).toBe(false);
    for (const state of ["BLOCKED", "UNKNOWN", "DEGRADED"] as const) {
      expect(doctorChecklist(report([check("task_store_readable", state)])).needsAttention).toBe(true);
    }
  });

  it("one usable tool satisfies the group and makes other tools optional", () => {
    const result = doctorChecklist(report([
      check("executor_readiness", "BLOCKED"),
      check("executor_codex", "READY", true, "executor_tool"),
      check("executor_opencode", "BLOCKED", true, "executor_tool"),
    ]));
    expect(result.needsAttention).toBe(false);
    expect(result.items.map((item) => item.state)).toEqual(["就绪", "就绪", "可选"]);
  });
});
