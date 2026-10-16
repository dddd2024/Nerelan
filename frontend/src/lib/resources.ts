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

export type QuotaBasis = "official_percent" | "official_status" | "estimated" | "unknown";

export interface QuotaWindow {
  window: string;
  basis: QuotaBasis;
  usedPercent: number | null;
  /** [low, high] when the percent is an estimate. */
  usedPercentRange: [number, number] | null;
  /** "available" | "near_limit" | "limit_reached" when the CLI only states availability. */
  availability: string | null;
  /** List-price units used in the window, when measured locally. */
  usedUnits: number | null;
  capacitySamples: number | null;
  /** "official_calibration" | "limit_hits" when the window was estimated. */
  capacitySource: string | null;
  /** The official reading an estimate was carried forward from. */
  anchor: { usedPercent: number; at: string | null } | null;
  /** When an official percent was read (status line or a Nerelan run). */
  asOf: string | null;
  resetsAt: string | null;
  resetsAtEstimated: boolean;
  status: string | null;
  resetPassed: boolean;
}

export interface LimitHit {
  at: string;
  window: string | null;
  source: string | null;
}

export interface QuotaGuardEntry {
  at: string | null;
  role: string | null;
  bindingId: string;
  decision: "switch" | "warn" | "ok";
  reason: string;
  window: string | null;
  switchedTo: string | null;
}

export interface Quota {
  state: "OBSERVED" | "UNKNOWN";
  source: string | null;
  observedAt: string | null;
  reason: string | null;
  plan: string | null;
  windows: QuotaWindow[];
  limitHits: LimitHit[];
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

export interface MagpieModel {
  modelId: string;
  provider: string | null;
  displayName: string | null;
  reasoning: boolean | null;
  contextWindow: number | null;
  maxOutputTokens: number | null;
  isGroup: boolean;
}

export interface MagpieAccountWindow {
  name: string;
  usedPercent: number;
  remainingPercent: number;
  resetsAt: string | null;
  unlimited: boolean;
}

export interface MagpieAccount {
  provider: string | null;
  kind: string | null;
  plan: string | null;
  accountRef: string | null;
  windows: MagpieAccountWindow[];
  cachedWindows: MagpieAccountWindow[];
  state: string;
  reason: string | null;
  observedAt: string | null;
  provenance: string;
  sourceVersion: string | null;
}

export interface MagpieSnapshot {
  status: string;
  version: string | null;
  models: MagpieModel[];
  accounts: MagpieAccount[];
  reason: string | null;
}

export interface CorrelationEntry {
  externalProvider: string | null;
  externalAccountRef?: string | null;
  externalModelId?: string | null;
  matchedConnectionIds: string[];
  matchedBindingIds?: string[];
  status: string;
  reason: string;
}

export interface Correlation {
  accounts: CorrelationEntry[];
  models: CorrelationEntry[];
  status: string;
}

export interface MagpieView {
  status: string;
  version: string | null;
  models: MagpieModel[];
  accounts: MagpieAccount[];
  reason: string | null;
  legacyFallback: { connections: number; usableBindings: number };
}

/** Display-only view of GET /api/resources. Never selects writes/bindings. */
export type ResourceViewMode = "legacy" | "hybrid" | "magpie_primary";

export interface ResourceOverview {
  resources: Resource[];
  usableBindings: number;
  quotaKnown: number;
  tokens: TokenCounters;
  equivalentCost: EquivalentCost | null;
  quotaGuard: QuotaGuardEntry[];
  viewMode?: ResourceViewMode;
  externalSources?: { magpie: MagpieSnapshot };
  correlation?: Correlation;
  magpieView?: MagpieView;
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

const VIEW_MODES: ResourceViewMode[] = ["legacy", "hybrid", "magpie_primary"];
const asViewMode = (value: unknown): ResourceViewMode | null => {
  const s = asString(value);
  return s && VIEW_MODES.includes(s as ResourceViewMode) ? (s as ResourceViewMode) : null;
};

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
      const used = percent(w.used_percent);
      const range = Array.isArray(w.used_percent_range) ? w.used_percent_range.map(percent) : [];
      const basis = BASES.includes(w.basis as QuotaBasis) ? (w.basis as QuotaBasis)
        : used !== null ? "official_percent" : "unknown";
      return {
        window: asString(w.window) ?? "window",
        basis,
        usedPercent: used,
        usedPercentRange: range.length === 2 && range[0] !== null && range[1] !== null
          ? [range[0], range[1]] : null,
        availability: asString(w.availability),
        usedUnits: asNumber(w.used_units),
        capacitySamples: asNumber(asRecord(w.capacity_units).samples),
        capacitySource: asString(w.capacity_source),
        anchor: percent(asRecord(w.anchor).used_percent) !== null
          ? { usedPercent: percent(asRecord(w.anchor).used_percent) as number, at: asString(asRecord(w.anchor).at) }
          : null,
        asOf: asString(w.as_of),
        resetsAt: asString(w.resets_at),
        resetsAtEstimated: w.resets_at_estimated === true,
        status: asString(w.status),
        resetPassed: w.reset_passed === true,
      };
    }),
    limitHits: (Array.isArray(raw.limit_hits) ? raw.limit_hits : []).flatMap((item) => {
      const hit = asRecord(item);
      const at = asString(hit.at);
      return at ? [{ at, window: asString(hit.window), source: asString(hit.source) }] : [];
    }),
  };
}

