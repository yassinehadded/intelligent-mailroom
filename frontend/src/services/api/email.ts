import { apiGet, apiPost } from "@/lib/api-client";
import type {
  EmailHealthResponse,
  EmailPollResponse,
  EmailStatusResponse,
} from "@/types/api";

export const emailApi = {
  getStatus: () => apiGet<EmailStatusResponse>("/api/v1/email/status"),
  getHealth: () => apiGet<EmailHealthResponse>("/api/v1/email/health"),
  poll: (limit?: number) =>
    apiPost<EmailPollResponse>(
      limit ? `/api/v1/email/poll?limit=${limit}` : "/api/v1/email/poll",
    ),
};
