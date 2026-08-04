import { ChevronDown, Globe } from "lucide-react";
import { useTranslation } from "react-i18next";
import { supportedLanguages } from "@/i18n";
import { cn } from "@/lib/utils";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation("common");
  const current = supportedLanguages.find((lang) => lang.code === i18n.language) ?? supportedLanguages[0];

  return (
    <div className="relative shrink-0">
      <label htmlFor="language-select" className="sr-only">
        {t("language.label")}
      </label>
      <div className="relative flex items-center gap-1.5 rounded-lg border border-border bg-card px-2.5 py-1.5 shadow-sm">
        <Globe className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
        <span className="text-base leading-none" aria-hidden="true">
          🌐
        </span>
        <select
          id="language-select"
          value={i18n.language.startsWith("fr") ? "fr" : "en"}
          onChange={(event) => void i18n.changeLanguage(event.target.value)}
          className={cn(
            "max-w-[7.5rem] cursor-pointer appearance-none bg-transparent py-0.5 pr-6 pl-0 text-sm font-medium text-foreground",
            "focus:outline-none focus:ring-0",
          )}
        >
          {supportedLanguages.map((language) => (
            <option key={language.code} value={language.code}>
              {language.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-2 h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
      </div>
      <span className="sr-only">{t("language.current", { language: current.label })}</span>
    </div>
  );
}
