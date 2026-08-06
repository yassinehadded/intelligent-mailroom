import {
  Activity,
  Brain,
  FileStack,
  HelpCircle,
  LayoutDashboard,
  Mail,
  Moon,
  ScrollText,
  Settings,
  Sun,
  Workflow,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", labelKey: "nav.dashboard", icon: LayoutDashboard },
  { to: "/email", labelKey: "nav.email", icon: Mail },
  { to: "/ai", labelKey: "nav.ai", icon: Brain },
  { to: "/documents", labelKey: "nav.documents", icon: FileStack },
  { to: "/maarch", labelKey: "nav.maarch", icon: Workflow },
  { to: "/settings", labelKey: "nav.settings", icon: Settings },
  { to: "/logs", labelKey: "nav.logs", icon: ScrollText },
  { to: "/help", labelKey: "nav.help", icon: HelpCircle },
] as const;

export function Sidebar() {
  const { t } = useTranslation("common");

  return (
    <aside className="hidden w-64 shrink-0 border-r border-border rtl:border-r-0 rtl:border-l bg-card/50 lg:flex lg:flex-col">
      <div className="flex h-16 items-center gap-3 border-b border-border px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Activity className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold">{t("appName")}</p>
          <p className="text-xs text-muted-foreground">{t("appSubtitle")}</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-4 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary font-semibold"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {t(item.labelKey)}
          </NavLink>
        ))}

        <div className="pt-4">
          <div className="rounded-xl border border-primary/20 bg-primary/5 p-3.5 text-xs">
            <div className="flex items-center gap-2 font-semibold text-primary">
              <HelpCircle className="h-4 w-4" />
              <span>{t("nav.help")}</span>
            </div>
            <p className="mt-1 text-muted-foreground">
              Documentation, guides, FAQs & support.
            </p>
            <NavLink
              to="/help"
              className="mt-2.5 flex w-full items-center justify-center rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
            >
              Open Help Center
            </NavLink>
          </div>
        </div>
      </nav>
    </aside>
  );
}

export function ThemeToggle({ dark, onToggle }: { dark: boolean; onToggle: () => void }) {
  const { t } = useTranslation("common");

  return (
    <button
      type="button"
      onClick={onToggle}
      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
      aria-label={t("theme.toggle")}
    >
      {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}
