import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, within } from "@testing-library/react";
import { ResourceOverview } from "@/components/resource-overview";
import { getDefaultModelControlClient, resetDefaultModelControlClientForTests } from "@/lib/model-control-client";
import { normalizeResourceOverview, type ResourceViewMode } from "@/lib/resources";
import { renderWithProviders } from "./test-utils";

const LEGACY_PAYLOAD = {
  resources: [],
  summary: { usable_bindings: 0, quota_known: 0, tokens: {}, equivalent_cost: null },
};

const ACCOUNTS = [
  {
    provider: "openai",
    kind: "subscription",
    plan: "plus",
    account_ref: "acct_bound",
    state: "FRESH",
    observed_at: "2026-11-04T04:44:18Z",
    provenance: "EXTERNAL_MAGPIE",
    source_version: null,
    windows: [{ name: "five_hour", used_percent: 49, remaining_percent: 51, resets_at: null, unlimited: false }],
  },
  {
    provider: "moonshot",
    kind: "credit",
    plan: null,
    account_ref: "acct_telemetry",
    state: "FRESH",
    observed_at: "2026-11-04T04:44:18Z",
    provenance: "EXTERNAL_MAGPIE",
    source_version: null,
    windows: [{ name: "weekly", used_percent: 10, remaining_percent: 90, resets_at: null, unlimited: false }],
  },
  {
    provider: "anthropic",
    kind: "subscription",
    plan: null,
    account_ref: "acct_stale",
    state: "STALE",
    observed_at: null,
    provenance: "EXTERNAL_MAGPIE",
    source_version: null,
    windows: [],
  },
];

const HYBRID_PAYLOAD = {
  ...LEGACY_PAYLOAD,
  view_mode: "hybrid",
  external_sources: {
    magpie: { status: "available", version: "magpie-cli 0.4", models: [], accounts: ACCOUNTS, reason: null },
  },
  account_attribution: {
    status: "available",
    reason: null,
    summary: { accounts: 3, route_bound: 1, no_route_identity: 1, ambiguous: 0, unobserved: 1, malformed: 0 },
    accounts: [
      {
        provider: "openai",
        account_ref: "acct_bound",
        state: "FRESH",
        reason: null,
        observed_at: "2026-11-04T04:44:18Z",
        usage_scope: "account",
        windows: [],
        cached_windows: [],
        attribution: {
          status: "route_bound",
          reason: null,
          route_provider: "codex",
          connection_ids: ["chatgpt-account"],
        },
      },
      {
        provider: "moonshot",
        account_ref: "acct_telemetry",
        state: "FRESH",
        reason: null,
        observed_at: "2026-11-04T04:44:18Z",
        usage_scope: "account",
        windows: [],
        cached_windows: [],
        attribution: {
          status: "no_route_identity",
          reason: "provider_not_mapped_to_any_executor",
          route_provider: null,
          connection_ids: [],
        },
      },
      {
        provider: "anthropic",
        account_ref: "acct_stale",
        state: "STALE",
        reason: "stale_observation",
        observed_at: null,
        usage_scope: "account",
        windows: [],
        cached_windows: [],
        attribution: {
          status: "unobserved",
          reason: "stale_observation",
          route_provider: "claude-code",
          connection_ids: [],
        },
      },
    ],
  },
};

function mockGetResources(perMode: (mode?: ResourceViewMode) => unknown) {
  return vi.spyOn(getDefaultModelControlClient(), "getResources").mockImplementation(async (mode) =>
    normalizeResourceOverview(perMode(mode)));
}

describe("account attribution", () => {
  beforeEach(() => {
    resetDefaultModelControlClientForTests();
  });

  it("normalizes the five attribution states and keeps the machine reason", () => {
    const overview = normalizeResourceOverview(HYBRID_PAYLOAD);
    const accounts = overview.accountAttribution?.accounts ?? [];
    expect(accounts.map((entry) => entry.status)).toEqual([
      "route_bound",
      "no_route_identity",
      "unobserved",
    ]);
    expect(accounts[0].routeProvider).toBe("codex");
    expect(accounts[0].connectionIds).toEqual(["chatgpt-account"]);
    expect(accounts[1].reasonCode).toBe("provider_not_mapped_to_any_executor");
    expect(overview.accountAttribution?.summary).toEqual({
      accounts: 3,
      routeBound: 1,
      noRouteIdentity: 1,
      ambiguous: 0,
      unobserved: 1,
      malformed: 0,
    });
  });

  it("keeps an unknown attribution status visible instead of guessing", () => {
    const overview = normalizeResourceOverview({
      ...HYBRID_PAYLOAD,
      account_attribution: {
        status: "available",
        reason: null,
        summary: {},
        accounts: [{ account_ref: "x", attribution: { status: "something_new" } }],
      },
    });
    expect(overview.accountAttribution?.accounts[0].status).toBe("unknown");
  });

  it("omits the section entirely for legacy payloads", () => {
    expect(normalizeResourceOverview(LEGACY_PAYLOAD).accountAttribution).toBeUndefined();
  });

  it("renders one badge per account and a summary that never claims a routed task", async () => {
    mockGetResources((mode) => (mode === "hybrid" ? HYBRID_PAYLOAD : LEGACY_PAYLOAD));
    renderWithProviders(<ResourceOverview />);
    fireEvent.change(screen.getByTestId("resource-view-mode"), { target: { value: "hybrid" } });

    const panel = await screen.findByTestId("magpie-panel");
    const summary = within(panel).getByTestId("account-attribution-summary");
    expect(summary).toHaveTextContent("账户 3");
    expect(summary).toHaveTextContent("已绑定路由 1");
    expect(summary).toHaveTextContent("仅遥测 1");
    expect(summary).toHaveTextContent("未观测 1");

    const bound = within(panel).getByTestId("magpie-account-openai");
    const boundBadge = within(bound).getByTestId("account-attribution");
    expect(boundBadge).toHaveAttribute("data-attribution", "route_bound");
    expect(boundBadge).toHaveTextContent("已绑定路由 · 路由 codex · 连接 chatgpt-account");
    // Provider-level binding must never be phrased as "this account is in use".
    expect(boundBadge).not.toHaveTextContent("正在使用");

    const telemetry = within(panel).getByTestId("magpie-account-moonshot");
    expect(within(telemetry).getByTestId("account-attribution")).toHaveAttribute(
      "data-attribution",
      "no_route_identity",
    );
    expect(within(telemetry).getByTestId("account-attribution")).toHaveTextContent("仅遥测（无路由）");

    const stale = within(panel).getByTestId("magpie-account-anthropic");
    expect(within(stale).getByTestId("account-attribution")).toHaveAttribute("data-attribution", "unobserved");
  });

  it("renders no badge when the payload carries no attribution", async () => {
    mockGetResources((mode) =>
      mode === "hybrid"
        ? { ...HYBRID_PAYLOAD, account_attribution: undefined }
        : LEGACY_PAYLOAD);
    renderWithProviders(<ResourceOverview />);
    fireEvent.change(screen.getByTestId("resource-view-mode"), { target: { value: "hybrid" } });

    const panel = await screen.findByTestId("magpie-panel");
    expect(within(panel).getByTestId("magpie-accounts")).toBeInTheDocument();
    expect(within(panel).queryByTestId("account-attribution")).toBeNull();
    expect(within(panel).queryByTestId("account-attribution-summary")).toBeNull();
  });
});
