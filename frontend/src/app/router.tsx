import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/app-shell";
import { AiPage } from "@/features/ai/ai-page";
import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { DocumentsPage } from "@/features/documents/documents-page";
import { EmailPage } from "@/features/email/email-page";
import { HelpPage } from "@/features/help/help-page";
import { LogsPage } from "@/features/logs/logs-page";
import { MaarchPage } from "@/features/maarch/maarch-page";
import { SettingsPage } from "@/features/settings/settings-page";

export function AppRouter() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="email" element={<EmailPage />} />
        <Route path="ai" element={<AiPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="maarch" element={<MaarchPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="logs" element={<LogsPage />} />
        <Route path="help" element={<HelpPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
