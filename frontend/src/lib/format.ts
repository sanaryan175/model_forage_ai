export function formatBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return "N/A";
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** exponent;
  return `${value.toFixed(exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}

export function formatMs(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "N/A";
  return `${ms.toFixed(2)} ms`;
}

export function formatPct(pct: number | null | undefined): string {
  if (pct === null || pct === undefined) return "N/A";
  return `${pct.toFixed(1)}%`;
}

export function formatThroughput(ips: number | null | undefined): string {
  if (ips === null || ips === undefined) return "N/A";
  return `${ips.toFixed(1)} inf/s`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDuration(start: string | null, end: string | null): string {
  if (!start) return "N/A";
  const startMs = new Date(start).getTime();
  const endMs = end ? new Date(end).getTime() : Date.now();
  const seconds = Math.max(0, (endMs - startMs) / 1000);
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}
