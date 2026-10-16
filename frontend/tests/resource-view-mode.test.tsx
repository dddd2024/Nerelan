import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, within } from "@testing-library/react";
import { ResourceOverview } from "@/components/resource-overview";
import {
  createHttpModelControlClient,
  getDefaultModelControlClient,
  resetDefaultModelControlClientForTests,
} from "@/lib/model-control-client";
import { normalizeResourceOverview, type ResourceViewMode } from "@/lib/resources";
import { renderWithProviders } from "./test-utils";

const LEGACY_PAYLOAD = {
  resources: [
    {
      connection_id: "sense",
      name: "SenseNova",
      enabled: true,
      credential: { kind: "api_key", configured: true },
      credential_owner: "nerelan",
      executors: [],
      bindings: [],
      token_usage: { input: 100, output: 20, tasks_with_tokens: 1 },
      equivalent_cost: { state: "ESTIMATED", usd: 0.01, price_as_of: "2026-10-14" },
      quota: { state: "UNKNOWN", reason: "api_key_has_no_subscription_window", windows: [] },
    },
  ],
  summary: {
    usable_bindings: 1,
    quota_known: 0,
    tokens: { input: 100, output: 20 },
    equivalent_cost: { state: "ESTIMATED", usd: 0.01, price_as_of: "2026-10-14" },
  },
};

const HYBRID_PAYLOAD = {
  ...LEGACY_PAYLOAD,
  view_mode: "hybrid",
  external_sources: {
    magpie: {
      status: "available",
      version: "magpie-cli 0.4",
      models: [
        { model_id: "gpt-6.1-sol", provider: "openai", display_name: "GPT-6.1 Sol", reasoning: true, context_window: 200000 },
      ],
      accounts: [
        {
          provider: "openai",
          kind: "subscription",
          plan: "plus",
          account_ref: "acct_abc123",
          state: "ok",
          observed_at: "2026-10-14T04:44:18Z",
          provenance: "EXTERNAL_MAGPIE",
          source_version: "magpie-cli 0.4",
          windows: [{ name: "five_hour", used_percent: 49, remaining_percent: 51, resets_at: "2026-10-14T09:05:11Z", unlimited: false }],
        },
        {
          provider: "anthropic",
          kind: "subscription",
          plan: null,
          account_ref: "acct_xyz",
          state: "UNKNOWN",
          observed_at: null,
          provenance: "EXTERNAL_MAGPIE",
          source_version: null,
          windows: [{ name: "weekly", used_percent: 0, remaining_percent: 0, resets_at: null, unlimited: false }],
        },
      ],
      reason: null,
    },
  },
  correlation: {
    status: "partial",
    accounts: [
      { external_provider: "openai", external_account_ref: "acct_abc123", matched_connection_ids: ["chatgpt-account"], status: "matched", reason: "source_alias" },
    ],
    models: [
      { external_provider: "openai", external_model_id: "gpt-6.1-sol", matched_binding_ids: ["chatgpt-gpt"], status: "matched", reason: "model_alias" },
    ],
  },
};

const MAGPIE_PRIMARY_PAYLOAD = {
  view_mode: "magpie_primary",
  magpie_view: {
    status: "available",
    version: "magpie-cli 0.4",
    models: HYBRID_PAYLOAD.external_sources.magpie.models,
    accounts: HYBRID_PAYLOAD.external_sources.magpie.accounts,
    legacy_fallback: { connections: 1, usable_bindings: 1 },
    reason: null,
  },
  resources: LEGACY_PAYLOAD.resources,
  summary: LEGACY_PAYLOAD.summary,
};

const UNAVAILABLE_HYBRID = {
  ...LEGACY_PAYLOAD,
  view_mode: "hybrid",
  external_sources: { magpie: { status: "unavailable", version: null, models: [], accounts: [], reason: "not_configured" } },
};

function mockGetResources(perMode: (mode?: ResourceViewMode) => unknown) {
  return vi.spyOn(getDefaultModelControlClient(), "getResources").mockImplementation(async (mode) =>
    normalizeResourceOverview(perMode(mode)));
}

