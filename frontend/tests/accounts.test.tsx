import { afterEach, describe, expect, it, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { AccountsPage } from "@/routes/accounts";
import * as client from "@/lib/platform-client";
import type { AccountPool, PoolAccount } from "@/lib/platform-client";

function account(overrides: Partial<PoolAccount> = {}): PoolAccount {
  return {
    account_ref: "codex:1", provider: "codex", health: "HEALTHY", headroom_pct: 40, next_reset_at: null,
    anomaly_flags: [], dispatchable: true, admission_evidence: true, cooldown: null, score: null, ...overrides,
  };
}

function pool(overrides: Partial<AccountPool> = {}): AccountPool {
  return {
    source: "magpie", monitoring: true,
    summary: { total_accounts: 1, dispatchable_accounts: 1, cooling_accounts: 0, best_headroom_pct: 40, earliest_capacity_at: null },
    accounts: [account()], budget: null, policy: {}, alerts: { active: [], recent: [] }, ...overrides,
  };
}

function mount(value: AccountPool) {
  vi.spyOn(client, "fetchAccountPool").mockResolvedValue(value);
  renderWithProviders(<AccountsPage />);
}

afterEach(() => vi.restoreAllMocks());

describe("Accounts page", () => {
  it("summarizes the pool and states where the data came from", async () => {
    mount(pool({ summary: { total_accounts: 11, dispatchable_accounts: 6, cooling_accounts: 2, best_headroom_pct: 99.6, earliest_capacity_at: null } }));
    expect(await screen.findByTestId("pool-dispatchable")).toHaveTextContent("6 / 11");
    expect(screen.getByText("2 个冷却中")).toBeInTheDocument();
    expect(screen.getByTestId("pool-best-headroom")).toHaveTextContent("100%");
    expect(screen.getByText("数据来自 Magpie")).toBeInTheDocument();
  });

  it("keeps unknown headroom unknown instead of showing zero", async () => {
    mount(pool({ accounts: [account({ health: "STALE", headroom_pct: null, dispatchable: false })] }));
    const row = await screen.findByTestId("pool-account-codex");
    expect(within(row).getByText("未知")).toBeInTheDocument();
    expect(within(row).queryByText("0%")).not.toBeInTheDocument();
    expect(within(row).getByText("数据过期")).toBeInTheDocument();
  });

  it("marks accounts that never reach admission as observed only", async () => {
    mount(pool({ accounts: [account({ provider: "workbuddy", admission_evidence: false })] }));
    expect(within(await screen.findByTestId("pool-account-workbuddy")).getByText("仅观测")).toBeInTheDocument();
  });

  it("distinguishes quarantine from an ordinary cooldown", async () => {
    const until = Date.now() / 1000 + 600;
    mount(pool({ accounts: [
      account({ cooldown: { until, kind: "account_abnormal", tier: "quarantine", streak: 1 } }),
      account({ account_ref: "claude:1", provider: "claude", cooldown: { until, kind: "task_failed", tier: "transient", streak: 1 } }),
    ] }));
    expect(within(await screen.findByTestId("pool-account-codex")).getByText(/隔离中/)).toBeInTheDocument();
    expect(within(screen.getByTestId("pool-account-claude")).getByText(/冷却中/)).toBeInTheDocument();
  });

  it("reports feedback only when attempts exist", async () => {
    mount(pool({ accounts: [
      account({ score: { attempts: 4, successes: 3, reliability: 0.75, mean_cost_units: null, mean_wall_seconds: 2 } }),
      account({ account_ref: "claude:1", provider: "claude" }),
    ] }));
    expect(within(await screen.findByTestId("pool-account-codex")).getByText("75% 成功 · 4 次 · 2.0 秒")).toBeInTheDocument();
    expect(within(screen.getByTestId("pool-account-claude")).getByText("暂无反馈")).toBeInTheDocument();
  });

  it("lists active alerts with their severity", async () => {
    mount(pool({ alerts: { active: [
      { code: "pool_no_usable_account", severity: "critical", subject: "pool", detail: "没有可派发账户", since: 1 },
    ], recent: [] } }));
    expect(await screen.findByTestId("pool-alert-pool_no_usable_account")).toHaveAttribute("data-severity", "critical");
    expect(screen.getByTestId("pool-alert-count")).toHaveTextContent("1");
    expect(screen.queryByTestId("pool-no-alerts")).not.toBeInTheDocument();
  });

  it("says so when the monitor thread is not running", async () => {
    mount(pool({ monitoring: false }));
    expect(await screen.findByText("监控线程未运行")).toBeInTheDocument();
    expect(screen.getByTestId("pool-no-alerts")).toBeInTheDocument();
  });

  it("shows the enforced budget and an uncapped one honestly", async () => {
    mount(pool({ budget: { max_cost_micro_units: 5_000_000, remaining_cost_micro_units: 1_500_000, max_token_units: null, remaining_token_units: null } }));
    expect(await screen.findByTestId("pool-budget-cost")).toHaveTextContent("成本：剩余 1.50 / 5.00");
    expect(screen.getByText("Token：未设上限")).toBeInTheDocument();
  });

  it("shows the policy version and offers no rollback control in the browser", async () => {
    mount(pool({ policy: { enabled: true, revision: 3, effective: { reliability_weight: 0.55, cost_weight: 0.3, latency_weight: 0.15 } } }));
    expect(await screen.findByTestId("pool-policy-state")).toHaveTextContent("自进化已开启 · 版本 3");
    expect(screen.queryByRole("button", { name: /回滚/ })).not.toBeInTheDocument();
  });

  it("explains an unavailable source and an empty pool", async () => {
    mount(pool({ source: "unavailable", summary: null, accounts: [] }));
    expect(await screen.findByText("账户状态暂时无法读取")).toBeInTheDocument();
    expect(screen.getByText(/还没有账户/)).toBeInTheDocument();
    expect(screen.getByTestId("pool-dispatchable")).toHaveTextContent("—");
  });

  it("labels last-known rows when the source stops answering", async () => {
    mount(pool({ source: "unavailable" }));
    expect(await screen.findByText("账户状态暂时无法读取，显示最近一次结果")).toBeInTheDocument();
    expect(screen.getByTestId("pool-account-codex")).toBeInTheDocument();
  });

  it("does not show an empty pool when the first read fails", async () => {
    vi.spyOn(client, "fetchAccountPool").mockRejectedValue(new Error("down"));
    renderWithProviders(<AccountsPage />);
    expect(await screen.findByText("账户状态读取失败")).toBeInTheDocument();
    expect(screen.queryByText(/还没有账户/)).not.toBeInTheDocument();
  });
});
