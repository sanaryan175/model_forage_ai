"use client";

import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useArtifacts } from "@/hooks/use-artifacts";
import { formatBytes, formatDate } from "@/lib/format";
import { API_URL } from "@/lib/api-client";

const EXTENSION_BY_FORMAT: Record<string, string> = {
  tflite: ".tflite",
  tensorrt: ".engine",
  coreml: ".mlmodel",
};

export default function GeneratedModelsPage() {
  const { data, isLoading, isError, refetch } = useArtifacts();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Generated Models</h1>
        <p className="text-sm text-muted-foreground">Every artifact produced by a completed conversion job.</p>
      </div>

      <div className="rounded-xl border border-border bg-surface">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : isError ? (
          <ErrorState title="Unable to load generated models." onRetry={() => refetch()} />
        ) : data && data.items.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model</TableHead>
                <TableHead>Format</TableHead>
                <TableHead>Optimization</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="w-10">Download</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((artifact) => (
                <TableRow key={artifact.id}>
                  <TableCell className="font-medium">{artifact.model_name ?? "—"}</TableCell>
                  <TableCell className="font-mono uppercase">
                    {artifact.format}
                    <span className="ml-1 text-muted-foreground">{EXTENSION_BY_FORMAT[artifact.format]}</span>
                  </TableCell>
                  <TableCell className="font-mono uppercase text-muted-foreground">{artifact.optimization}</TableCell>
                  <TableCell className="font-mono tabular-nums">{formatBytes(artifact.file_size)}</TableCell>
                  <TableCell className="text-muted-foreground">{formatDate(artifact.created_at)}</TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="size-7"
                      nativeButton={false}
                      render={<a href={`${API_URL}/api/artifacts/${artifact.id}/download`} />}
                    >
                      <Download className="size-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState title="No generated models yet" description="Completed conversions will appear here as downloadable artifacts." />
        )}
      </div>
    </div>
  );
}
