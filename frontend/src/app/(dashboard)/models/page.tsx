"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { MoreHorizontal, Plus, Search, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { StatusBadge } from "@/components/common/status-badge";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useDeleteModel, useModels } from "@/hooks/use-models";
import { formatBytes, formatDate } from "@/lib/format";
import { apiErrorMessage } from "@/lib/api-client";

export default function ModelsPage() {
  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const { data, isLoading, isError, refetch } = useModels(search);
  const deleteModel = useDeleteModel();
  const router = useRouter();

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteModel.mutateAsync(deleteTarget);
      toast.success("Model deleted");
    } catch (error) {
      toast.error(apiErrorMessage(error, "Failed to delete model"));
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Models</h1>
          <p className="text-sm text-muted-foreground">Upload and manage your PyTorch and ONNX models.</p>
        </div>
        <Button nativeButton={false} render={<Link href="/models/upload" />}>
          <Plus className="size-4" />
          Upload Model
        </Button>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search models..."
          className="pl-8"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="rounded-xl border border-border bg-surface">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : isError ? (
          <ErrorState title="Unable to load models." onRetry={() => refetch()} />
        ) : data && data.items.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model</TableHead>
                <TableHead>Framework</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((model) => (
                <TableRow key={model.id} className="cursor-pointer" onClick={() => router.push(`/models/${model.id}`)}>
                  <TableCell className="font-medium">{model.name}</TableCell>
                  <TableCell className="font-mono uppercase text-muted-foreground">{model.framework}</TableCell>
                  <TableCell className="font-mono tabular-nums">{formatBytes(model.size)}</TableCell>
                  <TableCell className="font-mono text-muted-foreground">{model.version}</TableCell>
                  <TableCell>
                    <StatusBadge status={model.status} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">{formatDate(model.created_at)}</TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <DropdownMenu>
                      <DropdownMenuTrigger render={<Button variant="ghost" size="icon" className="size-7" />}>
                        <MoreHorizontal className="size-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => router.push(`/models/${model.id}`)}>View details</DropdownMenuItem>
                        <DropdownMenuItem variant="destructive" onClick={() => setDeleteTarget(model.id)}>
                          <Trash2 className="size-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState
            title="No models yet"
            description="Upload an ONNX or TorchScript (.pt) model to start converting."
            action={
              <Button size="sm" nativeButton={false} render={<Link href="/models/upload" />}>
                Upload your first model
              </Button>
            }
          />
        )}
      </div>

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete this model?"
        description="This will permanently delete the model file and all its conversion jobs. This cannot be undone."
        confirmLabel="Delete"
        destructive
        onConfirm={handleDelete}
      />
    </div>
  );
}
