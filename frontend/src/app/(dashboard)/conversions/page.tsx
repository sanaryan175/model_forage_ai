"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusBadge } from "@/components/common/status-badge";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useConversions } from "@/hooks/use-conversions";
import { formatDate, formatDuration } from "@/lib/format";

export default function ConversionsPage() {
  const { data, isLoading, isError, refetch } = useConversions();
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Conversion Jobs</h1>
        <p className="text-sm text-muted-foreground">Track every conversion from queue to completion.</p>
      </div>

      <div className="rounded-xl border border-border bg-surface">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : isError ? (
          <ErrorState title="Unable to load conversion jobs." onRetry={() => refetch()} />
        ) : data && data.items.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Target</TableHead>
                <TableHead>Optimization</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((job) => (
                <TableRow key={job.id} className="cursor-pointer" onClick={() => router.push(`/conversions/${job.id}`)}>
                  <TableCell className="font-mono uppercase">{job.target_format}</TableCell>
                  <TableCell className="font-mono uppercase text-muted-foreground">{job.optimization}</TableCell>
                  <TableCell className="w-32">
                    <Progress value={job.progress} className="h-1.5" />
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={job.status} />
                  </TableCell>
                  <TableCell className="font-mono text-muted-foreground">
                    {formatDuration(job.started_at, job.completed_at)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{formatDate(job.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState
            title="No conversion jobs yet"
            description="Upload a model and start a conversion to see jobs here."
            action={
              <Button size="sm" nativeButton={false} render={<Link href="/models" />}>
                Go to models
              </Button>
            }
          />
        )}
      </div>
    </div>
  );
}
