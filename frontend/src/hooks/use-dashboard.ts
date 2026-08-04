import { useQuery } from "@tanstack/react-query";
import { analysisApi, auditApi, emailApi, healthApi, maarchApi } from "@/services/api";
import { ApiError } from "@/lib/api-client";

function isConfiguredError(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 503 || error.status === 502);
}

export function useDashboardData() {
  const readiness = useQuery({
    queryKey: ["health", "ready"],
    queryFn: healthApi.getReadiness,
    refetchInterval: 15_000,
  });

  const emailStatus = useQuery({
    queryKey: ["email", "status"],
    queryFn: emailApi.getStatus,
    refetchInterval: 30_000,
  });

  const emailHealth = useQuery({
    queryKey: ["email", "health"],
    queryFn: emailApi.getHealth,
    refetchInterval: 30_000,
    retry: false,
  });

  const maarchHealth = useQuery({
    queryKey: ["maarch", "health"],
    queryFn: maarchApi.getHealth,
    refetchInterval: 30_000,
    retry: false,
  });

  const analysisStatus = useQuery({
    queryKey: ["analysis", "status"],
    queryFn: analysisApi.getStatus,
    refetchInterval: 60_000,
  });

  const auditEvents = useQuery({
    queryKey: ["audit", "events", { limit: 20 }],
    queryFn: () => auditApi.getEvents({ limit: 20 }),
    refetchInterval: 15_000,
  });

  const today = new Date().toISOString().slice(0, 10);
  const processedToday =
    auditEvents.data?.events.filter(
      (event) => event.event_type === "ingested" && event.created_at.startsWith(today),
    ).length ?? 0;

  const errors =
    auditEvents.data?.events.filter((event) => event.event_type === "failed").length ?? 0;

  const pendingQueue = emailHealth.data?.unseen_count ?? 0;

  return {
    readiness,
    emailStatus,
    emailHealth,
    maarchHealth,
    analysisStatus,
    auditEvents,
    processedToday,
    errors,
    pendingQueue,
    isConfiguredError,
  };
}
