import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { apiClient, API_URL, getToken } from "@/lib/api-client";
import type { ConversionJob, JobLogEntry, OptimizationType, TargetFormat } from "@/types/api";

export function useConversions() {
  return useQuery({
    queryKey: ["conversions"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ items: ConversionJob[]; total: number }>("/api/conversions");
      return data;
    },
    refetchInterval: (query) =>
      query.state.data?.items.some((j) => !["completed", "failed", "cancelled"].includes(j.status)) ? 2500 : false,
  });
}

export function useConversion(jobId: string | undefined) {
  return useQuery({
    queryKey: ["conversions", jobId],
    queryFn: async () => {
      const { data } = await apiClient.get<ConversionJob>(`/api/conversions/${jobId}`);
      return data;
    },
    enabled: Boolean(jobId),
    refetchInterval: (query) =>
      query.state.data && !["completed", "failed", "cancelled"].includes(query.state.data.status) ? 1500 : false,
  });
}

export function useConversionLogs(jobId: string | undefined, live: boolean) {
  return useQuery({
    queryKey: ["conversions", jobId, "logs"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ items: JobLogEntry[] }>(`/api/conversions/${jobId}/logs`);
      return data.items;
    },
    enabled: Boolean(jobId),
    refetchInterval: live ? 1500 : false,
  });
}

export function useCreateConversion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      model_id: string;
      target_formats: TargetFormat[];
      optimization: OptimizationType;
      batch_size: number;
      target_device: string;
      input_shape?: number[] | null;
    }) => {
      const { data } = await apiClient.post<ConversionJob[]>("/api/conversions", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useCancelConversion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      const { data } = await apiClient.post<ConversionJob>(`/api/conversions/${jobId}/cancel`);
      return data;
    },
    onSuccess: (_data, jobId) => {
      queryClient.invalidateQueries({ queryKey: ["conversions"] });
      queryClient.invalidateQueries({ queryKey: ["conversions", jobId] });
    },
  });
}

export function useRetryConversion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      const { data } = await apiClient.post<ConversionJob>(`/api/conversions/${jobId}/retry`);
      return data;
    },
    onSuccess: (_data, jobId) => {
      queryClient.invalidateQueries({ queryKey: ["conversions"] });
      queryClient.invalidateQueries({ queryKey: ["conversions", jobId] });
    },
  });
}

/** Live status via SSE, falling back gracefully if the stream errors out (polling above still applies). */
export function useConversionStream(jobId: string | undefined) {
  const [status, setStatus] = useState<{ status: string; progress: number; error_message: string | null } | null>(
    null,
  );
  const queryClient = useQueryClient();
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) return;
    const token = getToken();
    const url = new URL(`${API_URL}/api/conversions/${jobId}/stream`);
    if (token) url.searchParams.set("token", token);

    const source = new EventSource(url.toString());
    sourceRef.current = source;

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      setStatus(payload);
      queryClient.invalidateQueries({ queryKey: ["conversions", jobId] });
      queryClient.invalidateQueries({ queryKey: ["conversions", jobId, "logs"] });
      if (["completed", "failed", "cancelled"].includes(payload.status)) {
        source.close();
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
        queryClient.invalidateQueries({ queryKey: ["benchmarks"] });
      }
    };
    source.onerror = () => source.close();

    return () => source.close();
  }, [jobId, queryClient]);

  return status;
}
