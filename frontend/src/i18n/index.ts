import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import enAi from "@/locales/en/ai.json";
import enCommon from "@/locales/en/common.json";
import enDashboard from "@/locales/en/dashboard.json";
import enDocuments from "@/locales/en/documents.json";
import enEmail from "@/locales/en/email.json";
import enHelp from "@/locales/en/help.json";
import enLogs from "@/locales/en/logs.json";
import enMaarch from "@/locales/en/maarch.json";
import enSettings from "@/locales/en/settings.json";

import frAi from "@/locales/fr/ai.json";
import frCommon from "@/locales/fr/common.json";
import frDashboard from "@/locales/fr/dashboard.json";
import frDocuments from "@/locales/fr/documents.json";
import frEmail from "@/locales/fr/email.json";
import frHelp from "@/locales/fr/help.json";
import frLogs from "@/locales/fr/logs.json";
import frMaarch from "@/locales/fr/maarch.json";
import frSettings from "@/locales/fr/settings.json";

export const LANGUAGE_STORAGE_KEY = "mailroom-language";

export const supportedLanguages = [
  { code: "en", label: "English" },
  { code: "fr", label: "Français" },
] as const;

export type SupportedLanguage = (typeof supportedLanguages)[number]["code"];

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        common: enCommon,
        dashboard: enDashboard,
        email: enEmail,
        ai: enAi,
        documents: enDocuments,
        maarch: enMaarch,
        settings: enSettings,
        logs: enLogs,
        help: enHelp,
      },
      fr: {
        common: frCommon,
        dashboard: frDashboard,
        email: frEmail,
        ai: frAi,
        documents: frDocuments,
        maarch: frMaarch,
        settings: frSettings,
        logs: frLogs,
        help: frHelp,
      },
    },
    fallbackLng: "en",
    supportedLngs: ["en", "fr"],
    defaultNS: "common",
    ns: ["common", "dashboard", "email", "ai", "documents", "maarch", "settings", "logs", "help"],
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
      lookupLocalStorage: LANGUAGE_STORAGE_KEY,
    },
  });

i18n.on("languageChanged", (language) => {
  document.documentElement.lang = language;
});

document.documentElement.lang = i18n.language;

export default i18n;
