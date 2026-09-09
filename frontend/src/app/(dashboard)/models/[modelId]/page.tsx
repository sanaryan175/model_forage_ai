"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft, Download, Trash2, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/common/status-badge";
import { ErrorState } from "@/components/common/error-state";
import { EmptyState } from "@/components/common/empty-state";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ConversionConfigDialog } from "@/components/conversions/conversion-config-dialog";
import { useDeleteModel, useModel, useModelArtifacts } from "@/hooks/use-models";
import { useConversions } from "@/hooks/use-conversions";
import { formatBytes, formatDate } from "@/lib/format";
import { apiErrorMessage, API_URL } from "@/lib/api-client";

export default function ModelDetailPage({ params }: { params: Promise<{ modelId: string }> }) {
  const { modelId } = use(params);
  const router = useRouter();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const { data: model, isLoading, isError, refetch } = useModel(modelId);
  const { data: artifacts } = useModelArtifacts(modelId);
  const { data: conversions } = useConversions();
  const deleteModel = useDeleteModel();

  const modelJobs = conversions?.items.filter((job) => job.model_id === modelId) ?? [];

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full rounded-xl" />
      </div>
    );
  }

  if (isError || !model) {
    return <ErrorState title="Unable to load model." onRetry={() => refetch()} />;
  }

  const handleDelete = async () => {
    try {
      await deleteModel.mutateAsync(model.id);
      toast.success("Model deleted");
      router.push("/models");
    } catch (error) {
      toast.error(apiErrorMessage(error, "Failed to delete model"));
    }
  };

  return (
    <div className="space-y-6">
      <Link href="/models" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" />
        Back to models
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{model.name}</h1>
          <p className="text-sm text-muted-foreground">{model.original_filename}</p>
        </div>
        <div className="flex gap-2">
          {model.status === "ready" && (
            <ConversionConfigDialog
              modelId={model.id}
              modelFramework={model.framework}
              trigger={
                <Button>
                  <Zap className="size-4" />
                  Convert
                </Button>
              }
            />
          )}
          <Button variant="outline" onClick={() => router.push(`/compare?model=${model.id}`)}>
            Compare
          </Button>
          <Button variant="outline" className="text-destructive hover:text-destructive" onClick={() => setDeleteOpen(true)}>
            <Trash2 className="size-4" />
          </Button>
        </div>
      </div>

      {model.status === "invalid" && model.validation_error && (
        <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">
          <p className="font-medium">Validation failed</p>
          <p className="mt-1 text-destructive/90">{model.validation_error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-border bg-surface p-5 lg:col-span-2">
          <h2 className="mb-4 font-medium">Overview</h2>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <Field label="Framework" value={model.framework.toUpperCase()} mono />
            <Field label="Status" value={<StatusBadge status={model.status} />} />
            <Field label="File size" value={formatBytes(model.size)} mono />
            <Field label="Version" value={model.version} mono />
            <Field label="Input shape" value={model.input_shape ?? "N/A"} mono />
            <Field label="Output shape" value={model.output_shape ?? "N/A"} mono />
            <Field label="Input names" value={model.input_names ?? "N/A"} mono />
            <Field label="Output names" value={model.output_names ?? "N/A"} mono />
            <Field label="Created" value={formatDate(model.created_at)} />
          </dl>
        </div>

        <div className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-4 font-medium">Artifacts</h2>
          {!artifacts || artifacts.length === 0 ? (
            <EmptyState title="No artifacts yet" description="Run a conversion to generate deployable artifacts." />
          ) : (
            <ul className="space-y-2">
              {artifacts.map((artifact) => (
                <li key={artifact.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm">
                  <div>
                    <p className="font-mono uppercase">{artifact.format}</p>
                    <p className="text-xs text-muted-foreground">{formatBytes(artifact.file_size)}</p>
                  </div>
                  <a
                    href={`${API_URL}/api/models/artifacts/download-local?key=${encodeURIComponent(artifact.file_path)}`}
                    className="text-muted-foreground hover:text-primary"
                  >
                    <Download className="size-4" />
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface p-5">
        <h2 className="mb-4 font-medium">Conversion History</h2>
        {modelJobs.length === 0 ? (
          <EmptyState title="No conversions yet" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Target</TableHead>
                <TableHead>Optimization</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {modelJobs.map((job) => (
                <TableRow key={job.id} className="cursor-pointer" onClick={() => router.push(`/conversions/${job.id}`)}>
                  <TableCell className="font-mono uppercase">{job.target_format}</TableCell>
                  <TableCell className="font-mono uppercase text-muted-foreground">{job.optimization}</TableCell>
                  <TableCell>
                    <StatusBadge status={job.status} />
                  </TableCell>
                  <TableCell className="font-mono tabular-nums">{job.progress}%</TableCell>
                  <TableCell className="text-muted-foreground">{formatDate(job.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete this model?"
        description="This will permanently delete the model file and all its conversion jobs."
        confirmLabel="Delete"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  );
}

function Field({ label, value, mono }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={mono ? "font-mono text-sm" : "text-sm"}>{value}</dd>
    </div>
  );
}
