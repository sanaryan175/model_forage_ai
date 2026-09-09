import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { ArtifactRecord, ModelRecord } from "@/types/api";

export function useModels(search?: string) {
  return useQuery({
    queryKey: ["models", search ?? ""],
    queryFn: async () => {
      const { data } = await apiClient.get<{ items: ModelRecord[]; total: number }>("/api/models", {
        params: search ? { search } : undefined,
      });
      return data;
    },
    refetchInterval: (query) => (query.state.data?.items.some((m) => m.status === "validating") ? 2000 : false),
  });
}

export function useModel(modelId: string | undefined) {
  return useQuery({
    queryKey: ["models", modelId],
    queryFn: async () => {
      const { data } = await apiClient.get<ModelRecord>(`/api/models/${modelId}`);
      return data;
    },
    enabled: Boolean(modelId),
    refetchInterval: (query) => (query.state.data?.status === "validating" ? 1500 : false),
  });
}

export function useModelArtifacts(modelId: string | undefined) {
  return useQuery({
    queryKey: ["models", modelId, "artifacts"],
    queryFn: async () => {
      const { data } = await apiClient.get<ArtifactRecord[]>(`/api/models/${modelId}/artifacts`);
      return data;
    },
    enabled: Boolean(modelId),
  });
}

export function useUploadModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ name, file }: { name: string; file: File }) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post<ModelRecord>("/api/models/upload", formData, {
        params: { name },
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["models"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (modelId: string) => {
      await apiClient.delete(`/api/models/${modelId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["models"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
