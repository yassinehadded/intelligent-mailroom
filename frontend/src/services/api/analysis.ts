import { apiGet, apiPost } from "@/lib/api-client";
import type {
  AnalysisStatusResponse,
  ClassifyTextRequest,
  ClassifyTextResponse,
  RoutingRule,
} from "@/types/api";

export const analysisApi = {
  getStatus: () => apiGet<AnalysisStatusResponse>("/api/v1/analysis/status"),
  getRoutingRules: () =>
    apiGet<{ rules: RoutingRule[] }>("/api/v1/analysis/routing-rules"),
  classify: (payload: ClassifyTextRequest) =>
    apiPost<ClassifyTextResponse>("/api/v1/analysis/classify", payload),
};
