import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Outlet } from "react-router-dom";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { useTheme } from "@/hooks/use-theme";

export function AppShell() {
  const { dark, toggleTheme } = useTheme();
  const { t, i18n } = useTranslation("common");

  useEffect(() => {
    document.title = t("appName");
  }, [t, i18n.language]);

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header dark={dark} onToggleTheme={toggleTheme} />
        <main className="flex-1 px-4 py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
