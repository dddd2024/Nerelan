import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { dispatchBlockLabel, explainPaidGateway, runtimeExplanation, runtimeMessage, runtimeTitle } from "@/lib/runtime-labels";

describe("runtime labels", () => {
  it("explains in Chinese why a paid subscription is not dispatched through a gateway", () => {
    expect(runtimeMessage("binding_resolution_failed:paid_subscription_gateway").label).toBe("付费订阅不能经网关派发");
    for (const cause of ["provider:codex", "group_member:claude", "group_membership_unknown", "auto_membership_unknown",
      "model_family:gpt", "model_unknown", "settings_unreadable"]) {
      expect(dispatchBlockLabel(cause)).toMatch(/^不派发：.+付费订阅只能由官方工具执行。$/);
      expect(dispatchBlockLabel(cause)).not.toContain(cause);
    }
    expect(dispatchBlockLabel("provider:codex")).toContain("codex");
    expect(explainPaidGateway("m: paid_subscription_gateway")).toBe("m: 付费订阅不能经网关派发");
  });

  it.each([
    "review_not_independent", "usage_budget_reached", "usage_reservation_overrun",
    "executor_dispatch_failed", "MODEL_UNAVAILABLE", "api_error_429", "quota_exhausted",
    "timeout", "executor_nonzero", "deterministic_validation_failure", "no_runnable_model",
    "window_expired", "owner_stopped", "owner_revoked", "renew_until_reached",
    "receipt_persistence_failed", "usage_unknown", "usage_unknown_budget_reached",
  ])("explains the known code %s and what to do next", (code) => {
    const message = runtimeMessage(code);
    expect(message.label).toMatch(/[\u4e00-\u9fff]/);
    expect(message.label).not.toBe(code);
    expect(message.nextStep).toMatch(/^.+。$/);
    expect(runtimeExplanation(code)).toBe(`${message.label}：${message.nextStep}`);
    expect(runtimeTitle(code)).toContain(code);
    expect(runtimeTitle(code)).toContain(message.nextStep);
  });

  it("uses the prefix for unknown colon-suffixed codes and retains all diagnostic detail", () => {
    const code = "MODEL_UNAVAILABLE:not_allowed_for_user_type";
    expect(runtimeMessage(code)).toEqual(runtimeMessage("MODEL_UNAVAILABLE"));
    expect(runtimeTitle(code)).toContain(code);
    expect(runtimeMessage("timeout:executor:123")).toEqual(runtimeMessage("timeout"));
  });

  it.each(["new_failure", "new_failure:detail", "", "toString", "__proto__", "TIMEOUT"])(
    "preserves the unknown code %s unchanged", (code) => {
      expect(runtimeMessage(code)).toEqual({ label: code, nextStep: "" });
      expect(runtimeExplanation(code)).toBe(code);
      expect(runtimeTitle(code)).toBe(code);
    },
  );

  it("covers every goal and task status declared by the backend", () => {
    for (const [file, pattern] of [
      ["control_store.py", /GOAL_STATES = frozenset\(\s*\{([^}]+)\}/],
      ["run_store.py", /TASK_STATUS_ORDER = \(([^)]+)\)/],
    ] as const) {
      // Vitest runs from `frontend/`; the backend sources are one level up.
      const source = readFileSync(resolve(process.cwd(), "..", "reverse_agent", "platform_v1", file), "utf8");
      const declaration = source.match(pattern)?.[1];
      expect(declaration).toBeTruthy();
      const codes = Array.from(declaration!.matchAll(/"([A-Z_]+)"/g), (match) => match[1]);
      expect(codes.length).toBeGreaterThan(0);
      for (const code of codes) {
        expect(runtimeMessage(code).label, code).not.toBe(code);
        expect(runtimeMessage(code).nextStep, code).toMatch(/。$/);
      }
    }
  });
});
