import { useTranslation } from "react-i18next";

export function getLocaleCode(language: string): string {
  return language.startsWith("fr") ? "fr-FR" : "en-US";
}

export function formatDateLocalized(value: string | null | undefined, locale: string): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "long",
    timeStyle: "short",
  }).format(date);
}

export function formatPercentLocalized(value: number | null | undefined, locale: string): string {
  if (value == null) return "—";
  return new Intl.NumberFormat(locale, {
    style: "percent",
    maximumFractionDigits: 0,
  }).format(value);
}

export function useLocalizedFormatters() {
  const { i18n } = useTranslation();
  const locale = getLocaleCode(i18n.language);

  return {
    locale,
    formatDate: (value: string | null | undefined) => formatDateLocalized(value, locale),
    formatPercent: (value: number | null | undefined) => formatPercentLocalized(value, locale),
  };
}

export function useEnumTranslation() {
  const { t } = useTranslation("common");

  return {
    translateStatus: (status: string) => t(`maarchStatus.${status}`, { defaultValue: status }),
    translateCategory: (category: string) => t(`category.${category}`, { defaultValue: category }),
    translateEventType: (eventType: string) => t(`eventType.${eventType}`, { defaultValue: eventType }),
    translateSystem: (key: string) => t(`system.${key}`, { defaultValue: key }),
    translateYesNo: (value: boolean) => (value ? t("yes") : t("no")),
    translateEnabled: (value: boolean) => (value ? t("enabled") : t("disabled")),
  };
}
