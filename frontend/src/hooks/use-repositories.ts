import { useQuery } from "@tanstack/react-query";
import { fetchRepositories } from "@/lib/repository-client";
import type { Repository } from "@/lib/repository-client";

export { type Repository } from "@/lib/repository-client";

export interface RepositoryDiscoveryState {
  repositories: Repository[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

export interface UseRepositoriesOptions {
  enabled?: boolean;
}

export function useRepositories(options: UseRepositoriesOptions = {}) {
  const enabled = options.enabled !== false;
  return useQuery<Repository[], Error>({
    queryKey: ["repositories"],
    queryFn: async () => {
      return fetchRepositories();
    },
    enabled,
    staleTime: 30000,
    retry: 1,
  });
}
