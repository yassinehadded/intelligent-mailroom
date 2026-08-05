import { LifeBuoy, MessageSquare, PhoneCall, ShieldCheck, Zap } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ContactSupportModal } from "@/features/help/contact-support-modal";
import { FaqAccordion } from "@/features/help/faq-accordion";
import { GuidesGrid } from "@/features/help/guides-grid";
import { HelpHero } from "@/features/help/help-hero";

export function HelpPage() {
  const { t } = useTranslation("help");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");
  const [isSupportModalOpen, setIsSupportModalOpen] = useState(false);

  return (
    <div className="space-y-8 pb-12">
      <PageHeader title={t("title")} description={t("subtitle")} />

      {/* Hero Search Section */}
      <HelpHero
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        activeCategory={activeCategory}
        onCategorySelect={setActiveCategory}
      />

      {/* Highlights / Quick Stats Bar */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="flex items-center gap-4 border-border p-4 shadow-sm">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-500/10 text-blue-500">
            <Zap className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Automated Processing</p>
            <p className="text-sm font-semibold">24/7 Pipeline Monitoring</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4 border-border p-4 shadow-sm">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Enterprise Security</p>
            <p className="text-sm font-semibold">Maarch API v2 Verified</p>
          </div>
        </Card>

        <Card className="flex items-center gap-4 border-border p-4 shadow-sm">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-purple-500/10 text-purple-500">
            <PhoneCall className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Support SLA</p>
            <p className="text-sm font-semibold">24 Hours Response Time</p>
          </div>
        </Card>
      </div>

      {/* User Guides Section */}
      <GuidesGrid categoryFilter={activeCategory} searchQuery={searchQuery} />

      {/* FAQ Section */}
      <FaqAccordion categoryFilter={activeCategory} searchQuery={searchQuery} />

      {/* Still Need Help CTA Banner */}
      <Card className="relative overflow-hidden border-primary/20 bg-gradient-to-r from-primary/10 via-background to-card p-6 shadow-soft md:p-8">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <LifeBuoy className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-bold">{t("support.title")}</h3>
            </div>
            <p className="text-xs text-muted-foreground max-w-xl">
              {t("support.subtitle")}
            </p>
          </div>

          <Button
            size="lg"
            onClick={() => setIsSupportModalOpen(true)}
            className="shrink-0 font-semibold shadow-md"
          >
            <MessageSquare className="mr-2 h-4 w-4" />
            {t("support.button")}
          </Button>
        </div>
      </Card>

      {/* Interactive Contact Support Ticket Modal */}
      <ContactSupportModal
        isOpen={isSupportModalOpen}
        onClose={() => setIsSupportModalOpen(false)}
      />
    </div>
  );
}
