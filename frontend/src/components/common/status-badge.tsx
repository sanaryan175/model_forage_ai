import { AlertTriangle, CheckCircle2, CircleDashed, Loader2, OctagonX, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { JobStatus, ModelStatus } from "@/types/api";

type Status = JobStatus | ModelStatus | "invalid" | "ready";

const CONFIG: Record<string, { label: string; className: string; icon: React.ElementType; spin?: boolean }> = {
  queued: { label: "Queued", className: "bg-muted text-muted-foreground border-border", icon: CircleDashed },
  uploading: { label: "Uploading", className: "bg-muted text-muted-foreground border-border", icon: Loader2, spin: true },
  validating: { label: "Validating", className: "bg-warning/10 text-warning border-warning/25", icon: Loader2, spin: true },
  converting: { label: "Converting", className: "bg-primary/10 text-primary border-primary/25", icon: Loader2, spin: true },
  optimizing: { label: "Optimizing", className: "bg-primary/10 text-primary border-primary/25", icon: Loader2, spin: true },
  benchmarking: { label: "Benchmarking", className: "bg-primary/10 text-primary border-primary/25", icon: Loader2, spin: true },
  completed: { label: "Completed", className: "bg-success/10 text-success border-success/25", icon: CheckCircle2 },
  ready: { label: "Ready", className: "bg-success/10 text-success border-success/25", icon: CheckCircle2 },
  failed: { label: "Failed", className: "bg-destructive/10 text-destructive border-destructive/25", icon: XCircle },
  invalid: { label: "Invalid", className: "bg-destructive/10 text-destructive border-destructive/25", icon: OctagonX },
  cancelled: { label: "Cancelled", className: "bg-warning/10 text-warning border-warning/25", icon: AlertTriangle },
};

export function StatusBadge({ status, className }: { status: Status; className?: string }) {
  const config = CONFIG[status] ?? CONFIG.queued;
  const Icon = config.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wide",
        config.className,
        className,
      )}
    >
      <Icon className={cn("size-3", config.spin && "animate-spin")} />
      {config.label}
    </span>
  );
}
