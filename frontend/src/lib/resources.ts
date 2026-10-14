// Read model of GET /api/resources: every connection's credential, executors, bindings,
// tokens, list-price equivalent cost and subscription quota. Unknown stays null, never 0.

export interface TokenCounters {
  input: number;
  cacheRead: number;
  cacheWrite: number;
  output: number;
  reasoning: number;
}

export interface EquivalentCost {
  state: "ESTIMATED" | "PARTIAL" | "UNKNOWN";
  usd: number | null;
  priceSource: string | null;
  priceAsOf: string | null;
  unpriced: string[];
  notes: string[];
  cliReportedUsd: number | null;
}

export interface QuotaWindow {
  window: string;
  usedPercent: number | null;
  resetsAt: string | null;
  status: string | null;
  resetPassed: boolean;
}

export interface Quota {
  state: "OBSERVED" | "UNKNOWN";
  source: string | null;
  observedAt: string | null;
  reason: string | null;
  plan: string | null;
  windows: QuotaWindow[];
}

export interface ResourceBinding {
  bindingId: string;
  modelId: string;
  executorId: string;
  usable: boolean;
  tasks: number;
  tokens: TokenCounters | null;
  equivalentCost: EquivalentCost | null;
}

export interface Resource {
  connectionId: string;
  name: string;
  enabled: boolean;
  credentialKind: "api_key" | "subscription" | "none";
  credentialConfigured: boolean;
  credentialOwner: string;
  executors: { executorId: string; ready: boolean }[];
  bindings: ResourceBinding[];
  tokens: TokenCounters;
  tasksWithTokens: number;
  equivalentCost: EquivalentCost | null;
  quota: Quota;
}

export interface ResourceOverview {
  resources: Resource[];
  usableBindings: number;
  quotaKnown: number;
  tokens: TokenCounters;
  equivalentCost: EquivalentCost | null;
}

type Raw = Record<string, unknown>;

const asRecord = (value: unknown): Raw => (value && typeof value === "object" ? (value as Raw) : {});
const asNumber = (value: unknown): number | null => (typeof value === "number" && Number.isFinite(value) ? value : null);
const asCount = (value: unknown): number => {
  const n = asNumber(value);
  return n !== null && n >= 0 ? n : 0;
};
const asString = (value: unknown): string | null => (typeof value === "string" && value ? value : null);
const asStrings = (value: unknown): string[] => (Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : []);

function tokens(value: unknown): TokenCounters {
  const raw = asRecord(value);
  return {
    input: asCount(raw.input),
    cacheRead: asCount(raw.cache_read),
    cacheWrite: asCount(raw.cache_write),
    output: asCount(raw.output),
    reasoning: asCount(raw.reasoning),
  };
}

function cost(value: unknown): EquivalentCost | null {
  if (!value || typeof value !== "object") return null;
  const raw = asRecord(value);
  const state = raw.state === "ESTIMATED" || raw.state === "PARTIAL" ? raw.state : "UNKNOWN";
  return {
    state,
    usd: asNumber(raw.usd),
    priceSource: asString(raw.price_source),
    priceAsOf: asString(raw.price_as_of),
    unpriced: asStrings(raw.unpriced),
    notes: asStrings(raw.notes),
    cliReportedUsd: asNumber(raw.cli_reported_usd),
  };
}

function quota(value: unknown): Quota {
  const raw = asRecord(value);
  const windows = Array.isArray(raw.windows) ? raw.windows : [];
  return {
    state: raw.state === "OBSERVED" ? "OBSERVED" : "UNKNOWN",
    source: asString(raw.source),
    observedAt: asString(raw.observed_at),
    reason: asString(raw.reason),
    plan: asString(raw.plan),
    windows: windows.map((item) => {
      const w = asRecord(item);
      const used = asNumber(w.used_percent);
      return {
        window: asString(w.window) ?? "window",
        usedPercent: used !== null && used >= 0 && used <= 100 ? used : null,
        resetsAt: asString(w.resets_at),
        status: asString(w.status),
        resetPassed: w.reset_passed === true,
      };
    }),
  };
}

export function normalizeResourceOverview(payload: unknown): ResourceOverview {
  const raw = asRecord(payload);
  const summary = asRecord(raw.summary);
  const resources = (Array.isArray(raw.resources) ? raw.resources : []).map((item): Resource => {
    const r = asRecord(item);
    const credential = asRecord(r.credential);
    const usage = asRecord(r.token_usage);
    const kind = credential.kind === "api_key" || credential.kind === "subscription" ? credential.kind : "none";
    return {
      connectionId: asString(r.connection_id) ?? "",
      name: asString(r.name) ?? asString(r.connection_id) ?? "",
      enabled: r.enabled === true,
      credentialKind: kind,
      credentialConfigured: credential.configured === true,
      credentialOwner: asString(r.credential_owner) ?? "none",
      executors: (Array.isArray(r.executors) ? r.executors : []).map((e) => ({
        executorId: asString(asRecord(e).executor_id) ?? "",
        ready: asRecord(e).ready === true,
      })),
      bindings: (Array.isArray(r.bindings) ? r.bindings : []).map((b): ResourceBinding => {
        const row = asRecord(b);
        const binding = asRecord(row.tokens);
        return {
          bindingId: asString(row.binding_id) ?? "",
          modelId: asString(row.model_id) ?? "",
          executorId: asString(row.executor_id) ?? "",
          usable: row.usable === true,
          tasks: asCount(binding.tasks),
          tokens: row.tokens && typeof row.tokens === "object" ? tokens(row.tokens) : null,
          equivalentCost: cost(row.equivalent_cost),
        };
      }),
      tokens: tokens(usage),
      tasksWithTokens: asCount(usage.tasks_with_tokens),
      equivalentCost: cost(r.equivalent_cost),
      quota: quota(r.quota),
    };
  });
  return {
    resources,
    usableBindings: asCount(summary.usable_bindings),
    quotaKnown: asCount(summary.quota_known),
    tokens: tokens(summary.tokens),
    equivalentCost: cost(summary.equivalent_cost),
  };
}

export const totalTokens = (t: TokenCounters): number => t.input + t.cacheRead + t.cacheWrite + t.output;
