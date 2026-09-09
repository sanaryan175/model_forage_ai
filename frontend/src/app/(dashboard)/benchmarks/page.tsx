"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useBenchmarks } from "@/hooks/use-benchmarks";
import { formatBytes, formatMs, formatPct } from "@/lib/format";

const chartTooltipStyle = {
  background: "var(--color-surface-2)",
  border: "1px solid var(--color-border)",
  borderRadius: 8,
  fontSize: 12,
};

export default function BenchmarksPage() {
  const { data, isLoading, isError, refetch } = useBenchmarks();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-72 w-full rounded-xl" />
      </div>
    );
  }

  if (isError || !data) {
    return <ErrorState title="Unable to load benchmarks." onRetry={() => refetch()} />;
  }

  const chartData = data.items.map((b) => ({
    name: `${b.model_name} / ${b.target_format.toUpperCase()}`,
    latency: b.latency_mean_ms,
    size: b.model_size_bytes ? b.model_size_bytes / (1024 * 1024) : null,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Benchmarks</h1>
        <p className="text-sm text-muted-foreground">Latency, size, accuracy and memory for every conversion.</p>
      </div>

      {data.items.length === 0 ? (
        <EmptyState title="No benchmarks yet" description="Complete a conversion job to see benchmark results." />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <ChartCard title="Latency Comparison (ms)">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} hide />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar dataKey="latency" fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ChartCard>
            <ChartCard title="Model Size Comparison (MB)">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} hide />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar dataKey="size" fill="var(--color-secondary)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ChartCard>
          </div>

          <div className="rounded-xl border border-border bg-surface">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Format</TableHead>
                  <TableHead>Optimization</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Latency</TableHead>
                  <TableHead>Accuracy</TableHead>
                  <TableHead>Memory</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell className="font-medium">{b.model_name}</TableCell>
                    <TableCell className="font-mono uppercase">{b.target_format}</TableCell>
                    <TableCell className="font-mono uppercase text-muted-foreground">{b.optimization}</TableCell>
                    <TableCell className="font-mono tabular-nums">{formatBytes(b.model_size_bytes)}</TableCell>
                    <TableCell className="font-mono tabular-nums">{formatMs(b.latency_mean_ms)}</TableCell>
                    <TableCell className="font-mono tabular-nums">{formatPct(b.accuracy_pct)}</TableCell>
                    <TableCell className="font-mono tabular-nums">
                      {b.memory_usage_mb ? `${b.memory_usage_mb.toFixed(1)} MB` : "N/A"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </>
      )}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactElement }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <h2 className="mb-4 text-sm font-medium">{title}</h2>
      <ResponsiveContainer width="100%" height={220}>
        {children}
      </ResponsiveContainer>
    </div>
  );
}
