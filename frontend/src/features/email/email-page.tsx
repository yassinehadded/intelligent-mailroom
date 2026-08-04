import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Loader2, Mail, RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-dot";
import { useEmailPoll } from "@/hooks/use-email-poll";
import { useEnumTranslation, useLocalizedFormatters } from "@/lib/i18n-helpers";
import { auditApi, emailApi } from "@/services/api";
import type { AuditEvent } from "@/types/api";

type MailboxRow = AuditEvent & { statusLabel: string; statusTone: "success" | "error" | "neutral" };

export function EmailPage() {
  const { t, i18n } = useTranslation(["email", "common"]);
  const { formatDate, formatPercent } = useLocalizedFormatters();
  const { translateEventType, translateCategory, translateSystem } = useEnumTranslation();
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<number[]>([]);
  const { poll, isPolling, activeStep, steps } = useEmailPoll();

  const statusQuery = useQuery({
    queryKey: ["email", "status"],
    queryFn: emailApi.getStatus,
  });

  const healthQuery = useQuery({
    queryKey: ["email", "health"],
    queryFn: emailApi.getHealth,
    retry: false,
  });

  const auditQuery = useQuery({
    queryKey: ["audit", "events", { limit: 100 }],
    queryFn: () => auditApi.getEvents({ limit: 100 }),
    refetchInterval: 15_000,
  });

  const rows = useMemo<MailboxRow[]>(() => {
    return (auditQuery.data?.events ?? []).map((event) => ({
      ...event,
      statusLabel: translateEventType(event.event_type),
      statusTone:
        event.event_type === "ingested" ? "success" : event.event_type === "failed" ? "error" : "neutral",
    }));
  }, [auditQuery.data?.events, i18n.language, translateEventType]);

  const filtered = rows.filter((row) => {
    const haystack = `${row.subject ?? ""} ${row.sender_email ?? ""} ${row.category ?? ""}`.toLowerCase();
    return haystack.includes(search.toLowerCase());
  });

  const toggleAll = () => {
    setSelected((current) => (current.length === filtered.length ? [] : filtered.map((row) => row.id)));
  };

  const healthStatus = healthQuery.data?.status
    ? translateSystem(healthQuery.data.status)
    : healthQuery.isError
      ? t("common:unavailable")
      : t("common:checking");

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("email:title")}
        description={t("email:description")}
        actions={
          <>
            <Button variant="outline" onClick={() => auditQuery.refetch()}>
              <RefreshCw className="h-4 w-4" />
              {t("common:buttons.refresh")}
            </Button>
            <Button onClick={() => void poll()} disabled={isPolling}>
              {isPolling ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {t("common:buttons.pollNow")}
            </Button>
          </>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>{t("email:mailbox")}</CardDescription>
            <CardTitle>{statusQuery.data?.mailbox ?? t("common:emptyValue")}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {statusQuery.data?.host ?? t("common:notConfigured")} · {t("email:limit", { count: statusQuery.data?.fetch_limit ?? t("common:emptyValue") })}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>{t("email:imapHealth")}</CardDescription>
            <CardTitle>{healthStatus}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {t("email:unseenMessages", { count: healthQuery.data?.unseen_count ?? t("common:emptyValue") })}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>{t("email:selection")}</CardDescription>
            <CardTitle>{t("email:selectedCount", { count: selected.length })}</CardTitle>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button size="sm" variant="outline" onClick={toggleAll}>
              {t("common:buttons.selectAll")}
            </Button>
            <Button size="sm" onClick={() => void poll()} disabled={isPolling}>
              {t("common:buttons.process")}
            </Button>
          </CardContent>
        </Card>
      </div>

      {activeStep !== null ? (
        <Card>
          <CardHeader>
            <CardTitle>{t("email:liveProcessing")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {steps.map((step, index) => (
              <div key={step} className="flex items-center gap-2 text-sm">
                {index <= activeStep ? <CheckCircle2 className="h-4 w-4 text-success" /> : <span className="h-4 w-4 rounded-full border" />}
                {step}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader className="gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>{t("email:historyTitle")}</CardTitle>
            <CardDescription>{t("email:historyDescription")}</CardDescription>
          </div>
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t("email:searchPlaceholder")}
            className="max-w-sm"
          />
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {auditQuery.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={index} className="h-12 w-full" />
              ))}
            </div>
          ) : filtered.length ? (
            <table className="w-full min-w-[960px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="px-3 py-3">
                    <input
                      type="checkbox"
                      checked={selected.length === filtered.length && filtered.length > 0}
                      onChange={toggleAll}
                    />
                  </th>
                  <th className="px-3 py-3">{t("email:columns.sender")}</th>
                  <th className="px-3 py-3">{t("email:columns.subject")}</th>
                  <th className="px-3 py-3">{t("email:columns.received")}</th>
                  <th className="px-3 py-3">{t("email:columns.status")}</th>
                  <th className="px-3 py-3">{t("email:columns.aiCategory")}</th>
                  <th className="px-3 py-3">{t("email:columns.destination")}</th>
                  <th className="px-3 py-3">{t("email:columns.confidence")}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr key={row.id} className="border-b border-border/70 hover:bg-muted/40">
                    <td className="px-3 py-3">
                      <input
                        type="checkbox"
                        checked={selected.includes(row.id)}
                        onChange={() =>
                          setSelected((current) =>
                            current.includes(row.id)
                              ? current.filter((id) => id !== row.id)
                              : [...current, row.id],
                          )
                        }
                      />
                    </td>
                    <td className="px-3 py-3">{row.sender_email ?? t("common:emptyValue")}</td>
                    <td className="px-3 py-3 font-medium">{row.subject ?? t("common:emptyValue")}</td>
                    <td className="px-3 py-3">{formatDate(row.created_at)}</td>
                    <td className="px-3 py-3">
                      <StatusBadge label={row.statusLabel} tone={row.statusTone} />
                    </td>
                    <td className="px-3 py-3">{row.category ? translateCategory(row.category) : t("common:emptyValue")}</td>
                    <td className="px-3 py-3">{row.destination_serial_id ?? t("common:emptyValue")}</td>
                    <td className="px-3 py-3">{formatPercent(row.confidence ?? undefined)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState
              title={t("email:empty.title")}
              description={t("email:empty.description")}
              icon={Mail}
              action={
                <Button onClick={() => void poll()} disabled={isPolling}>
                  {t("common:buttons.pollNow")}
                </Button>
              }
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
