import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";
import { getDefaultModelControlClient } from "@/lib/model-control-client";
import type {
  Binding,
  Connection,
  ConnectionInput,
  Executor,
} from "@/schemas/model-access";
import type { BindingInput } from "@/schemas/model-access";

export const CONNECTIONS_QUERY_KEY = ["connections"] as const;
export const EXECUTORS_QUERY_KEY = ["executors"] as const;
export const BINDINGS_QUERY_KEY = ["bindings"] as const;

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
