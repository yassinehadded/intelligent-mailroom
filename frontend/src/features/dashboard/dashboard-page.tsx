import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowUpRight,
  Brain,
  CheckCircle2,
  Loader2,
  Mail,
  RefreshCw,
  Server,
  Workflow,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-dot";
import { useDashboardData } from "@/hooks/use-dashboard";
import { useEmailPoll } from "@/hooks/use-email-poll";
import { useEnumTranslation, useLocalizedFormatters } from "@/lib/i18n-helpers";
import { ApiError } from "@/lib/api-client";

function MetricCard({
  title,
  value,
  description,
  loading,
}: {
  title: string;
  value: React.ReactNode;
  description?: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="text-3xl font-semibold">{loading ? <Skeleton className="h-8 w-16" /> : value}</CardTitle>
      </CardHeader>
      {description ? <CardContent className="text-sm text-muted-foreground">{description}</CardContent> : null}
    </Card>
  );
}

function ServiceCard({
  title,
  icon: Icon,
  status,
  detail,
  loading,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  status: "success" | "warning" | "error" | "neutral";
  detail: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div>
          <CardDescription>{title}</CardDescription>
          <CardTitle className="mt-2 flex items-center gap-2 text-lg">
            <Icon className="h-4 w-4 text-primary" />
            {loading ? <Skeleton className="h-5 w-24" /> : <StatusBadge label={detail} tone={status} />}
          </CardTitle>
        </div>
      </CardHeader>
    </Card>
  );
}

export function DashboardPage() {
  const { t } = useTranslation(["dashboard", "common"]);
  const { formatDate } = useLocalizedFormatters();
  const { translateEventType, translateSystem } = useEnumTranslation();
  const {
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
  } = useDashboardData();
  const { poll, isPolling, activeStep, steps } = useEmailPoll();

  const maarchTone =
    maarchHealth.isError && isConfiguredError(maarchHealth.error)
      ? "warning"
      : maarchHealth.data?.status === "connected"
        ? "success"
        : "error";

  const emailTone = !emailStatus.data?.configured
    ? "warning"
    : emailHealth.isError
      ? "error"
      : "success";

  const workerTone =
    readiness.data?.status === "ready"
      ? "success"
      : readiness.data?.status === "degraded"
        ? "warning"
        : "neutral";

  const maarchDetail =
    maarchHealth.data?.application_name ??
    (maarchHealth.error instanceof ApiError ? t("common:notConfigured") : t("common:checking"));

  const emailDetail = emailStatus.data?.configured
    ? translateSystem(emailHealth.data?.status ?? "configured")
    : t("common:notConfigured");

  const aiDetail = analysisStatus.data
    ? t("common:engine", { provider: analysisStatus.data.ai_provider })
    : t("common:checking");

  const workerDetail = readiness.data?.status
    ? translateSystem(readiness.data.status)
    : t("common:checking");

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("dashboard:title")}
        description={t("dashboard:description")}
        actions={
          <>
            <Button variant="outline" onClick={() => void poll()} disabled={isPolling}>
              {isPolling ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              {t("common:buttons.pollNow")}
            </Button>
            <Button asChild>
              <a href="http://localhost:8081" target="_blank" rel="noreferrer">
                {t("common:buttons.openMaarch")}
                <ArrowUpRight className="h-4 w-4" />
              </a>
            </Button>
          </>
        }
      />

      {activeStep !== null ? (
        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard:processingMailbox")}</CardTitle>
            <CardDescription>{t("dashboard:processingDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {steps.map((step, index) => {
              const done = index < activeStep;
              const current = index === activeStep;
              return (
                <motion.div
                  key={step}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-3 text-sm"
                >
                  {done ? (
                    <CheckCircle2 className="h-4 w-4 text-success" />
                  ) : current ? (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  ) : (
                    <span className="h-4 w-4 rounded-full border border-border" />
                  )}
                  <span className={done ? "text-foreground" : current ? "font-medium" : "text-muted-foreground"}>
                    {step}
                  </span>
                </motion.div>
              );
            })}
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ServiceCard title={t("dashboard:cards.maarchStatus")} icon={Workflow} status={maarchTone} detail={maarchDetail} loading={maarchHealth.isLoading} />
        <ServiceCard title={t("dashboard:cards.emailStatus")} icon={Mail} status={emailTone} detail={emailDetail} loading={emailStatus.isLoading} />
        <ServiceCard
          title={t("dashboard:cards.aiStatus")}
          icon={Brain}
          status={analysisStatus.data?.ai_enabled ? "success" : "warning"}
          detail={aiDetail}
          loading={analysisStatus.isLoading}
        />
        <ServiceCard title={t("dashboard:cards.workerStatus")} icon={Server} status={workerTone} detail={workerDetail} loading={readiness.isLoading} />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title={t("dashboard:cards.unreadEmails")} value={pendingQueue} description={t("dashboard:metrics.unreadDescription")} loading={emailHealth.isLoading} />
        <MetricCard title={t("dashboard:cards.processedToday")} value={processedToday} description={t("dashboard:metrics.processedDescription")} loading={auditEvents.isLoading} />
        <MetricCard title={t("dashboard:cards.recentErrors")} value={errors} description={t("dashboard:metrics.errorsDescription")} loading={auditEvents.isLoading} />
        <MetricCard title={t("dashboard:cards.pendingQueue")} value={pendingQueue} description={t("dashboard:metrics.pendingDescription")} loading={emailHealth.isLoading} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>{t("dashboard:recentActivity.title")}</CardTitle>
              <CardDescription>{t("dashboard:recentActivity.description")}</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/logs">{t("common:buttons.viewAll")}</Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {auditEvents.isLoading ? (
              Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} className="h-14 w-full" />)
            ) : auditEvents.data?.events.length ? (
              auditEvents.data.events.slice(0, 8).map((event) => (
                <div key={event.id} className="flex items-start justify-between gap-4 rounded-lg border border-border px-4 py-3">
                  <div>
                    <p className="text-sm font-medium">{event.subject ?? translateEventType(event.event_type)}</p>
                    <p className="text-xs text-muted-foreground">
                      {event.sender_email ?? t("common:systemLabel")} · {formatDate(event.created_at)}
                    </p>
                  </div>
                  <StatusBadge
                    label={translateEventType(event.event_type)}
                    tone={
                      event.event_type === "ingested"
                        ? "success"
                        : event.event_type === "failed"
                          ? "error"
                          : "neutral"
                    }
                  />
                </div>
              ))
            ) : (
              <div className="flex items-center gap-3 rounded-lg border border-dashed border-border px-4 py-8 text-sm text-muted-foreground">
                <AlertTriangle className="h-4 w-4" />
                {t("dashboard:recentActivity.empty")}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard:quickActions.title")}</CardTitle>
            <CardDescription>{t("dashboard:quickActions.description")}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <Button onClick={() => void poll()} disabled={isPolling}>
              {t("common:buttons.pollNow")}
            </Button>
            <Button variant="outline" asChild>
              <Link to="/email">{t("dashboard:quickActions.openEmail")}</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/maarch">{t("dashboard:quickActions.testMaarch")}</Link>
            </Button>
            <p className="text-xs text-muted-foreground">{t("dashboard:quickActions.workerNote")}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
