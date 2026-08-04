import { useQuery } from "@tanstack/react-query";
import { ExternalLink, RefreshCw, Workflow } from "lucide-react";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-dot";
import { useEnumTranslation } from "@/lib/i18n-helpers";
import { maarchApi } from "@/services/api";

export function MaarchPage() {
  const { t } = useTranslation(["maarch", "common"]);
  const { translateYesNo, translateStatus } = useEnumTranslation();

  const connectionQuery = useQuery({
    queryKey: ["maarch", "connection"],
    queryFn: maarchApi.getConnection,
    retry: false,
  });

  const healthQuery = useQuery({
    queryKey: ["maarch", "health"],
    queryFn: maarchApi.getHealth,
    retry: false,
  });

  const entitiesQuery = useQuery({
    queryKey: ["maarch", "entities"],
    queryFn: maarchApi.getEntities,
    retry: false,
  });

  const referenceQuery = useQuery({
    queryKey: ["maarch", "reference"],
    queryFn: maarchApi.getReference,
    retry: false,
  });

  const refreshAll = () => {
    void connectionQuery.refetch();
    void healthQuery.refetch();
    void entitiesQuery.refetch();
    void referenceQuery.refetch();
  };

  const defaultStatus = referenceQuery.data?.defaults.status
    ? translateStatus(referenceQuery.data.defaults.status)
    : t("common:emptyValue");

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("maarch:title")}
        description={t("maarch:description")}
        actions={
          <>
            <Button variant="outline" onClick={refreshAll}>
              <RefreshCw className="h-4 w-4" />
              {t("common:buttons.reloadMetadata")}
            </Button>
            <Button asChild>
              <a href={healthQuery.data?.maarch_url ?? "http://localhost:8081"} target="_blank" rel="noreferrer">
                {t("common:buttons.openMaarch")}
                <ExternalLink className="h-4 w-4" />
              </a>
            </Button>
          </>
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Workflow className="h-4 w-4" />
              {t("maarch:connection")}
            </CardTitle>
            <CardDescription>{t("maarch:connectionSource")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {connectionQuery.isLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">{t("maarch:fields.connected")}</span>
                  <StatusBadge
                    label={translateYesNo(connectionQuery.data?.connected ?? false)}
                    tone={connectionQuery.data?.connected ? "success" : "error"}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">{t("maarch:fields.webserviceReady")}</span>
                  <span>{translateYesNo(connectionQuery.data?.webservice_ready ?? false)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">{t("maarch:fields.currentUser")}</span>
                  <span>{connectionQuery.data?.current_user ?? t("common:emptyValue")}</span>
                </div>
                {(connectionQuery.data?.warnings ?? []).map((warning) => (
                  <p key={warning} className="rounded-lg bg-warning/10 px-3 py-2 text-warning">
                    {warning}
                  </p>
                ))}
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("maarch:authentication")}</CardTitle>
            <CardDescription>{t("maarch:authenticationSource")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {healthQuery.isLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">{t("maarch:fields.application")}</span>
                  <span>{healthQuery.data?.application_name ?? t("common:emptyValue")}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">{t("maarch:fields.authMode")}</span>
                  <Badge variant="secondary">{healthQuery.data?.auth_mode ?? t("common:emptyValue")}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">{t("maarch:fields.maarchUrl")}</span>
                  <span className="truncate">{healthQuery.data?.maarch_url ?? t("common:emptyValue")}</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t("maarch:entities")}</CardTitle>
            <CardDescription>{t("maarch:entitiesCount", { count: entitiesQuery.data?.count ?? 0 })}</CardDescription>
          </CardHeader>
          <CardContent className="max-h-[420px] space-y-2 overflow-y-auto">
            {entitiesQuery.isLoading ? (
              Array.from({ length: 6 }).map((_, index) => <Skeleton key={index} className="h-10 w-full" />)
            ) : (
              entitiesQuery.data?.entities.map((entity) => (
                <div key={entity.serialId} className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm">
                  <div>
                    <p className="font-medium">{entity.shortLabel ?? entity.id}</p>
                    <p className="text-xs text-muted-foreground">{entity.id}</p>
                  </div>
                  <Badge variant="outline">#{entity.serialId}</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("maarch:referenceMetadata")}</CardTitle>
            <CardDescription>{t("maarch:referenceDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {referenceQuery.isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : (
              <>
                <div>
                  <p className="mb-2 font-medium">{t("maarch:fields.defaults")}</p>
                  <div className="rounded-lg border border-border p-3 text-muted-foreground">
                    {t("maarch:defaultsSummary", {
                      modelId: referenceQuery.data?.defaults.model_id ?? t("common:emptyValue"),
                      status: defaultStatus,
                      attachmentType: referenceQuery.data?.defaults.attachment_type ?? t("common:emptyValue"),
                    })}
                  </div>
                </div>
                <div>
                  <p className="mb-2 font-medium">{t("maarch:fields.indexingModels")}</p>
                  <div className="space-y-2">
                    {referenceQuery.data?.indexing_models.slice(0, 8).map((model) => (
                      <div key={model.id} className="flex justify-between rounded-lg border border-border px-3 py-2">
                        <span>{model.label}</span>
                        <Badge variant="secondary">{model.id}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
