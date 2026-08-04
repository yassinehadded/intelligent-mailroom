import { cn } from "@/lib/utils";

type StatusTone = "success" | "warning" | "error" | "neutral" | "info";

const toneClasses: Record<StatusTone, string> = {
  success: "bg-success",
  warning: "bg-warning",
  error: "bg-destructive",
  neutral: "bg-muted-foreground",
  info: "bg-primary",
};

export function StatusDot({ tone = "neutral", className }: { tone?: StatusTone; className?: string }) {
  return <span className={cn("inline-block h-2 w-2 rounded-full", toneClasses[tone], className)} />;
}

export function StatusBadge({
  label,
  tone = "neutral",
}: {
  label: string;
  tone?: StatusTone;
}) {
  const variant =
    tone === "success"
      ? "success"
      : tone === "warning"
        ? "warning"
        : tone === "error"
          ? "destructive"
          : "secondary";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-medium",
        variant === "success" && "bg-success/10 text-success",
        variant === "warning" && "bg-warning/10 text-warning",
        variant === "destructive" && "bg-destructive/10 text-destructive",
        variant === "secondary" && "bg-secondary text-secondary-foreground",
      )}
    >
      <StatusDot tone={tone} />
      {label}
    </span>
  );
}
