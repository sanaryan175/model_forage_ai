"use client";

import Link from "next/link";
import { Boxes, CheckCircle2, Timer, Workflow } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { MetricCard } from "@/components/common/metric-card";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/common/status-badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useDashboard } from "@/hooks/use-dashboard";
import { formatBytes, formatDate, formatMs } from "@/lib/format";
import { Progress } from "@/components/ui/progress";

const FORMAT_COLORS: Record<string, string> = {
  tflite: "var(--color-primary)",
  tensorrt: "var(--color-secondary)",
  coreml: "var(--color-success)",
  onnx: "var(--color-warning)",
};

export default function DashboardPage() {
  const { data, isLoading, isError, refetch } = useDashboard();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-80 rounded-xl" />
      </div>
    );
  }

  if (isError || !data) {
    return <ErrorState title="Unable to load dashboard." onRetry={() => refetch()} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Overview</h1>
        <p className="text-sm text-muted-foreground">Your model conversion pipeline at a glance.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Total Models" value={data.stats.total_models} icon={Boxes} />
        <MetricCard label="Active Jobs" value={data.stats.active_jobs} icon={Workflow} />
        <MetricCard label="Completed Conversions" value={data.stats.completed_conversions} icon={CheckCircle2} />
        <MetricCard label="Average Latency" value={formatMs(data.stats.average_latency_ms)} icon={Timer} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-border bg-surface p-5 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-medium">Active Conversion Jobs</h2>
            <Link href="/conversions" className="text-xs text-primary hover:underline">
              View all
            </Link>
          </div>
          {data.active_jobs.length === 0 ? (
            <EmptyState title="No active jobs" description="Start a conversion from the Models page." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Target</TableHead>
                  <TableHead>Optimization</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Started</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.active_jobs.map((job) => (
                  <TableRow key={job.id} className="cursor-pointer">
                    <TableCell>
                      <Link href={`/conversions/${job.id}`} className="block font-mono uppercase">
                        {job.target_format}
                      </Link>
                    </TableCell>
                    <TableCell className="font-mono uppercase text-muted-foreground">{job.optimization}</TableCell>
                    <TableCell className="w-32">
                      <Progress value={job.progress} className="h-1.5" />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={job.status} />
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(job.started_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        <div className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-4 font-medium">Model Format Distribution</h2>
          {data.format_distribution.length === 0 ? (
            <EmptyState title="No conversions yet" />
          ) : (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width={120} height={120}>
                <PieChart>
                  <Pie
                    data={data.format_distribution}
                    dataKey="count"
                    nameKey="format"
                    innerRadius={35}
                    outerRadius={55}
                    paddingAngle={2}
                  >
                    {data.format_distribution.map((entry) => (
                      <Cell key={entry.format} fill={FORMAT_COLORS[entry.format] ?? "var(--color-muted-foreground)"} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: "var(--color-surface-2)",
                      border: "1px solid var(--color-border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 text-sm">
                {data.format_distribution.map((entry) => (
                  <div key={entry.format} className="flex items-center gap-2">
                    <span
                      className="size-2 rounded-full"
                      style={{ background: FORMAT_COLORS[entry.format] ?? "var(--color-muted-foreground)" }}
                    />
                    <span className="font-mono uppercase text-muted-foreground">{entry.format}</span>
                    <span className="font-mono tabular-nums">{entry.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-medium">Recent Models</h2>
          <Link href="/models" className="text-xs text-primary hover:underline">
            View all
          </Link>
        </div>
        {data.recent_models.length === 0 ? (
          <EmptyState title="No models uploaded yet" description="Upload an ONNX or TorchScript model to get started." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model</TableHead>
                <TableHead>Framework</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.recent_models.map((model) => (
                <TableRow key={model.id}>
                  <TableCell>
                    <Link href={`/models/${model.id}`} className="block font-medium">
                      {model.name}
                    </Link>
                  </TableCell>
                  <TableCell className="font-mono uppercase text-muted-foreground">{model.framework}</TableCell>
                  <TableCell className="font-mono tabular-nums">{formatBytes(model.size)}</TableCell>
                  <TableCell>
                    <StatusBadge status={model.status} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">{formatDate(model.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
