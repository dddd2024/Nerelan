import { useQuery } from "@tanstack/react-query";
import { fetchRuns } from "@/lib/platform-client";

export function useRuns() {
  return useQuery({
    queryKey: ["runs"],
    queryFn: fetchRuns,
    staleTime: 2_000,
    refetchInterval: 4_000,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });
}
