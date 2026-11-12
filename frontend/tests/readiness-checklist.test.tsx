import { act, cleanup, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { focusManager, onlineManager } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ReadinessChecklist } from "@/components/readiness-checklist";
import * as client from "@/lib/platform-client";
import type { DoctorCheck, DoctorReport } from "@/lib/platform-client";
import { renderWithProviders } from "./test-utils";

function check(id: string, state: DoctorCheck["state"], required = true, component = "test"): DoctorCheck {
  return { id, state, required, component, summary: "raw message", reason_code: "test", remediation_id: "none" };
}
function report(checks: DoctorCheck[]): DoctorReport {
  return { schema_version: 1, state: "UNKNOWN", checks };
}
const missing = report([check("connection_binding_readiness", "BLOCKED")]);

describe("readiness checklist", () => {
  beforeEach(() => { sessionStorage.clear(); });
  afterEach(() => { cleanup(); vi.useRealTimers(); vi.restoreAllMocks(); });

  it("shows a missing item with its settings link and ready items", async () => {
    vi.spyOn(client, "fetchDoctorReport").mockResolvedValue(report([
      ...missing.checks, check("task_api_reachable", "READY"),
    ]));
    renderWithProviders(<ReadinessChecklist />);
    const section = await screen.findByRole("region", { name: "准备情况" });
    expect(within(section).getByText("模型连接与绑定")).toBeInTheDocument();
    expect(within(section).getByText("需要处理")).toBeInTheDocument();
    expect(within(section).getByText("就绪")).toBeInTheDocument();
    expect(within(section).getByRole("link", { name: "前往设置" })).toHaveAttribute("href", "/settings/models");
  });

  it("hides when all required checks are ready", async () => {
    const fetch = vi.spyOn(client, "fetchDoctorReport").mockResolvedValue(report([
      check("task_api_reachable", "READY"), check("optional", "BLOCKED", false),
    ]));
    renderWithProviders(<ReadinessChecklist />);
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
    expect(fetch).toHaveBeenCalledOnce();
    expect(screen.queryByRole("region", { name: "准备情况" })).not.toBeInTheDocument();
  });

  it("one usable tool hides the checklist despite unavailable alternatives", async () => {
    vi.spyOn(client, "fetchDoctorReport").mockResolvedValue(report([
      check("executor_readiness", "READY"),
      check("executor_codex", "READY", false, "executor_tool"),
      check("executor_opencode", "BLOCKED", false, "executor_tool"),
    ]));
    renderWithProviders(<ReadinessChecklist />);
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
    expect(screen.queryByRole("region", { name: "准备情况" })).not.toBeInTheDocument();
  });

  it("lists unavailable alternatives as optional when another required check is missing", async () => {
    vi.spyOn(client, "fetchDoctorReport").mockResolvedValue(report([
      ...missing.checks, check("executor_readiness", "READY"),
      check("executor_codex", "READY", false, "executor_tool"),
      check("executor_opencode", "BLOCKED", false, "executor_tool"),
    ]));
    renderWithProviders(<ReadinessChecklist />);
    const tool = (await screen.findByText("OpenCode 工具")).closest("li")!;
    expect(within(tool).getByText("可选")).toBeInTheDocument();
  });

  it("shows the tool requirement when none is usable", async () => {
    vi.spyOn(client, "fetchDoctorReport").mockResolvedValue(report([
      check("executor_readiness", "BLOCKED"),
      check("executor_codex", "BLOCKED", false, "executor_tool"),
    ]));
    renderWithProviders(<ReadinessChecklist />);
    expect(await screen.findByText("Agent 工具（至少一个）")).toBeInTheDocument();
    expect(screen.getByText("需要处理")).toBeInTheDocument();
  });

  it("refetches on request and hides after recovery", async () => {
    const fetch = vi.spyOn(client, "fetchDoctorReport").mockResolvedValueOnce(missing)
      .mockResolvedValue(report([check("connection_binding_readiness", "READY")]));
    renderWithProviders(<ReadinessChecklist />);
    await userEvent.click(await screen.findByRole("button", { name: "重新检查" }));
    await waitFor(() => expect(screen.queryByRole("region", { name: "准备情况" })).not.toBeInTheDocument());
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("keeps dismissal across remounts in the session", async () => {
    const fetch = vi.spyOn(client, "fetchDoctorReport").mockResolvedValue(missing);
    const view = renderWithProviders(<ReadinessChecklist />);
    await userEvent.click(await screen.findByRole("button", { name: "本次不再显示" }));
    view.unmount();
    renderWithProviders(<ReadinessChecklist />);
    expect(screen.queryByRole("region", { name: "准备情况" })).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledOnce();
  });

  it("allows retry after a request failure", async () => {
    vi.spyOn(client, "fetchDoctorReport").mockRejectedValueOnce(new Error("offline")).mockResolvedValue(missing);
    renderWithProviders(<ReadinessChecklist />);
    expect(await screen.findByRole("alert")).toHaveTextContent("无法检查准备情况");
    await userEvent.click(screen.getByRole("button", { name: "重新检查" }));
    expect(await screen.findByText("模型连接与绑定")).toBeInTheDocument();
  });

  it("does not poll or refetch on focus and reconnect", async () => {
    vi.useFakeTimers();
    const fetch = vi.spyOn(client, "fetchDoctorReport").mockResolvedValue(missing);
    renderWithProviders(<ReadinessChecklist />);
    await act(async () => { await vi.advanceTimersByTimeAsync(10); });
    await act(async () => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
      onlineManager.setOnline(false);
      onlineManager.setOnline(true);
      await vi.advanceTimersByTimeAsync(60_000);
    });
    expect(fetch).toHaveBeenCalledOnce();
  });
});
