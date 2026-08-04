import { apiGet } from "@/lib/api-client";
import type { AuditEventsResponse } from "@/types/api";

export const auditApi = {
  getEvents: (params?: { limit?: number; event_type?: string }) => {
    const search = new URLSearchParams();
    if (params?.limit) search.set("limit", String(params.limit));
    if (params?.event_type) search.set("event_type", params.event_type);
    const query = search.toString();
    return apiGet<AuditEventsResponse>(`/api/v1/audit/events${query ? `?${query}` : ""}`);
  },
};
