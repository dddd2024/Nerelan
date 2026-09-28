import type { PlatformUsageSummary, PlatformUsageRole } from "@/lib/platform-client";

/**
 * Truthful presentation model for a run's usage summary.
 *
 * The backend contract (run_store.usage_summary) is:
 *  - status is USAGE_UNKNOWN when there are no observations OR any unknown
 *    observation, otherwise OBSERVED;
 *  - numeric totals sum ONLY observed records; UNKNOWN observations carry no
 *    metrics and never contribute to totals.
 *
 * This helper derives a presentation kind from the existing count fields so the
 * UI never prints "Tokens 0 / Cost $0" beside text claiming unknown is not
 * zero. It does not infer any new backend field or alter enforcement.
 */
export type UsagePresentationKind =
  | "observed"
  | "observed-zero"
  | "no-observations"
  | "all-unknown"
  | "partial";

export type UsageRoleKind =
  | "observed"
  | "observed-zero"
  | "no-observations"
  | "all-unknown"
  | "partial";

export interface UsageRolePresentation {
  role: string;
  kind: UsageRoleKind;
  total_token_units: number;
  cost_micro_units: number;
  observation_count: number;
  unknown_observation_count: number;
}

export interface UsagePresentation {
  kind: UsagePresentationKind;
  observation_count: number;
  unknown_observation_count: number;
  total_token_units: number;
  cost_micro_units: number;
  /** True when observed-only numeric totals may be shown truthfully. */
  show_totals: boolean;
  per_role: UsageRolePresentation[];
}

function roleTokenTotal(role: PlatformUsageRole): number {
  return (
    role.input_units +
    role.output_units +
    role.reasoning_units +
    role.cache_read_units +
    role.cache_write_units
  );
}

function deriveRoleKind(role: PlatformUsageRole): UsageRoleKind {
  // A role with zero observations has no observed value at all; it must never
  // be labelled "observed-zero" (which means: observed, and the value is 0).
  if (role.observation_count === 0) return "no-observations";
  if (role.unknown_observation_count === role.observation_count) {
    return "all-unknown";
  }
  if (role.unknown_observation_count > 0) return "partial";
  if (roleTokenTotal(role) === 0 && role.cost_micro_units === 0) {
    return "observed-zero";
  }
  return "observed";
}

export function deriveUsagePresentation(
  usage: PlatformUsageSummary,
): UsagePresentation {
  const {
    observation_count,
    unknown_observation_count,
    total_token_units,
    cost_micro_units,
    per_role,
  } = usage;

  let kind: UsagePresentationKind;
  if (observation_count === 0) {
    kind = "no-observations";
  } else if (unknown_observation_count === observation_count) {
    kind = "all-unknown";
  } else if (unknown_observation_count > 0) {
    kind = "partial";
  } else if (total_token_units === 0 && cost_micro_units === 0) {
    kind = "observed-zero";
  } else {
    kind = "observed";
  }

  return {
    kind,
    observation_count,
    unknown_observation_count,
    total_token_units,
    cost_micro_units,
    show_totals:
      kind === "observed" || kind === "observed-zero" || kind === "partial",
    per_role: per_role.map((role) => ({
      role: role.role,
      kind: deriveRoleKind(role),
      total_token_units: roleTokenTotal(role),
      cost_micro_units: role.cost_micro_units,
      observation_count: role.observation_count,
      unknown_observation_count: role.unknown_observation_count,
    })),
  };
}
