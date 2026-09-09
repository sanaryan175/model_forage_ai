import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

interface HealthResponse {
  status: string;
  app_env: string;
  aws_mode: string;
  database: string;
  converter_capabilities: Record<string, boolean>;
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data } = await apiClient.get<HealthResponse>("/api/health");
      return data;
    },
  });
}
