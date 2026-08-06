import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";
import { getDefaultModelControlClient } from "@/lib/model-control-client";
import type {
  ModelConnectionResult,
  ModelProfile,
  ModelProfileInput,
} from "@/schemas/model-profile";

export const MODEL_PROFILES_QUERY_KEY = ["model-profiles"] as const;

function replaceProfiles(queryClient: QueryClient, profiles: ModelProfile[]) {
  queryClient.setQueryData<ModelProfile[]>(
    MODEL_PROFILES_QUERY_KEY,
    structuredClone(profiles),
  );
}

export function useModelProfiles() {
  const client = getDefaultModelControlClient();
  return useQuery<ModelProfile[]>({
    queryKey: MODEL_PROFILES_QUERY_KEY,
    queryFn: () => client.listProfiles(),
    staleTime: 30_000,
    retry: false,
  });
}

export function useUpsertModelProfile() {
  const queryClient = useQueryClient();
  const client = getDefaultModelControlClient();
  return useMutation<ModelProfile, Error, ModelProfileInput>({
    mutationFn: (input) => client.upsertProfile(input),
    onSuccess: async () => {
      replaceProfiles(queryClient, await client.listProfiles());
    },
  });
}

export function useDeleteModelProfile() {
  const queryClient = useQueryClient();
  const client = getDefaultModelControlClient();
  return useMutation<void, Error, string>({
    mutationFn: (profileId) => client.deleteProfile(profileId),
    onSuccess: async () => {
      replaceProfiles(queryClient, await client.listProfiles());
    },
  });
}

export function useSetDefaultModelProfile() {
  const queryClient = useQueryClient();
  const client = getDefaultModelControlClient();
  return useMutation<ModelProfile[], Error, string>({
    mutationFn: (profileId) => client.setDefaultProfile(profileId),
    onSuccess: (profiles) => replaceProfiles(queryClient, profiles),
  });
}

export function useTestModelProfile() {
  const client = getDefaultModelControlClient();
  return useMutation<
    ModelConnectionResult,
    Error,
    { profileId: string; apiKey?: string }
  >({
    mutationFn: ({ profileId, apiKey }) =>
      client.testProfile(profileId, apiKey),
  });
}
