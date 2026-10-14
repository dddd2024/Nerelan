import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import { ResourceOverview } from "@/components/resource-overview";
import {
  createHttpModelControlClient,
  getDefaultModelControlClient,
  resetDefaultModelControlClientForTests,
} from "@/lib/model-control-client";
import { normalizeResourceOverview } from "@/lib/resources";
import { renderWithProviders } from "./test-utils";

const PAYLOAD = {
  resources: [
    {
      connection_id: "chatgpt-account",
      name: "ChatGPT",
      enabled: true,
      credential: { kind: "subscription", configured: true, status: "available" },
      credential_owner: "codex-cli",
      executors: [{ executor_id: "codex", ready: true }],
      bindings: [{ binding_id: "chatgpt-gpt", model_id: "gpt-6.1-sol", executor_id: "codex", usable: true,
                   tokens: { input: 26473, cache_read: 33024, cache_write: 0, output: 291, tasks: 2 },
                   equivalent_cost: { state: "ESTIMATED", usd: 0.0592, price_as_of: "2026-10-14" } }],
      token_usage: { input: 26473, cache_read: 33024, cache_write: 0, output: 291, reasoning: 0, tasks_with_tokens: 1 },
      equivalent_cost: { state: "ESTIMATED", usd: 0.0021, price_as_of: "2026-10-14", cli_reported_usd: 0.0019 },
      quota: {
        state: "OBSERVED", source: "codex_session_log", observed_at: "2026-10-14T04:44:18Z", plan: "plus",
        windows: [
          { window: "five_hour", used_percent: 49, resets_at: "2026-10-14T09:05:11Z", reset_passed: false },
          { window: "weekly", used_percent: 40, resets_at: "2026-10-13T06:07:52Z", reset_passed: true },
        ],
      },
    },
    {
      connection_id: "sense",
      name: "SenseNova",
      enabled: true,
      credential: { kind: "api_key", configured: true, status: "stored" },
      credential_owner: "nerelan",
      executors: [],
      bindings: [],
      token_usage: {},
      equivalent_cost: { state: "PARTIAL", usd: 16.5664, unpriced: ["vendor_unknown"] },
      quota: { state: "UNKNOWN", reason: "api_key_has_no_subscription_window", windows: [] },
    },
  ],
  summary: {
    usable_bindings: 1, quota_known: 1,
    tokens: { input: 26473, cache_read: 33024, cache_write: 0, output: 291 },
    equivalent_cost: { state: "PARTIAL", usd: 16.6256, price_source: "https://models.dev/api.json",
                       price_as_of: "2026-10-14" },
  },
};

