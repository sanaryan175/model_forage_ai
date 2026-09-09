"use client";

import { useCallback, useRef, useState } from "react";
import { File as FileIcon, UploadCloud, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatBytes } from "@/lib/format";

const ACCEPTED_EXTENSIONS = [".pt", ".onnx"];

export function FileDropzone({
  file,
  onFileSelected,
  disabled,
}: {
  file: File | null;
  onFileSelected: (file: File | null) => void;
  disabled?: boolean;
}) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSet = useCallback(
    (candidate: File) => {
      const ext = candidate.name.slice(candidate.name.lastIndexOf(".")).toLowerCase();
      if (!ACCEPTED_EXTENSIONS.includes(ext)) {
        setError(`Unsupported file type '${ext}'. Only .pt and .onnx are accepted.`);
        return;
      }
      setError(null);
      onFileSelected(candidate);
    },
    [onFileSelected],
  );

  if (file) {
    return (
      <div className="flex items-center justify-between rounded-lg border border-border bg-surface-2 px-4 py-3">
        <div className="flex items-center gap-3">
          <FileIcon className="size-5 text-primary" />
          <div>
            <p className="text-sm font-medium">{file.name}</p>
            <p className="font-mono text-xs text-muted-foreground">{formatBytes(file.size)}</p>
          </div>
        </div>
        {!disabled && (
          <button
            type="button"
            onClick={() => onFileSelected(null)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-surface-3 hover:text-foreground"
          >
            <X className="size-4" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const dropped = e.dataTransfer.files?.[0];
          if (dropped) validateAndSet(dropped);
        }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-12 text-center transition-colors",
          dragging ? "border-primary bg-primary/5" : "border-border hover:border-border-strong",
        )}
      >
        <UploadCloud className="size-8 text-muted-foreground" />
        <p className="text-sm font-medium">Drag and drop your model file here</p>
        <p className="text-xs text-muted-foreground">or click to browse — .pt or .onnx, up to 512 MB</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pt,.onnx"
          className="hidden"
          onChange={(e) => {
            const selected = e.target.files?.[0];
            if (selected) validateAndSet(selected);
          }}
        />
      </div>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
