import {
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  FileCode,
  Layers,
  Wrench,
} from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

interface GuideItem {
  id: string;
  category: string;
  title: string;
  description: string;
  readTime: string;
  steps: string[];
}

interface GuidesGridProps {
  categoryFilter: string;
  searchQuery: string;
}

export function GuidesGrid({ categoryFilter, searchQuery }: GuidesGridProps) {
  const { t } = useTranslation("help");
  const [expandedId, setExpandedId] = useState<string | null>("workflow-overview");

  const guideItems = t("guides.items", { returnObjects: true }) as GuideItem[];

  const filteredGuides = (guideItems || []).filter((guide) => {
    const matchesCategory =
      categoryFilter === "all" || guide.category === categoryFilter;
    const matchesSearch =
      !searchQuery.trim() ||
      guide.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      guide.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      guide.steps.some((step) =>
        step.toLowerCase().includes(searchQuery.toLowerCase()),
      );
    return matchesCategory && matchesSearch;
  });

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case "aiClassification":
        return <Brain className="h-5 w-5 text-purple-500" />;
      case "maarchIntegration":
        return <FileCode className="h-5 w-5 text-blue-500" />;
      case "troubleshooting":
        return <Wrench className="h-5 w-5 text-amber-500" />;
      default:
        return <Layers className="h-5 w-5 text-emerald-500" />;
    }
  };

  if (filteredGuides.length === 0) return null;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold tracking-tight">{t("guides.title")}</h2>
        <p className="text-sm text-muted-foreground">{t("guides.subtitle")}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {filteredGuides.map((guide) => {
          const isExpanded = expandedId === guide.id;

          return (
            <Card
              key={guide.id}
              className={`flex flex-col justify-between border-border transition-all duration-200 ${isExpanded ? "ring-2 ring-primary/40 bg-card shadow-md" : "hover:border-primary/50"
                }`}
            >
              <div className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent">
                    {getCategoryIcon(guide.category)}
                  </div>
                  <Badge variant="outline" className="text-xs font-medium text-muted-foreground">
                    <Clock className="mr-1 h-3 w-3" />
                    {guide.readTime}
                  </Badge>
                </div>

                <h3 className="mt-3 text-base font-semibold text-foreground">{guide.title}</h3>
                <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                  {guide.description}
                </p>

                {/* Expandable Step-by-Step Instructions */}
                {isExpanded && (
                  <div className="mt-4 border-t border-border pt-4 animate-in fade-in duration-150">
                    <p className="mb-2 text-xs font-semibold text-foreground">Implementation Steps:</p>
                    <ol className="space-y-2">
                      {guide.steps.map((step, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-xs text-muted-foreground">
                          <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" />
                          <span>{step}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>

              <div className="border-t border-border bg-muted/30 px-5 py-3">
                <button
                  type="button"
                  onClick={() => setExpandedId(isExpanded ? null : guide.id)}
                  className="flex w-full items-center justify-between text-xs font-medium text-primary hover:underline"
                >
                  <span>{isExpanded ? "Hide Steps" : "View Step-by-Step Guide"}</span>
                  {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
