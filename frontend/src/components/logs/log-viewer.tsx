"use client";

import { Copy, Download } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { JobLogEntry } from "@/types/api";

const LEVEL_COLOR: Record<string, string> = {
  debug: "text-muted-foreground",
  info: "text-foreground",
  warning: "text-warning",
  error: "text-destructive",
};

export function LogViewer({ logs, jobId }: { logs: JobLogEntry[]; jobId: string }) {
  const asText = logs
    .map((l) => `[${new Date(l.timestamp).toLocaleTimeString()}] ${l.level.toUpperCase()} ${l.message}`)
    .join("\n");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(asText);
    toast.success("Logs copied to clipboard");
  };

  const handleDownload = () => {
    const blob = new Blob([asText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `job-${jobId}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-[#0b0e15]">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <span className="text-xs font-medium text-muted-foreground">Logs</span>
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs" onClick={handleCopy}>
            <Copy className="size-3.5" />
            Copy
          </Button>
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs" onClick={handleDownload}>
            <Download className="size-3.5" />
            Download
          </Button>
        </div>
      </div>
      <div className="max-h-96 overflow-y-auto p-3 font-mono text-xs leading-relaxed">
        {logs.length === 0 ? (
          <p className="text-muted-foreground">No logs yet.</p>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="flex gap-2">
              <span className="shrink-0 text-muted-foreground">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
              <span className={cn("whitespace-pre-wrap", LEVEL_COLOR[log.level])}>{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
