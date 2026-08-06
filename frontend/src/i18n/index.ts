import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import arAi from "@/locales/ar/ai.json";
import arCommon from "@/locales/ar/common.json";
import arDashboard from "@/locales/ar/dashboard.json";
import arDocuments from "@/locales/ar/documents.json";
import arEmail from "@/locales/ar/email.json";
import arHelp from "@/locales/ar/help.json";
import arLogs from "@/locales/ar/logs.json";
import arMaarch from "@/locales/ar/maarch.json";
import arSettings from "@/locales/ar/settings.json";

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
  { code: "ar", label: "العربية 🇹🇳" },
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
      ar: {
        common: arCommon,
        dashboard: arDashboard,
        email: arEmail,
        ai: arAi,
        documents: arDocuments,
        maarch: arMaarch,
        settings: arSettings,
        logs: arLogs,
        help: arHelp,
      },
    },
    fallbackLng: "en",
    supportedLngs: ["en", "fr", "ar"],
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

const applyLanguageAttributes = (language: string) => {
  const isAr = language ? language.startsWith("ar") : false;
  document.documentElement.lang = isAr ? "ar" : language || "en";
  document.documentElement.dir = isAr ? "rtl" : "ltr";
};

i18n.on("languageChanged", (language) => {
  applyLanguageAttributes(language);
});

applyLanguageAttributes(i18n.language);

export default i18n;
