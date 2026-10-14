import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { ArtifactRecord } from "@/types/api";

export function useArtifacts() {
  return useQuery({
    queryKey: ["artifacts"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ items: ArtifactRecord[]; total: number }>("/api/artifacts");
      return data;
    },
    // Jobs can finish while the user is on another page, so never show a cached list on open.
    refetchOnMount: "always",
  });
}
