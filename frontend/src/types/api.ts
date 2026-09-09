export type ModelFramework = "pytorch" | "onnx";
export type ModelStatus = "uploading" | "validating" | "ready" | "invalid";

export interface ModelRecord {
  id: string;
  user_id: string;
  name: string;
  original_filename: string;
  framework: ModelFramework;
  version: string;
  size: number;
  status: ModelStatus;
  input_shape: string | null;
  output_shape: string | null;
  input_names: string | null;
  output_names: string | null;
  validation_error: string | null;
  created_at: string;
  updated_at: string;
}

export type TargetFormat = "tflite" | "tensorrt" | "coreml";
export type OptimizationType = "fp32" | "fp16" | "int8";
export type JobStatus =
  | "queued"
  | "validating"
  | "converting"
  | "optimizing"
  | "benchmarking"
  | "completed"
  | "failed"
  | "cancelled";

export interface ConversionJob {
  id: string;
  model_id: string;
  target_format: TargetFormat;
  optimization: OptimizationType;
  status: JobStatus;
  progress: number;
  batch_size: number;
  target_device: string;
  input_shape: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface JobLogEntry {
  id: string;
  level: "debug" | "info" | "warning" | "error";
  message: string;
  timestamp: string;
}

export interface Benchmark {
  id: string;
  job_id: string;
  model_name: string;
  target_format: string;
  optimization: string;
  model_size_bytes: number | null;
  latency_mean_ms: number | null;
  latency_median_ms: number | null;
  latency_p95_ms: number | null;
  throughput_ips: number | null;
  accuracy_pct: number | null;
  memory_usage_mb: number | null;
  benchmark_device: string;
  unsupported_metrics: string | null;
  created_at: string;
}

export interface ComparisonRow {
  job_id: string;
  model_name: string;
  target_format: string;
  optimization: string;
  benchmark: Benchmark | null;
}

export interface ComparisonResult {
  rows: ComparisonRow[];
  best_latency_job_id: string | null;
  smallest_size_job_id: string | null;
  highest_accuracy_job_id: string | null;
  best_overall_job_id: string | null;
}

export interface DashboardStats {
  total_models: number;
  active_jobs: number;
  completed_conversions: number;
  average_latency_ms: number | null;
}

export interface DashboardResponse {
  stats: DashboardStats;
  active_jobs: ConversionJob[];
  recent_models: ModelRecord[];
  format_distribution: { format: string; count: number }[];
}

export interface ArtifactRecord {
  id: string;
  job_id: string;
  format: string;
  file_path: string;
  file_size: number;
  checksum: string;
  created_at: string;
  model_name?: string | null;
  optimization?: string | null;
}

export interface User {
  id: string;
  name: string;
  email: string;
}
