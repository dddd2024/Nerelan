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

export function useRepositories() {
  return useQuery<Repository[], Error>({
    queryKey: ["repositories"],
    queryFn: async () => {
      return fetchRepositories();
    },
    staleTime: 30000,
    retry: 1,
  });
}
