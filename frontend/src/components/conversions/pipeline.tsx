import { Check, Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { JobStatus } from "@/types/api";

const STAGES: { key: JobStatus; label: string }[] = [
  { key: "queued", label: "Queued" },
  { key: "validating", label: "Validation" },
  { key: "converting", label: "Convert" },
  { key: "optimizing", label: "Optimize" },
  { key: "benchmarking", label: "Benchmark" },
  { key: "completed", label: "Completed" },
];

function stageIndex(status: JobStatus): number {
  if (status === "failed" || status === "cancelled") return -1;
  return STAGES.findIndex((s) => s.key === status);
}

export function ConversionPipeline({ status }: { status: JobStatus }) {
  const currentIndex = stageIndex(status);
  const terminalFailure = status === "failed" || status === "cancelled";

  return (
    <div className="flex items-center overflow-x-auto py-2">
      {STAGES.map((stage, index) => {
        const isDone = !terminalFailure && index < currentIndex;
        const isCurrent = !terminalFailure && index === currentIndex;
        const isLast = index === STAGES.length - 1;

        return (
          <div key={stage.key} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-full border text-xs font-medium",
                  isDone && "border-success/40 bg-success/10 text-success",
                  isCurrent && "border-primary bg-primary/10 text-primary",
                  !isDone && !isCurrent && "border-border bg-surface-2 text-muted-foreground",
                )}
              >
                {isDone ? (
                  <Check className="size-4" />
                ) : isCurrent ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  index + 1
                )}
              </div>
              <span
                className={cn(
                  "whitespace-nowrap text-[11px]",
                  isCurrent ? "text-foreground font-medium" : "text-muted-foreground",
                )}
              >
                {stage.label}
              </span>
            </div>
            {!isLast && (
              <div className={cn("mx-2 h-px w-10 shrink-0", isDone ? "bg-success/40" : "bg-border")} />
            )}
          </div>
        );
      })}
      {terminalFailure && (
        <div className="ml-4 flex items-center gap-1.5 text-xs font-medium text-destructive">
          <X className="size-4" />
          {status === "cancelled" ? "Cancelled" : "Failed"}
        </div>
      )}
    </div>
  );
}
