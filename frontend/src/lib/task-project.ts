/** Presentation-only canonical repository identity; do not alias by a matching slug. */
export function taskProjectName(repository: string | undefined): string {
  const repo = repository?.trim();
  return repo || "未归属";
}

export function taskProjectHref(repository: string | undefined): string | null {
  const repo = repository?.trim();
  return repo ? `/tasks?repository=${encodeURIComponent(repo)}` : null;
}

/** Never infer a Goal link from a title, issue number, branch or repository. */
export function linkedGoalId(value: unknown): string | undefined {
  return typeof value === "string" && /^[A-Za-z0-9_-]{1,160}$/.test(value)
    ? value : undefined;
}