describe("resource overview", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("normalizes the API without inventing numbers", () => {
    const overview = normalizeResourceOverview({
      resources: [{ connection_id: "x", quota: { state: "OBSERVED", windows: [{ window: "weekly", used_percent: 140 }] },
                    equivalent_cost: { state: "WHATEVER", usd: "1" } }],
    });
    const [resource] = overview.resources;
    expect(resource.quota.windows[0].usedPercent).toBeNull();
    expect(resource.equivalentCost).toMatchObject({ state: "UNKNOWN", usd: null });
    expect(resource.tokens).toEqual({ input: 0, cacheRead: 0, cacheWrite: 0, output: 0, reasoning: 0 });
    expect(normalizeResourceOverview(null).resources).toEqual([]);
  });

  it("shows quota windows, reset times, token counts and labelled list-price cost", async () => {
    vi.spyOn(getDefaultModelControlClient(), "getResources").mockResolvedValue(normalizeResourceOverview(PAYLOAD));
    renderWithProviders(<ResourceOverview />);

    const chatgpt = await screen.findByTestId("resource-chatgpt-account");
    expect(within(chatgpt).getByText("订阅 · Codex CLI 登录")).toBeInTheDocument();
    const fiveHour = within(chatgpt).getByTestId("quota-window-five_hour");
    expect(fiveHour).toHaveTextContent("已用 49%");
    expect(within(fiveHour).getByRole("meter")).toHaveAttribute("aria-valuenow", "49");
    expect(fiveHour).toHaveTextContent("重置");
    // A passed reset is not shown as 40% (stale) nor 0% (invented): it is unknown.
    const weekly = within(chatgpt).getByTestId("quota-window-weekly");
    expect(weekly).toHaveTextContent("已过重置时间，当前用量未知");
    expect(within(weekly).queryByRole("meter")).toBeNull();
    expect(chatgpt).toHaveTextContent("计划 plus");
    expect(within(chatgpt).getByTestId("resource-cost")).toHaveTextContent("< $0.01");
    expect(within(chatgpt).getByTestId("resource-cli-cost")).toHaveTextContent("Claude Code 自报 < $0.01");
    expect(chatgpt).toHaveTextContent("来自 Nerelan 的 1 个任务");

    const sense = screen.getByTestId("resource-sense");
    expect(within(sense).getByTestId("quota-unknown")).toHaveTextContent("API Key 按量计费，没有订阅额度窗口");
    expect(within(sense).getByTestId("resource-cost")).toHaveTextContent("$16.57（部分）");
    expect(within(fiveHour).getByRole("meter")).toHaveAttribute("aria-valuetext", "49%");

    const summary = screen.getByTestId("resource-summary");
    expect(summary).toHaveTextContent("等价成本 $16.63（部分）");
    expect(summary).toHaveTextContent("models.dev，2026-10-14");
  });

  it("labels each window by its basis: estimate with range, status only, usage only", async () => {
    const payload = {
      resources: [{
        connection_id: "claude-account", name: "Claude", enabled: true,
        credential: { kind: "subscription", configured: true }, credential_owner: "claude-code-cli",
        executors: [], bindings: [], token_usage: {},
        quota: {
          state: "OBSERVED", source: "claude_session_log",
          windows: [
            { window: "five_hour", basis: "estimated", used_percent: 89.1, used_percent_range: [65, 100],
              capacity_units: { samples: 9 }, resets_at: "2026-10-14T09:06:58Z", resets_at_estimated: true },
            { window: "weekly", basis: "official_status", status: "allowed_warning", availability: "near_limit",
              resets_at: "2026-10-20T06:00:00Z" },
            { window: "seven_day_opus", basis: "unknown", used_units: 18.65 },
          ],
          limit_hits: [{ at: "2026-10-13T13:07:16Z", source: "claude_session_log" },
                       { at: "2026-10-13T10:36:33Z", source: "claude_session_log" }],
        },
      }],
      summary: {
        quota_guard: [
          { at: "2026-10-14T05:10:00Z", role: "coder", binding_id: "claude-opus", decision: "switch",
            reason: "predicted_insufficient", window: "five_hour", switched_to: "chatgpt-gpt" },
          { at: "2026-10-14T05:11:00Z", role: null, binding_id: "claude-sonnet", decision: "warn",
            reason: "limit_reached:no_alternative", switched_to: null },
        ],
      },
    };
    vi.spyOn(getDefaultModelControlClient(), "getResources").mockResolvedValue(normalizeResourceOverview(payload));
    renderWithProviders(<ResourceOverview />);

    const five = await screen.findByTestId("quota-window-five_hour");
    expect(five).toHaveAttribute("data-basis", "estimated");
    expect(five).toHaveTextContent("预计已用约 89%（65–100%）");
    expect(five).toHaveTextContent("约 ");
    expect(five).toHaveTextContent("按本机历史 9 次触顶/用量估算");
    expect(within(five).getByTestId("meter-range")).toBeInTheDocument();
    const weekly = screen.getByTestId("quota-window-weekly");
    expect(within(weekly).getByTestId("quota-availability")).toHaveTextContent("接近上限");
    expect(within(weekly).queryByRole("meter")).toBeNull();  // no invented percentage
    expect(screen.getByTestId("quota-window-seven_day_opus")).toHaveTextContent("本窗口已用约 $18.65，上限未知");
    expect(screen.getByTestId("quota-limit-hits")).toHaveTextContent("最近 8 天触顶 2 次");
    const log = screen.getByTestId("quota-guard-log");
    expect(log).toHaveTextContent("coder：claude-opus → chatgpt-gpt（预计余量不足以完成下一项任务）");
    expect(log).toHaveTextContent("claude-sonnet 继续运行（未找到不降级的替代）（已触顶）");
  });

  it("reports a load failure instead of an empty overview", async () => {
    vi.spyOn(getDefaultModelControlClient(), "getResources").mockRejectedValue(new Error("模型控制服务不可用"));
    renderWithProviders(<ResourceOverview />);
    expect(await screen.findByTestId("resource-overview-error")).toHaveTextContent("模型控制服务不可用");
  });

  it("http client reads GET /resources and normalizes it", async () => {
    const mockFetch = vi.fn(async () => ({ ok: true, text: async () => JSON.stringify(PAYLOAD) }));
    vi.stubGlobal("fetch", mockFetch);
    try {
      const overview = await createHttpModelControlClient("/api").getResources();
      expect((mockFetch.mock.calls[0] as unknown[])[0]).toBe("/api/resources");
      expect(overview.resources[0].quota.windows[0]).toMatchObject({ window: "five_hour", usedPercent: 49 });
      expect(overview.quotaKnown).toBe(1);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("mock client lists its connections with unknown quota and no cost", async () => {
    const overview = await getDefaultModelControlClient().getResources();
    expect(overview.resources.length).toBeGreaterThan(0);
    expect(overview.resources.every((r) => r.quota.state === "UNKNOWN" && r.equivalentCost === null)).toBe(true);
  });
});
