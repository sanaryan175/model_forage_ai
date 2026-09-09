import { useMutation, useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Benchmark, ComparisonResult } from "@/types/api";

export function useBenchmarks() {
  return useQuery({
    queryKey: ["benchmarks"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ items: Benchmark[]; total: number }>("/api/benchmarks");
      return data;
    },
  });
}

export function useCompareBenchmarks() {
  return useMutation({
    mutationFn: async (jobIds: string[]) => {
      const { data } = await apiClient.post<ComparisonResult>("/api/benchmarks/compare", { job_ids: jobIds });
      return data;
    },
  });
}
