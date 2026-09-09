"use client";

import { useEffect, useMemo, useState } from "react";
import { Trophy } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { EmptyState } from "@/components/common/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useConversions } from "@/hooks/use-conversions";
import { useCompareBenchmarks } from "@/hooks/use-benchmarks";
import { formatBytes, formatMs, formatPct } from "@/lib/format";

export default function ComparePage() {
  const { data: conversions, isLoading } = useConversions();
  const [selected, setSelected] = useState<string[]>([]);
  const compare = useCompareBenchmarks();

  const completedJobs = useMemo(
    () => conversions?.items.filter((j) => j.status === "completed") ?? [],
    [conversions],
  );

  useEffect(() => {
    if (selected.length > 0) {
      compare.mutate(selected);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  const toggle = (jobId: string) => {
    setSelected((prev) => (prev.includes(jobId) ? prev.filter((id) => id !== jobId) : [...prev, jobId]));
  };

  const result = compare.data;

  type MetricKey = "model_size_bytes" | "latency_mean_ms" | "accuracy_pct" | "memory_usage_mb";
  const metricRows: { key: MetricKey; label: string; format: (v: number | null | undefined) => string; bestId: string | null | undefined }[] =
    result
      ? [
          { key: "model_size_bytes", label: "Size", format: formatBytes, bestId: result.smallest_size_job_id },
          { key: "latency_mean_ms", label: "Latency", format: formatMs, bestId: result.best_latency_job_id },
          { key: "accuracy_pct", label: "Accuracy", format: formatPct, bestId: result.highest_accuracy_job_id },
          {
            key: "memory_usage_mb",
            label: "Memory",
            format: (v) => (v ? `${v.toFixed(1)} MB` : "N/A"),
            bestId: null,
          },
        ]
      : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Compare</h1>
        <p className="text-sm text-muted-foreground">Select completed conversions to compare side by side.</p>
      </div>

      <div className="rounded-xl border border-border bg-surface p-5">
        <h2 className="mb-3 text-sm font-medium">Select models to compare</h2>
        {isLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : completedJobs.length === 0 ? (
          <EmptyState title="No completed conversions yet" description="Complete a conversion job before comparing." />
        ) : (
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {completedJobs.map((job) => (
              <label
                key={job.id}
                className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm hover:bg-surface-2"
              >
                <Checkbox checked={selected.includes(job.id)} onCheckedChange={() => toggle(job.id)} />
                <span className="font-mono uppercase">{job.target_format}</span>
                <span className="text-muted-foreground">· {job.optimization.toUpperCase()}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {result && result.rows.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-4 text-sm font-medium">Model Performance</h2>
          <table className="w-full min-w-[500px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="py-2 pr-4 font-normal">Metric</th>
                {result.rows.map((row) => (
                  <th key={row.job_id} className="py-2 pr-4 font-mono font-medium uppercase text-foreground">
                    {row.model_name} <span className="text-muted-foreground">/ {row.target_format}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {metricRows.map((metric) => (
                <tr key={metric.label} className="border-b border-border last:border-0">
                  <td className="py-2 pr-4 text-muted-foreground">{metric.label}</td>
                  {result.rows.map((row) => {
                    const value = row.benchmark?.[metric.key] as number | null | undefined;
                    const isBest = metric.bestId === row.job_id;
                    return (
                      <td
                        key={row.job_id}
                        className={cn("py-2 pr-4 font-mono tabular-nums", isBest && "font-semibold text-success")}
                      >
                        {metric.format(value)}
                        {isBest && <Trophy className="ml-1.5 inline size-3.5" />}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>

          <div className="mt-6 space-y-1 rounded-lg border border-border bg-surface-2 p-4 text-sm">
            <p className="font-medium">Recommendation</p>
            <RecommendationLine label="Best latency" jobId={result.best_latency_job_id} rows={result.rows} />
            <RecommendationLine label="Smallest model" jobId={result.smallest_size_job_id} rows={result.rows} />
            <RecommendationLine label="Highest accuracy" jobId={result.highest_accuracy_job_id} rows={result.rows} />
            <RecommendationLine label="Best overall" jobId={result.best_overall_job_id} rows={result.rows} />
          </div>
        </div>
      )}
    </div>
  );
}

function RecommendationLine({
  label,
  jobId,
  rows,
}: {
  label: string;
  jobId: string | null | undefined;
  rows: { job_id: string; model_name: string; target_format: string }[];
}) {
  const row = rows.find((r) => r.job_id === jobId);
  return (
    <p className="text-muted-foreground">
      <span className="text-foreground">{label}:</span>{" "}
      {row ? `${row.model_name} (${row.target_format.toUpperCase()})` : "N/A"}
    </p>
  );
}
