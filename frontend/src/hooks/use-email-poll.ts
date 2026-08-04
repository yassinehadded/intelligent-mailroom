import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { emailApi } from "@/services/api";
import { ApiError } from "@/lib/api-client";

const POLL_STEP_KEYS = [
  "poll.steps.connecting",
  "poll.steps.downloading",
  "poll.steps.extracting",
  "poll.steps.ocr",
  "poll.steps.classifying",
  "poll.steps.routing",
  "poll.steps.uploading",
  "poll.steps.completed",
] as const;

export function useEmailPoll() {
  const { t } = useTranslation("common");
  const queryClient = useQueryClient();
  const [activeStep, setActiveStep] = useState<number | null>(null);

  const steps = useMemo(() => POLL_STEP_KEYS.map((key) => t(key)), [t]);

  const mutation = useMutation({
    mutationFn: (limit?: number) => emailApi.poll(limit),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ["audit"] });
      void queryClient.invalidateQueries({ queryKey: ["email"] });
      toast.success(
        t("poll.success", {
          ingested: result.ingested,
          skipped: result.skipped,
        }),
      );
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.detail) : t("poll.failed");
      toast.error(message);
    },
  });

  const poll = useCallback(
    async (limit?: number) => {
      setActiveStep(0);
      const interval = window.setInterval(() => {
        setActiveStep((current) => {
          if (current === null || current >= steps.length - 2) return current;
          return current + 1;
        });
      }, 700);

      try {
        await mutation.mutateAsync(limit);
        setActiveStep(steps.length - 1);
      } finally {
        window.clearInterval(interval);
        window.setTimeout(() => setActiveStep(null), 1200);
      }
    },
    [mutation, steps.length],
  );

  return {
    poll,
    isPolling: mutation.isPending,
    activeStep,
    steps,
    lastResult: mutation.data,
    error: mutation.error,
  };
}
