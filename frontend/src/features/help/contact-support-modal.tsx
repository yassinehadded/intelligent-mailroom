import { AlertCircle, CheckCircle2, MessageSquare, Send, X } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface ContactSupportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ContactSupportModal({ isOpen, onClose }: ContactSupportModalProps) {
  const { t } = useTranslation("help");
  const [subject, setSubject] = useState("");
  const [category, setCategory] = useState("emailIngestion");
  const [priority, setPriority] = useState("medium");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !message.trim()) {
      toast.error(t("support.form.subjectPlaceholder") ? "Please complete all required fields." : "Champs requis");
      return;
    }

    setIsSubmitting(true);

    setTimeout(() => {
      setIsSubmitting(false);
      const ticketId = Math.floor(100000 + Math.random() * 900000).toString();

      toast.success(t("support.form.successTitle"), {
        description: t("support.form.successMessage", { id: ticketId }),
        icon: <CheckCircle2 className="h-5 w-5 text-emerald-500" />,
      });

      setSubject("");
      setMessage("");
      onClose();
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <Card className="relative w-full max-w-xl border-border bg-card p-6 shadow-xl sm:p-8">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
        >
          <X className="h-5 w-5" />
          <span className="sr-only">Close</span>
        </button>

        <div className="flex items-center gap-3 border-b border-border pb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <MessageSquare className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">{t("support.modalTitle")}</h2>
            <p className="text-xs text-muted-foreground">{t("support.modalDescription")}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              {t("support.form.subject")} <span className="text-destructive">*</span>
            </label>
            <Input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder={t("support.form.subjectPlaceholder")}
              required
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
                {t("support.form.category")}
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="gettingStarted">{t("categories.gettingStarted")}</option>
                <option value="emailIngestion">{t("categories.emailIngestion")}</option>
                <option value="aiClassification">{t("categories.aiClassification")}</option>
                <option value="maarchIntegration">{t("categories.maarchIntegration")}</option>
                <option value="troubleshooting">{t("categories.troubleshooting")}</option>
              </select>
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
                {t("support.form.priority")}
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="low">{t("support.form.priorityLow")}</option>
                <option value="medium">{t("support.form.priorityMedium")}</option>
                <option value="high">{t("support.form.priorityHigh")}</option>
              </select>
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              {t("support.form.message")} <span className="text-destructive">*</span>
            </label>
            <textarea
              rows={4}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={t("support.form.messagePlaceholder")}
              className="w-full rounded-lg border border-input bg-background p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              required
            />
          </div>

          <div className="flex items-center justify-between border-t border-border pt-4">
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <AlertCircle className="h-3.5 w-3.5 text-primary" /> Response time: ~24 hrs
            </p>

            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onClose}>
                {t("support.form.cancel")}
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  t("support.form.submitting")
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    {t("support.form.submit")}
                  </>
                )}
              </Button>
            </div>
          </div>
        </form>
      </Card>
    </div>
  );
}
