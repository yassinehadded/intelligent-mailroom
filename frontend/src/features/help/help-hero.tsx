import { LifeBuoy, Search, Sparkles, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

interface HelpHeroProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  activeCategory: string;
  onCategorySelect: (category: string) => void;
}

export function HelpHero({
  searchQuery,
  onSearchChange,
  activeCategory,
  onCategorySelect,
}: HelpHeroProps) {
  const { t } = useTranslation("help");

  const categories = [
    { id: "all", label: t("categories.all") },
    { id: "gettingStarted", label: t("categories.gettingStarted") },
    { id: "emailIngestion", label: t("categories.emailIngestion") },
    { id: "aiClassification", label: t("categories.aiClassification") },
    { id: "maarchIntegration", label: t("categories.maarchIntegration") },
    { id: "troubleshooting", label: t("categories.troubleshooting") },
  ];

  const quickSearches = ["IMAP", "OCR", "Maarch API", "Threshold", "Logs"];

  return (
    <div className="relative overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-primary/10 via-background to-card p-6 shadow-soft md:p-10">
      <div className="absolute right-0 top-0 -mr-16 -mt-16 h-64 w-64 rounded-full bg-primary/5 blur-3xl" />

      <div className="relative z-10 mx-auto max-w-3xl text-center">
        <Badge variant="outline" className="mb-3 border-primary/20 bg-primary/10 text-primary">
          <LifeBuoy className="mr-1.5 h-3.5 w-3.5" />
          {t("hero.badge")}
        </Badge>

        <h1 className="text-2xl font-bold tracking-tight sm:text-4xl">
          {t("hero.tagline")}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground sm:text-base">
          {t("subtitle")}
        </p>

        {/* Search Input Bar */}
        <div className="relative mt-6">
          <Search className="absolute left-4 top-3.5 h-5 w-5 text-muted-foreground" />
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={t("searchPlaceholder")}
            className="h-12 border-border bg-card/90 pl-12 pr-10 text-base shadow-sm backdrop-blur transition-all focus-visible:ring-2 focus-visible:ring-primary"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange("")}
              className="absolute right-3.5 top-3.5 rounded-full p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Quick Search Tag Chips */}
        <div className="mt-3 flex flex-wrap items-center justify-center gap-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-primary" /> {t("hero.quickLinksTitle")}
          </span>
          {quickSearches.map((term) => (
            <button
              key={term}
              type="button"
              onClick={() => onSearchChange(term)}
              className="rounded-md border border-border/80 bg-background/80 px-2 py-0.5 font-medium transition-colors hover:border-primary hover:bg-primary/5 hover:text-primary"
            >
              {term}
            </button>
          ))}
        </div>

        {/* Category Filters */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
          {categories.map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => onCategorySelect(cat.id)}
              className={`rounded-xl px-4 py-2 text-xs font-semibold transition-all ${activeCategory === cat.id
                  ? "bg-primary text-primary-foreground shadow-md"
                  : "border border-border bg-card text-muted-foreground hover:bg-accent hover:text-foreground"
                }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
