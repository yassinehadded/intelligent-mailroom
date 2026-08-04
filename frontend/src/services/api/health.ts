import { apiGet } from "@/lib/api-client";
import type { HealthResponse, ReadinessResponse } from "@/types/api";

export const healthApi = {
  getHealth: () => apiGet<HealthResponse>("/api/v1/health"),
  getReadiness: () => apiGet<ReadinessResponse>("/api/v1/health/ready"),
};
