export interface Repository {
  full_name: string;
  html_url: string;
  is_private: boolean;
  visibility: string;
  default_branch: string;
}

const API_BASE =
  import.meta.env.VITE_TASK_API_BASE ?? "http://127.0.0.1:8766";

function _isMock() {
  const mode = import.meta.env.MODE;
  if (mode === "mock") return true;
  if (mode === "test") {
    return !import.meta.env.VITE_TASK_CLIENT_USE_HTTP;
  }
  return false;
}

async function _json<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) return {} as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error("invalid api response");
  }
}

export async function fetchRepositories(): Promise<Repository[]> {
  if (_isMock()) {
    return [];
  }
  const response = await fetch(`${API_BASE}/api/repositories`, {
    headers: { Accept: "application/json" },
  });
  if (response.status === 503) {
    const payload = await _json<Record<string, unknown>>(response).catch(
      () => ({}),
    );
    throw new Error(
      `github adapter unavailable: ${(payload as { error?: string }).error ?? "unavailable"}`,
    );
  }
  if (response.status === 500) {
    const payload = await _json<Record<string, unknown>>(response).catch(
      () => ({}),
    );
    throw new Error(
      `repository discovery failed: ${(payload as { error?: string }).error ?? "failed"}`,
    );
  }
  if (!response.ok) {
    throw new Error(`fetch repositories failed: ${response.status}`);
  }
  const payload = (await _json<{
    repositories: Array<Record<string, unknown>>;
    total: number;
  }>(response)) as {
    repositories: Array<Record<string, unknown>>;
    total: number;
  };
  return (payload.repositories ?? []).map((r: Record<string, unknown>) => ({
    full_name: String(r.full_name ?? ""),
    html_url: String(r.html_url ?? ""),
    is_private: Boolean(r.is_private ?? false),
    visibility: String(r.visibility ?? ""),
    default_branch: String(r.default_branch ?? ""),
  }));
}

export async function selectRepository(
  full_name: string,
  html_url: string,
): Promise<{ repository: string }> {
  return {
    repository: html_url || `https://github.com/${full_name}`,
  };
}
