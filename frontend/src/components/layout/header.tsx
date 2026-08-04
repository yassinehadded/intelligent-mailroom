import { Menu } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { ThemeToggle } from "@/components/layout/sidebar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const mobileNav = [
  { to: "/", labelKey: "nav.dashboard" },
  { to: "/email", labelKey: "nav.email" },
  { to: "/ai", labelKey: "nav.ai" },
  { to: "/documents", labelKey: "nav.documents" },
  { to: "/maarch", labelKey: "nav.maarch" },
  { to: "/settings", labelKey: "nav.settings" },
  { to: "/logs", labelKey: "nav.logs" },
] as const;

export function Header({
  dark,
  onToggleTheme,
}: {
  dark: boolean;
  onToggleTheme: () => void;
}) {
  const { t } = useTranslation("common");
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
      <div className="flex h-16 items-center justify-between gap-3 px-4 lg:px-8">
        <div className="flex min-w-0 flex-1 items-center gap-3 lg:hidden">
          <Button variant="outline" size="icon" onClick={() => setOpen((value) => !value)}>
            <Menu className="h-4 w-4" />
          </Button>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">{t("appName")}</p>
            <p className="truncate text-xs text-muted-foreground">{t("appSubtitle")}</p>
          </div>
        </div>
        <div className="hidden min-w-0 flex-1 lg:block">
          <p className="text-sm text-muted-foreground">{t("appTagline")}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <LanguageSwitcher />
          <ThemeToggle dark={dark} onToggle={onToggleTheme} />
        </div>
      </div>
      {open ? (
        <nav className="border-t border-border px-4 py-3 lg:hidden">
          <div className="grid gap-1">
            {mobileNav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  cn(
                    "rounded-lg px-3 py-2 text-sm font-medium",
                    isActive ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-accent",
                  )
                }
              >
                {t(item.labelKey)}
              </NavLink>
            ))}
          </div>
        </nav>
      ) : null}
    </header>
  );
}
