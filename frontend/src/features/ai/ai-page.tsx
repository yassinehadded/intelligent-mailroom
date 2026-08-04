import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowDown, Brain, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useEnumTranslation, useLocalizedFormatters } from "@/lib/i18n-helpers";
import { analysisApi } from "@/services/api";

export function AiPage() {
  const { t, i18n } = useTranslation(["ai", "common"]);
  const { formatPercent } = useLocalizedFormatters();
  const { translateCategory, translateEnabled } = useEnumTranslation();
  const [subject, setSubject] = useState("");
  const [bodyText, setBodyText] = useState("");
  const [sender, setSender] = useState("");

  useEffect(() => {
    setSubject(t("ai:samples.subject"));
    setBodyText(t("ai:samples.body"));
    setSender(t("ai:samples.sender"));
  }, [i18n.language, t]);

  const statusQuery = useQuery({
    queryKey: ["analysis", "status"],
    queryFn: analysisApi.getStatus,
  });

  const rulesQuery = useQuery({
    queryKey: ["analysis", "routing-rules"],
    queryFn: analysisApi.getRoutingRules,
  });

  const classifyMutation = useMutation({
    mutationFn: analysisApi.classify,
  });

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("ai:title")}
        description={t("ai:description")}
        actions={
          <Button
            onClick={() =>
              classifyMutation.mutate({
                subject,
                body_text: bodyText,
                sender,
              })
            }
            disabled={classifyMutation.isPending}
          >
            <Sparkles className="h-4 w-4" />
            {t("common:buttons.runClassification")}
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader>
            <CardDescription>{t("ai:provider")}</CardDescription>
            <CardTitle>{statusQuery.data?.ai_provider ?? t("common:emptyValue")}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>{t("ai:ocr")}</CardDescription>
            <CardTitle>{translateEnabled(statusQuery.data?.ocr_enabled ?? false)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>{t("ai:minConfidence")}</CardDescription>
            <CardTitle>{formatPercent(statusQuery.data?.classification_min_confidence)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>{t("ai:openai")}</CardDescription>
            <CardTitle>
              {statusQuery.data?.openai_configured ? t("ai:openaiConfigured") : t("ai:openaiNotConfigured")}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t("ai:routingRules")}</CardTitle>
            <CardDescription>{t("ai:routingRulesSource")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {rulesQuery.isLoading
              ? Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} className="h-24 w-full" />)
              : rulesQuery.data?.rules.map((rule) => (
                  <div key={rule.category} className="rounded-xl border border-border p-4">
                    <div className="flex items-center gap-3">
                      <Badge>{translateCategory(rule.category)}</Badge>
                      <ArrowDown className="h-4 w-4 text-muted-foreground" />
                      <Badge variant="secondary">{rule.entity_id}</Badge>
                    </div>
                    <p className="mt-3 text-sm text-muted-foreground">
                      {t("ai:keywords", {
                        value: rule.keywords.join(", ") || t("ai:defaultFallback"),
                      })}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {t("ai:doctypeKeywords", {
                        keywords: rule.doctype_keywords.join(", ") || t("common:emptyValue"),
                        id: rule.default_doctype_id ?? t("common:emptyValue"),
                      })}
                    </p>
                  </div>
                ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              {t("ai:playground")}
            </CardTitle>
            <CardDescription>{t("ai:playgroundSource")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input value={sender} onChange={(event) => setSender(event.target.value)} placeholder={t("ai:placeholders.sender")} />
            <Input value={subject} onChange={(event) => setSubject(event.target.value)} placeholder={t("ai:placeholders.subject")} />
            <Textarea value={bodyText} onChange={(event) => setBodyText(event.target.value)} placeholder={t("ai:placeholders.body")} />

            {classifyMutation.data ? (
              <div className="rounded-xl border border-border bg-muted/30 p-4">
                <p className="text-sm font-medium">{t("ai:decision")}</p>
                <div className="mt-3 grid gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{t("ai:fields.category")}</span>
                    <span>{translateCategory(classifyMutation.data.classification.category)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{t("ai:fields.destination")}</span>
                    <span>
                      {classifyMutation.data.classification.destination_entity_id} (
                      {classifyMutation.data.classification.destination_serial_id ?? t("common:emptyValue")})
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{t("ai:fields.doctype")}</span>
                    <span>
                      {classifyMutation.data.classification.doctype_label ??
                        classifyMutation.data.classification.doctype_id ??
                        t("common:emptyValue")}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{t("ai:fields.confidence")}</span>
                    <span>{formatPercent(classifyMutation.data.classification.confidence)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{t("ai:fields.method")}</span>
                    <span>{classifyMutation.data.classification.method}</span>
                  </div>
                </div>
                <p className="mt-4 text-sm text-muted-foreground">
                  {classifyMutation.data.classification.reasoning ?? t("ai:noReasoning")}
                </p>
                <p className="mt-3 rounded-lg bg-card p-3 text-xs text-muted-foreground">
                  {t("ai:ocrSource", { source: classifyMutation.data.ocr_source })}
                  <br />
                  {t("ai:preview", { text: classifyMutation.data.extracted_text_preview })}
                </p>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