const BASES: QuotaBasis[] = ["official_percent", "official_status", "estimated", "unknown"];

function percent(value: unknown): number | null {
  const n = asNumber(value);
  return n !== null && n >= 0 && n <= 100 ? n : null;
}

function guardEntries(value: unknown): QuotaGuardEntry[] {
  return (Array.isArray(value) ? value : []).flatMap((item) => {
    const raw = asRecord(item);
    const decision = raw.decision === "switch" || raw.decision === "warn" || raw.decision === "ok" ? raw.decision : null;
    const bindingId = asString(raw.binding_id);
    if (!decision || !bindingId) return [];
    return [{
      at: asString(raw.at), role: asString(raw.role), bindingId, decision,
      reason: asString(raw.reason) ?? "", window: asString(raw.window), switchedTo: asString(raw.switched_to),
    }];
  });
}

function magpieModel(value: unknown): MagpieModel {
  const raw = asRecord(value);
  const id = asString(raw.model_id) ?? asString(raw.id) ?? "";
  return {
    modelId: id,
    provider: asString(raw.provider),
    displayName: asString(raw.display_name),
    reasoning: typeof raw.reasoning === "boolean" ? raw.reasoning : null,
    contextWindow: asNumber(raw.context_window),
    maxOutputTokens: asNumber(raw.max_output_tokens),
    isGroup: raw.is_group === true,
  };
}

function magpieAccountWindow(value: unknown): MagpieAccountWindow {
  const raw = asRecord(value);
  return {
    name: asString(raw.name) ?? "window",
    usedPercent: asNumber(raw.used_percent) ?? 0,
    remainingPercent: asNumber(raw.remaining_percent) ?? 0,
    resetsAt: asString(raw.resets_at),
    unlimited: raw.unlimited === true,
  };
}

function magpieAccount(value: unknown): MagpieAccount {
  const raw = asRecord(value);
  return {
    provider: asString(raw.provider),
    kind: asString(raw.kind),
    plan: asString(raw.plan),
    accountRef: asString(raw.account_ref),
    windows: (Array.isArray(raw.windows) ? raw.windows : []).map(magpieAccountWindow),
    cachedWindows: (Array.isArray(raw.cached_windows) ? raw.cached_windows : []).map(magpieAccountWindow),
    state: asString(raw.state) ?? "UNKNOWN",
    reason: asString(raw.reason),
    observedAt: asString(raw.observed_at),
    provenance: asString(raw.provenance) ?? "EXTERNAL_MAGPIE",
    sourceVersion: asString(raw.source_version),
  };
}

function magpieSnapshot(value: unknown): MagpieSnapshot {
  const raw = asRecord(value);
  return {
    status: asString(raw.status) ?? "unavailable",
    version: asString(raw.version),
    models: (Array.isArray(raw.models) ? raw.models : []).map(magpieModel),
    accounts: (Array.isArray(raw.accounts) ? raw.accounts : []).map(magpieAccount),
    reason: asString(raw.reason),
  };
}

function correlationEntry(value: unknown, isModel: boolean): CorrelationEntry {
  const raw = asRecord(value);
  return {
    externalProvider: asString(raw.external_provider),
    ...(isModel
      ? { externalModelId: asString(raw.external_model_id) }
      : { externalAccountRef: asString(raw.external_account_ref) }),
    matchedConnectionIds: asStrings(raw.matched_connection_ids),
    ...(isModel ? { matchedBindingIds: asStrings(raw.matched_binding_ids) } : {}),
    status: asString(raw.status) ?? "uncorrelated",
    reason: asString(raw.reason) ?? "",
  };
}

function correlation(value: unknown): Correlation {
  const raw = asRecord(value);
  const accounts = (Array.isArray(raw.accounts) ? raw.accounts : []).map((v) => correlationEntry(v, false));
  const models = (Array.isArray(raw.models) ? raw.models : []).map((v) => correlationEntry(v, true));
  return {
    accounts,
    models,
    status: asString(raw.status) ?? "no_external_data",
  };
}

function magpieView(value: unknown): MagpieView {
  const raw = asRecord(value);
  const fallback = asRecord(raw.legacy_fallback);
  return {
    status: asString(raw.status) ?? "unavailable",
    version: asString(raw.version),
    models: (Array.isArray(raw.models) ? raw.models : []).map(magpieModel),
    accounts: (Array.isArray(raw.accounts) ? raw.accounts : []).map(magpieAccount),
    reason: asString(raw.reason),
    legacyFallback: {
      connections: asCount(fallback.connections),
      usableBindings: asCount(fallback.usable_bindings),
    },
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
  const viewMode = asViewMode(raw.view_mode);
  return {
    resources,
    usableBindings: asCount(summary.usable_bindings),
    quotaKnown: asCount(summary.quota_known),
    tokens: tokens(summary.tokens),
    equivalentCost: cost(summary.equivalent_cost),
    quotaGuard: guardEntries(summary.quota_guard),
    ...(viewMode ? { viewMode } : {}),
    ...(raw.external_sources ? { externalSources: { magpie: magpieSnapshot(asRecord(raw.external_sources).magpie) } } : {}),
    ...(raw.correlation ? { correlation: correlation(raw.correlation) } : {}),
    ...(raw.magpie_view ? { magpieView: magpieView(raw.magpie_view) } : {}),
  };
}

export const totalTokens = (t: TokenCounters): number => t.input + t.cacheRead + t.cacheWrite + t.output;
