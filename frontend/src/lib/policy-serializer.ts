import type { PolicyContract } from "@/types";

/**
 * Serialize a PolicyContract to a canonical JSON string.
 * Canonical = sorted object keys, stable formatting, so identical policies
 * produce identical strings (useful for digesting delegation requests).
 */
export function serializePolicy(policy: PolicyContract): string {
  return JSON.stringify(sortKeys(policy), null, 2);
}

/** Deserialize a JSON string into a PolicyContract (throws on invalid JSON). */
export function deserializePolicy(json: string): PolicyContract {
  const parsed = JSON.parse(json) as unknown;
  return parsed as PolicyContract;
}

/** Round-trip a policy through JSON and back. */
export function roundTripPolicy(policy: PolicyContract): PolicyContract {
  return deserializePolicy(serializePolicy(policy));
}

// ---------------------------------------------------------------------------
// Internals
// ---------------------------------------------------------------------------

function sortKeys(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortKeys);
  }
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    const keys = Object.keys(value as Record<string, unknown>).sort();
    for (const key of keys) {
      out[key] = sortKeys((value as Record<string, unknown>)[key]);
    }
    return out;
  }
  return value;
}
