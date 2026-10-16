import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";
import { getDefaultModelControlClient, type AgentRole, type AgentRoster, type BindModelsResult } from "@/lib/model-control-client";
import type {
  Binding,
  Connection,
  ConnectionInput,
  ConnectionModelsResult,
  ConnectionProbeResult,
  Executor,
} from "@/schemas/model-access";
import type { BindingInput } from "@/schemas/model-access";
import type { ResourceOverview, ResourceViewMode } from "@/lib/resources";

export const CONNECTIONS_QUERY_KEY = ["connections"] as const;
export const EXECUTORS_QUERY_KEY = ["executors"] as const;
export const BINDINGS_QUERY_KEY = ["bindings"] as const;
export const AGENT_ROSTER_QUERY_KEY = ["agent-roster"] as const;
export const RESOURCES_QUERY_KEY = ["resources"] as const;

/**
 * Every AI resource with its tokens, list-price cost and subscription windows.
 * `mode` is a display preference only: it selects which external/Magpie data the
 * backend returns but never writes bindings or connections. A distinct query key
 * per mode keeps cached views from leaking across selections, and `legacy` (the
 * default) preserves the original single-resource behaviour exactly.
 */
export function useResources(mode: ResourceViewMode = "legacy") {
  const client = getDefaultModelControlClient();
  return useQuery<ResourceOverview>({
    queryKey: [...RESOURCES_QUERY_KEY, mode] as const,
    queryFn: () => client.getResources(mode),
    staleTime: 30_000,
    refetchInterval: 60_000,
    retry: false,
  });
}

export function useAgentRoster() {
  const client = getDefaultModelControlClient();
  return useQuery<AgentRoster>({
    queryKey: AGENT_ROSTER_QUERY_KEY,
    queryFn: () => client.getAgentRoster(),
    staleTime: 30_000,
    retry: false,
  });
}

export function usePutAgentRoster() {
  const queryClient = useQueryClient();
  const client = getDefaultModelControlClient();
  return useMutation<AgentRoster, Error, Partial<Record<AgentRole, string>>>({
    mutationFn: (roles) => client.putAgentRoster(roles),
    onSuccess: (roster) => queryClient.setQueryData(AGENT_ROSTER_QUERY_KEY, roster),
  });
}

function replaceConnections(queryClient: QueryClient, connections: Connection[]) {
  queryClient.setQueryData<Connection[]>(
    CONNECTIONS_QUERY_KEY,
    structuredClone(connections),
  );
}

function replaceBindings(queryClient: QueryClient, bindings: Binding[]) {
  queryClient.setQueryData<Binding[]>(
    BINDINGS_QUERY_KEY,
    structuredClone(bindings),
  );
}

export function useConnections() {
  const client = getDefaultModelControlClient();
  return useQuery<Connection[]>({
    queryKey: CONNECTIONS_QUERY_KEY,
    queryFn: () => client.listConnections(),
    staleTime: 30_000,
    retry: false,
  });
}

export function useUpsertConnection() {
  const queryClient = useQueryClient();
  const client = getDefaultModelControlClient();
  return useMutation<Connection, Error, ConnectionInput>({
    mutationFn: (input) => client.upsertConnection(input),
    onSuccess: async () => {
      replaceConnections(queryClient, await client.listConnections());
    },
  });
}

export function useDeleteConnection() {
  const queryClient = useQueryClient();
  const client = getDefaultModelControlClient();
  return useMutation<void, Error, string>({
    mutationFn: (connectionId) => client.deleteConnection(connectionId),
    onSuccess: async () => {
      replaceConnections(queryClient, await client.listConnections());
    },
  });
}

export function useExecutors() {
  const client = getDefaultModelControlClient();
  return useQuery<Executor[]>({
    queryKey: EXECUTORS_QUERY_KEY,
    queryFn: () => client.listExecutors(),
    staleTime: 60_000,
    retry: false,
  });
}

export function useBindings() {
  const client = getDefaultModelControlClient();
  return useQuery<Binding[]>({
    queryKey: BINDINGS_QUERY_KEY,
    queryFn: () => client.listBindings(),
    staleTime: 30_000,
    retry: false,
  });
}

export function useUpsertBinding() {
  const queryClient = useQueryClient();
  const client = getDefaultModelControlClient();
  return useMutation<Binding, Error, BindingInput>({
    mutationFn: (input) => client.upsertBinding(input),
    onSuccess: async () => {
      replaceBindings(queryClient, await client.listBindings());
    },
  });
}

export function useDeleteBinding() {
  const queryClient = useQueryClient();
  const client = getDefaultModelControlClient();
  return useMutation<void, Error, string>({
    mutationFn: (bindingId) => client.deleteBinding(bindingId),
    onSuccess: async () => {
      replaceBindings(queryClient, await client.listBindings());
    },
  });
}

export function useTestConnection() {
  const client = getDefaultModelControlClient();
  return useMutation<ConnectionProbeResult, Error, string>({
    mutationFn: (connectionId) => client.testConnection(connectionId),
  });
}

export function useBindConnectionModels() {
  const client = getDefaultModelControlClient();
  const queryClient = useQueryClient();
  return useMutation<BindModelsResult, Error, { connectionId: string; modelIds: string[]; executorId: string }>({
    mutationFn: ({ connectionId, modelIds, executorId }) => client.bindConnectionModels(connectionId, modelIds, executorId),
    onSuccess: () => void queryClient.invalidateQueries(),
  });
}

export function useListConnectionModels() {
  const client = getDefaultModelControlClient();
  return useMutation<ConnectionModelsResult, Error, string>({
    mutationFn: (connectionId) => client.listConnectionModels(connectionId),
  });
}
