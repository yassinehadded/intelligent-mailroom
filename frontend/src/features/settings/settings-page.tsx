import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Settings2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useEnumTranslation, useLocalizedFormatters } from "@/lib/i18n-helpers";
import { analysisApi, emailApi, maarchApi } from "@/services/api";

export function SettingsPage() {
  const { t } = useTranslation(["settings", "common"]);
  const { translateYesNo, translateEnabled, translateStatus } = useEnumTranslation();
  const { formatPercent } = useLocalizedFormatters();

  const emailStatus = useQuery({ queryKey: ["email", "status"], queryFn: emailApi.getStatus });
  const analysisStatus = useQuery({ queryKey: ["analysis", "status"], queryFn: analysisApi.getStatus });
  const maarchHealth = useQuery({ queryKey: ["maarch", "health"], queryFn: maarchApi.getHealth, retry: false });
  const maarchReference = useQuery({ queryKey: ["maarch", "reference"], queryFn: maarchApi.getReference, retry: false });

  const loading = emailStatus.isLoading || analysisStatus.isLoading;

  return (
    <div className="space-y-8">
      <PageHeader title={t("settings:title")} description={t("settings:description")} />

      <Card className="border-warning/30 bg-warning/5">
        <CardContent className="flex items-start gap-3 p-4 text-sm">
          <AlertCircle className="mt-0.5 h-4 w-4 text-warning" />
          <div>
            <p className="font-medium">{t("settings:backendNoticeTitle")}</p>
            <p className="mt-1 text-muted-foreground">{t("settings:backendNoticeDescription")}</p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings2 className="h-4 w-4" />
              {t("settings:emailSection")}
            </CardTitle>
            <CardDescription>{t("settings:emailSource")}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            {loading ? (
              <Skeleton className="h-40 w-full" />
            ) : (
              <>
                <Field label={t("settings:fields.configured")} value={translateYesNo(emailStatus.data?.configured ?? false)} />
                <Field label={t("settings:fields.host")} value={emailStatus.data?.host ?? t("common:emptyValue")} />
                <Field label={t("settings:fields.mailbox")} value={emailStatus.data?.mailbox ?? t("common:emptyValue")} />
                <Field label={t("settings:fields.fetchLimit")} value={String(emailStatus.data?.fetch_limit ?? t("common:emptyValue"))} />
                <Field label={t("settings:fields.defaultDestination")} value={String(emailStatus.data?.default_destination ?? t("common:emptyValue"))} />
                <Field label={t("settings:fields.markAsRead")} value={translateYesNo(emailStatus.data?.mark_as_read ?? false)} />
                <Input disabled value="••••••••" aria-label={t("settings:passwordHidden")} />
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("settings:aiSection")}</CardTitle>
            <CardDescription>{t("settings:aiSource")}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            {loading ? (
              <Skeleton className="h-40 w-full" />
            ) : (
              <>
                <Field label={t("settings:fields.aiEnabled")} value={translateYesNo(analysisStatus.data?.ai_enabled ?? false)} />
                <Field label={t("settings:fields.provider")} value={analysisStatus.data?.ai_provider ?? t("common:emptyValue")} />
                <Field label={t("settings:fields.openaiConfigured")} value={translateYesNo(analysisStatus.data?.openai_configured ?? false)} />
                <Field label={t("settings:fields.ocrEnabled")} value={translateEnabled(analysisStatus.data?.ocr_enabled ?? false)} />
                <Field label={t("settings:fields.tesseractEnabled")} value={translateEnabled(analysisStatus.data?.ocr_tesseract_enabled ?? false)} />
                <Field
                  label={t("settings:fields.confidenceThreshold")}
                  value={analysisStatus.data ? formatPercent(analysisStatus.data.classification_min_confidence) : t("common:emptyValue")}
                />
              </>
            )}
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>{t("settings:maarchSection")}</CardTitle>
            <CardDescription>{t("settings:maarchSource")}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <Field label={t("settings:fields.application")} value={maarchHealth.data?.application_name ?? t("common:emptyValue")} />
            <Field label={t("settings:fields.authMode")} value={maarchHealth.data?.auth_mode ?? t("common:emptyValue")} />
            <Field label={t("settings:fields.maarchUrl")} value={maarchHealth.data?.maarch_url ?? t("common:emptyValue")} />
            <Field label={t("settings:fields.defaultModel")} value={String(maarchReference.data?.defaults.model_id ?? t("common:emptyValue"))} />
            <Field
              label={t("settings:fields.defaultStatus")}
              value={
                maarchReference.data?.defaults.status
                  ? translateStatus(maarchReference.data.defaults.status)
                  : t("common:emptyValue")
              }
            />
            <Field label={t("settings:fields.attachmentType")} value={maarchReference.data?.defaults.attachment_type ?? t("common:emptyValue")} />
            <div className="md:col-span-2">
              <Badge variant="secondary">{t("settings:credentialsHidden")}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-muted-foreground">{label}</label>
      <Input readOnly value={value} />
    </div>
  );
}
