"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, UploadCloud, Workflow, XCircle } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EmptyState } from "@/components/common/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useModels } from "@/hooks/use-models";
import { useConversions } from "@/hooks/use-conversions";
import { formatDate } from "@/lib/format";

type ActivityEvent = {
  id: string;
  type: "upload" | "started" | "completed" | "failed" | "cancelled";
  message: string;
  timestamp: string;
  modelName?: string;
};

const ICONS: Record<ActivityEvent["type"], React.ElementType> = {
  upload: UploadCloud,
  started: Workflow,
  completed: CheckCircle2,
  failed: XCircle,
  cancelled: AlertTriangle,
};

const COLORS: Record<ActivityEvent["type"], string> = {
  upload: "text-primary",
  started: "text-muted-foreground",
  completed: "text-success",
  failed: "text-destructive",
  cancelled: "text-warning",
};

export default function ActivityPage() {
  const { data: models, isLoading: modelsLoading } = useModels();
  const { data: conversions, isLoading: jobsLoading } = useConversions();
  const [filter, setFilter] = useState<string>("all");

  const events = useMemo<ActivityEvent[]>(() => {
    const items: ActivityEvent[] = [];
    for (const model of models?.items ?? []) {
      items.push({
        id: `upload-${model.id}`,
        type: "upload",
        message: `${model.name} uploaded`,
        timestamp: model.created_at,
        modelName: model.name,
      });
    }
    for (const job of conversions?.items ?? []) {
      items.push({
        id: `start-${job.id}`,
        type: "started",
        message: `${job.target_format.toUpperCase()} conversion started`,
        timestamp: job.created_at,
      });
      if (job.completed_at) {
        items.push({
          id: `end-${job.id}`,
          type: job.status === "completed" ? "completed" : job.status === "cancelled" ? "cancelled" : "failed",
          message: `${job.target_format.toUpperCase()} conversion ${job.status}`,
          timestamp: job.completed_at,
        });
      }
    }
    return items.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [models, conversions]);

  const filtered = filter === "all" ? events : events.filter((e) => e.type === filter);
  const isLoading = modelsLoading || jobsLoading;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Activity</h1>
          <p className="text-sm text-muted-foreground">A timeline of uploads, conversions and results.</p>
        </div>
        <Select value={filter} onValueChange={(value) => setFilter(value ?? "all")}>
          <SelectTrigger className="w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All activity</SelectItem>
            <SelectItem value="upload">Uploads</SelectItem>
            <SelectItem value="started">Started</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-xl border border-border bg-surface p-5">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState title="No activity yet" />
        ) : (
          <ol className="space-y-4">
            {filtered.map((event) => {
              const Icon = ICONS[event.type];
              return (
                <li key={event.id} className="flex items-start gap-3">
                  <Icon className={`mt-0.5 size-4 shrink-0 ${COLORS[event.type]}`} />
                  <div className="flex-1">
                    <p className="text-sm">{event.message}</p>
                    <p className="text-xs text-muted-foreground">{formatDate(event.timestamp)}</p>
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </div>
    </div>
  );
}
