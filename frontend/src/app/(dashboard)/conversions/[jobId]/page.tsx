"use client";

import { use } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowLeft, RotateCw, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/common/error-state";
import { StatusBadge } from "@/components/common/status-badge";
import { ConversionPipeline } from "@/components/conversions/pipeline";
import { LogViewer } from "@/components/logs/log-viewer";
import {
  useCancelConversion,
  useConversion,
  useConversionLogs,
  useConversionStream,
  useRetryConversion,
} from "@/hooks/use-conversions";
import { formatDate, formatDuration } from "@/lib/format";
import { apiErrorMessage } from "@/lib/api-client";

const ACTIVE_STATUSES = ["queued", "validating", "converting", "optimizing", "benchmarking"];

export default function JobDetailPage({ params }: { params: Promise<{ jobId: string }> }) {
  const { jobId } = use(params);
  const { data: job, isLoading, isError, refetch } = useConversion(jobId);
  useConversionStream(jobId);
  const isActive = job ? ACTIVE_STATUSES.includes(job.status) : false;
  const { data: logs = [] } = useConversionLogs(jobId, isActive);
  const cancelJob = useCancelConversion();
  const retryJob = useRetryConversion();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full rounded-xl" />
      </div>
    );
  }

  if (isError || !job) {
    return <ErrorState title="Unable to load conversion job." onRetry={() => refetch()} />;
  }

  const handleCancel = async () => {
    try {
      await cancelJob.mutateAsync(job.id);
      toast.success("Job cancelled");
    } catch (error) {
      toast.error(apiErrorMessage(error, "Failed to cancel job"));
    }
  };

  const handleRetry = async () => {
    try {
      await retryJob.mutateAsync(job.id);
      toast.success("Job re-queued");
    } catch (error) {
      toast.error(apiErrorMessage(error, "Failed to retry job"));
    }
  };

  return (
    <div className="space-y-6">
      <Link href="/conversions" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" />
        Back to conversions
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-semibold tracking-tight">
            <span className="font-mono uppercase">{job.target_format}</span> Conversion
          </h1>
          <p className="font-mono text-xs text-muted-foreground">{job.id}</p>
        </div>
        <div className="flex gap-2">
          {isActive && (
            <Button variant="outline" onClick={handleCancel} disabled={cancelJob.isPending}>
              <XCircle className="size-4" />
              Cancel
            </Button>
          )}
          {(job.status === "failed" || job.status === "cancelled") && (
            <Button onClick={handleRetry} disabled={retryJob.isPending}>
              <RotateCw className="size-4" />
              Retry
            </Button>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface p-5">
        <div className="mb-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <Field label="Optimization" value={job.optimization.toUpperCase()} />
          <Field label="Status" value={<StatusBadge status={job.status} />} />
          <Field label="Progress" value={`${job.progress}%`} />
          <Field label="Duration" value={formatDuration(job.started_at, job.completed_at)} />
        </div>
        <ConversionPipeline status={job.status} />
      </div>

      {job.error_message && (
        <div
          className={`rounded-lg border p-4 text-sm ${
            job.status === "cancelled"
              ? "border-warning/25 bg-warning/5 text-warning"
              : "border-destructive/25 bg-destructive/5 text-destructive"
          }`}
        >
          <p className="font-medium">{job.status === "cancelled" ? "Job cancelled" : "Conversion error"}</p>
          <p className="mt-1 whitespace-pre-wrap opacity-90">{job.error_message}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Field label="Started" value={formatDate(job.started_at)} card />
        <Field label="Completed" value={formatDate(job.completed_at)} card />
        <Field label="Target device" value={job.target_device} card mono />
      </div>

      <LogViewer logs={logs} jobId={job.id} />
    </div>
  );
}

function Field({
  label,
  value,
  card,
  mono,
}: {
  label: string;
  value: React.ReactNode;
  card?: boolean;
  mono?: boolean;
}) {
  const content = (
    <>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={mono ? "font-mono text-sm" : "text-sm font-medium"}>{value}</p>
    </>
  );
  if (card) {
    return <div className="rounded-lg border border-border bg-surface p-4">{content}</div>;
  }
  return <div>{content}</div>;
}
