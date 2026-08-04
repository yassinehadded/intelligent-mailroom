import { useQuery } from "@tanstack/react-query";
import { Download, FileStack } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-dot";
import { useEnumTranslation, useLocalizedFormatters } from "@/lib/i18n-helpers";
import { downloadCsv } from "@/lib/utils";
import { auditApi } from "@/services/api";

export function DocumentsPage() {
  const { t } = useTranslation(["documents", "common"]);
  const { formatDate, formatPercent } = useLocalizedFormatters();
  const { translateCategory, translateEventType } = useEnumTranslation();
  const [search, setSearch] = useState("");
  const auditQuery = useQuery({
    queryKey: ["audit", "events", { limit: 200, event_type: "ingested" }],
    queryFn: () => auditApi.getEvents({ limit: 200, event_type: "ingested" }),
    refetchInterval: 20_000,
  });

  const rows = useMemo(() => {
    return (auditQuery.data?.events ?? []).filter((event) => {
      const haystack = `${event.subject ?? ""} ${event.sender_email ?? ""} ${event.res_id ?? ""}`.toLowerCase();
      return haystack.includes(search.toLowerCase());
    });
  }, [auditQuery.data?.events, search]);

  const exportCsv = () => {
    downloadCsv(
      "processed-documents.csv",
      [
        [
          t("documents:csvHeaders.reference"),
          t("documents:csvHeaders.subject"),
          t("documents:csvHeaders.sender"),
          t("documents:csvHeaders.destination"),
          t("documents:csvHeaders.maarchId"),
          t("documents:csvHeaders.processingDate"),
          t("documents:csvHeaders.category"),
          t("documents:csvHeaders.confidence"),
        ],
        ...rows.map((row) => [
          String(row.id),
          row.subject ?? "",
          row.sender_email ?? "",
          String(row.destination_serial_id ?? ""),
          String(row.res_id ?? ""),
          row.created_at,
          row.category ?? "",
          row.confidence != null ? String(row.confidence) : "",
        ]),
      ],
    );
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("documents:title")}
        description={t("documents:description")}
        actions={
          <Button variant="outline" onClick={exportCsv} disabled={!rows.length}>
            <Download className="h-4 w-4" />
            {t("common:buttons.exportCsv")}
          </Button>
        }
      />

      <Card>
        <CardHeader className="gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>{t("documents:registryTitle")}</CardTitle>
            <CardDescription>{t("documents:registryCount", { count: rows.length })}</CardDescription>
          </div>
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t("documents:searchPlaceholder")}
            className="max-w-sm"
          />
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {auditQuery.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, index) => (
                <Skeleton key={index} className="h-12 w-full" />
              ))}
            </div>
          ) : rows.length ? (
            <table className="w-full min-w-[960px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="px-3 py-3">{t("documents:columns.reference")}</th>
                  <th className="px-3 py-3">{t("documents:columns.subject")}</th>
                  <th className="px-3 py-3">{t("documents:columns.sender")}</th>
                  <th className="px-3 py-3">{t("documents:columns.destination")}</th>
                  <th className="px-3 py-3">{t("documents:columns.maarchId")}</th>
                  <th className="px-3 py-3">{t("documents:columns.processingDate")}</th>
                  <th className="px-3 py-3">{t("documents:columns.category")}</th>
                  <th className="px-3 py-3">{t("documents:columns.confidence")}</th>
                  <th className="px-3 py-3">{t("documents:columns.status")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} className="border-b border-border/70 hover:bg-muted/40">
                    <td className="px-3 py-3">#{row.id}</td>
                    <td className="px-3 py-3 font-medium">{row.subject ?? t("common:emptyValue")}</td>
                    <td className="px-3 py-3">{row.sender_email ?? t("common:emptyValue")}</td>
                    <td className="px-3 py-3">{row.destination_serial_id ?? t("common:emptyValue")}</td>
                    <td className="px-3 py-3">{row.res_id ?? t("common:emptyValue")}</td>
                    <td className="px-3 py-3">{formatDate(row.created_at)}</td>
                    <td className="px-3 py-3">{row.category ? translateCategory(row.category) : t("common:emptyValue")}</td>
                    <td className="px-3 py-3">{formatPercent(row.confidence ?? undefined)}</td>
                    <td className="px-3 py-3">
                      <StatusBadge label={translateEventType("ingested")} tone="success" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState
              title={t("documents:empty.title")}
              description={t("documents:empty.description")}
              icon={FileStack}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
