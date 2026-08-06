import { ChevronDown, Globe } from "lucide-react";
import { useTranslation } from "react-i18next";
import { supportedLanguages } from "@/i18n";
import { cn } from "@/lib/utils";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation("common");
  const currentLang = i18n.language.startsWith("ar")
    ? "ar"
    : i18n.language.startsWith("fr")
      ? "fr"
      : "en";
  const current = supportedLanguages.find((lang) => lang.code === currentLang) ?? supportedLanguages[0];

  return (
    <div className="relative shrink-0">
      <label htmlFor="language-select" className="sr-only">
        {t("language.label")}
      </label>
      <div className="relative flex items-center gap-1.5 rounded-lg border border-border bg-card px-2.5 py-1.5 shadow-sm">
        <Globe className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
        <select
          id="language-select"
          value={currentLang}
          onChange={(event) => void i18n.changeLanguage(event.target.value)}
          className={cn(
            "max-w-[8.5rem] cursor-pointer appearance-none bg-transparent py-0.5 pr-6 pl-0 rtl:pl-6 rtl:pr-0 text-sm font-medium text-foreground",
            "focus:outline-none focus:ring-0",
          )}
        >
          {supportedLanguages.map((language) => (
            <option key={language.code} value={language.code}>
              {language.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-2 rtl:right-auto rtl:left-2 h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
      </div>
      <span className="sr-only">{t("language.current", { language: current.label })}</span>
    </div>
  );
}
