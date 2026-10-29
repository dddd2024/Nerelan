import { describe, expect, it } from "vitest";
import { linkedGoalId, taskProjectHref, taskProjectName } from "@/lib/task-project";

describe("project display uses real repository fields", () => {
  it("makes unknown ownership explicit", () => {
    expect(taskProjectName(undefined)).toBe("未归属");
    expect(taskProjectHref(undefined)).toBeNull();
  });

  it("keeps different repository identities distinct", () => {
    expect(taskProjectHref("team/alpha")).toBe("/tasks?repository=team%2Falpha");
    expect(taskProjectHref("other/alpha")).toBe("/tasks?repository=other%2Falpha");
  });

  it("only renders bounded direct Goal IDs", () => {
    expect(linkedGoalId("goal_19-abc")).toBe("goal_19-abc");
    expect(linkedGoalId("")).toBeUndefined();
    expect(linkedGoalId("uncertain goal title")).toBeUndefined();
  });
});