describe("resource view mode", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("http client sends ?mode= for each view and omits it for legacy/no-arg", async () => {
    const calls: string[] = [];
    const mockFetch = vi.fn(async (url: unknown) => {
      calls.push(String(url));
      return { ok: true, text: async () => JSON.stringify(LEGACY_PAYLOAD) };
    });
    vi.stubGlobal("fetch", mockFetch);
    try {
      const client = createHttpModelControlClient("/api");
      await client.getResources();
      await client.getResources("hybrid");
      await client.getResources("magpie_primary");
      await client.getResources("legacy");
      expect(calls).toEqual([
        "/api/resources",
        "/api/resources?mode=hybrid",
        "/api/resources?mode=magpie_primary",
        "/api/resources?mode=legacy",
      ]);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("normalizes viewMode and rejects unknown view strings", () => {
    expect(normalizeResourceOverview({ view_mode: "hybrid" }).viewMode).toBe("hybrid");
    expect(normalizeResourceOverview({ view_mode: "nonsense" }).viewMode).toBeUndefined();
    expect(normalizeResourceOverview({}).viewMode).toBeUndefined();
  });

  it("legacy default renders legacy summary and no Magpie panel", async () => {
    mockGetResources(() => LEGACY_PAYLOAD);
    renderWithProviders(<ResourceOverview />);
    expect(await screen.findByTestId("resource-summary")).toHaveTextContent("等价成本 $0.01");
    expect(screen.queryByTestId("magpie-panel")).toBeNull();
    expect(screen.getByTestId("resource-view-mode")).toHaveValue("legacy");
  });

  it("hybrid renders legacy resources plus a separate Magpie panel with models, accounts and provenance", async () => {
    mockGetResources((mode) => (mode === "hybrid" ? HYBRID_PAYLOAD : LEGACY_PAYLOAD));
    renderWithProviders(<ResourceOverview />);

    fireEvent.change(screen.getByTestId("resource-view-mode"), { target: { value: "hybrid" } });

    const panel = await screen.findByTestId("magpie-panel");
    expect(panel).toHaveAttribute("data-status", "available");
    expect(within(panel).getByTestId("magpie-status")).toHaveTextContent("可用");
    expect(within(panel).getByTestId("magpie-model-gpt-6.1-sol")).toHaveTextContent("GPT-6.1 Sol");
    expect(within(panel).getByTestId("magpie-model-gpt-6.1-sol")).toHaveTextContent("openai");
    const account = within(panel).getByTestId("magpie-account-openai");
    expect(account).toHaveTextContent("账号伪名 acct_abc123");
    expect(account).toHaveTextContent("计划 plus");
    expect(within(account).getByTestId("magpie-window-five_hour")).toHaveTextContent("已用 49% · 剩余 51%");
    expect(account).toHaveTextContent("观测于");
    expect(account).toHaveTextContent("EXTERNAL_MAGPIE");
    // Legacy summary stays separate and is not summed with Magpie data.
    expect(screen.getByTestId("resource-summary")).toHaveTextContent("等价成本 $0.01");
    expect(screen.queryByTestId("legacy-fallback")).toBeNull();
    // Correlation is ambiguous, never verified same account / actual routed model.
    const correlation = within(panel).getByTestId("magpie-correlation");
    expect(correlation).toHaveTextContent("可能匹配本地连接 chatgpt-account（来源匹配，未验证为同一账号）");
    expect(correlation).toHaveTextContent("候选绑定 chatgpt-gpt（实际路由模型未知）");
    expect(correlation).toHaveTextContent("实际用量与现金花费未知");
  });

  it("does not show a fake zero allowance for an unobserved Magpie account", async () => {
    mockGetResources((mode) => (mode === "hybrid" ? HYBRID_PAYLOAD : LEGACY_PAYLOAD));
    renderWithProviders(<ResourceOverview />);
    fireEvent.change(screen.getByTestId("resource-view-mode"), { target: { value: "hybrid" } });

    const panel = await screen.findByTestId("magpie-panel");
    const unknown = within(panel).getByTestId("magpie-account-anthropic");
    expect(unknown).toHaveAttribute("data-state", "UNKNOWN");
    expect(within(unknown).getByTestId("magpie-account-unknown")).toHaveTextContent("当前用量与余额未知，不计入本地合计");
    expect(within(unknown).getByTestId("magpie-window-weekly")).toHaveTextContent("用量未知");
    expect(within(unknown).getByTestId("magpie-window-weekly")).not.toHaveTextContent("已用 0%");
  });

  it("unavailable Magpie shows a clear state while legacy remains usable", async () => {
    mockGetResources((mode) => (mode === "hybrid" ? UNAVAILABLE_HYBRID : LEGACY_PAYLOAD));
    renderWithProviders(<ResourceOverview />);
    fireEvent.change(screen.getByTestId("resource-view-mode"), { target: { value: "hybrid" } });

    const panel = await screen.findByTestId("magpie-panel");
    expect(panel).toHaveAttribute("data-status", "unavailable");
    expect(within(panel).getByTestId("magpie-unavailable")).toHaveTextContent("not_configured");
    expect(panel).toHaveTextContent("本地记录仍可使用");
    expect(screen.getByTestId("resource-summary")).toBeInTheDocument();
    expect(screen.queryByTestId("magpie-models")).toBeNull();
  });

  it("magpie_primary leads with Magpie and keeps legacy behind a fallback disclosure", async () => {
    mockGetResources((mode) => (mode === "magpie_primary" ? MAGPIE_PRIMARY_PAYLOAD : LEGACY_PAYLOAD));
    renderWithProviders(<ResourceOverview />);
    fireEvent.change(screen.getByTestId("resource-view-mode"), { target: { value: "magpie_primary" } });

    const panel = await screen.findByTestId("magpie-panel");
    expect(within(panel).getByTestId("magpie-model-gpt-6.1-sol")).toBeInTheDocument();
    // Legacy is accessible but collapsed behind a disclosure, not leading above the panel.
    const fallback = screen.getByTestId("legacy-fallback");
    expect(fallback.querySelector("summary")).toHaveTextContent("本地记录回退");
    expect(within(fallback).getByTestId("resource-summary")).toBeInTheDocument();
    // The Magpie panel renders before the legacy fallback in document order.
    expect(panel.compareDocumentPosition(fallback) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("rolling back to legacy drops the Magpie panel and restores legacy-only behaviour", async () => {
    const impl = mockGetResources((mode) =>
      mode === "hybrid" ? HYBRID_PAYLOAD : LEGACY_PAYLOAD,
    );
    renderWithProviders(<ResourceOverview />);

    await screen.findByTestId("resource-summary");
    fireEvent.change(screen.getByTestId("resource-view-mode"), { target: { value: "hybrid" } });
    await screen.findByTestId("magpie-panel");
    expect(impl).toHaveBeenCalledWith("hybrid");

    fireEvent.change(screen.getByTestId("resource-view-mode"), { target: { value: "legacy" } });
    await screen.findByTestId("resource-summary");
    expect(screen.queryByTestId("magpie-panel")).toBeNull();
    expect(screen.queryByTestId("legacy-fallback")).toBeNull();
    expect(impl).toHaveBeenCalledWith("legacy");
  });
});
