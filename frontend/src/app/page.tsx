import Link from "next/link";
import {
  ArrowDown,
  ArrowRight,
  BarChart3,
  Cloud,
  Cpu,
  Layers,
  Lock,
  Shield,
  Sparkles,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const STEPS = [
  {
    title: "Upload",
    description:
      "Upload an ONNX model or a TorchScript (.pt). It is stored in S3 and validated with a real ONNX Runtime inference.",
    icon: Layers,
  },
  {
    title: "Configure",
    description:
      "Pick target formats (TFLite, TensorRT) and precision: FP32 or FP16. An ONNX baseline run is added automatically.",
    icon: Sparkles,
  },
  {
    title: "Convert",
    description:
      "Jobs go through SQS to independent workers: a CPU worker on ECS Fargate and a GPU worker for TensorRT.",
    icon: Cpu,
  },
  {
    title: "Compare",
    description:
      "Every result is benchmarked for size, latency and fidelity against the original ONNX model, then downloadable.",
    icon: BarChart3,
  },
];

// Measured with the project's ResNet-18 (CIFAR-10, 224x224 input). Fidelity was 100% for every format.
const BENCHMARKS = [
  { label: "ONNX baseline", device: "CPU", latency: "7.9 ms", size: "44.7 MB" },
  { label: "TFLite FP32", device: "CPU", latency: "33.6 ms", size: "44.7 MB" },
  { label: "TFLite FP16", device: "CPU", latency: "35.6 ms", size: "22.4 MB" },
  {
    label: "TensorRT FP32",
    device: "RTX 2050",
    latency: "2.7 ms",
    size: "59.6 MB",
  },
  {
    label: "TensorRT FP16",
    device: "RTX 2050",
    latency: "1.2 ms",
    size: "23.2 MB",
    highlight: true,
  },
];

// From ml/Comparison.ipynb: both models scored on the 10,000 labelled CIFAR-10 test images.
const ACCURACY = [
  { metric: "Accuracy", original: "60.86%", tflite: "60.91%" },
  { metric: "Precision", original: "78.63%", tflite: "78.64%" },
  { metric: "Recall", original: "60.86%", tflite: "60.91%" },
  { metric: "F1 score", original: "64.38%", tflite: "64.43%" },
];

const TECHNOLOGIES = [
  {
    tech: "PyTorch",
    where: "Model training (Colab), .pt upload",
    role: "Trains the ResNet-18 and exports TorchScript models to ONNX",
  },
  {
    tech: "ONNX + ONNX Runtime",
    where: "API + every worker",
    role: "Common model format; validates uploads and runs the baseline benchmark",
  },
  {
    tech: "onnx2tf + TensorFlow Lite",
    where: "CPU worker (ECS)",
    role: "Converts ONNX to .tflite (FP32 / FP16) for mobile and edge devices",
  },
  {
    tech: "TensorRT + CUDA",
    where: "GPU worker (laptop RTX 2050)",
    role: "Builds GPU-optimized .engine files (FP32 / FP16)",
  },
  {
    tech: "Next.js + React + TypeScript",
    where: "Frontend",
    role: "Dashboard: upload, configure, live job progress, compare, download",
  },
  {
    tech: "FastAPI",
    where: "Backend API",
    role: "REST API, JWT auth, publishes jobs to SQS, streams downloads",
  },
  {
    tech: "SQLAlchemy + Alembic",
    where: "API + workers",
    role: "Database models and schema migrations",
  },
  {
    tech: "Amazon S3",
    where: "AWS",
    role: "Stores uploaded models and converted artifacts",
  },
  {
    tech: "Amazon SQS (+ DLQ)",
    where: "AWS",
    role: "Job queues per worker type; failed jobs move to a dead-letter queue",
  },
  {
    tech: "Amazon ECS Fargate",
    where: "AWS",
    role: "Runs the CPU conversion worker container without managing servers",
  },
  {
    tech: "Amazon RDS PostgreSQL",
    where: "AWS",
    role: "Shared database: users, models, jobs, logs, benchmarks",
  },
  {
    tech: "Amazon ECR",
    where: "AWS",
    role: "Stores the worker's Docker image that ECS runs",
  },
  {
    tech: "AWS IAM",
    where: "AWS",
    role: "Least-privilege roles: the worker can only use its bucket and queue",
  },
  {
    tech: "Amazon CloudWatch Logs",
    where: "AWS",
    role: "Collects the cloud worker's logs",
  },
  {
    tech: "Docker",
    where: "Build",
    role: "Packages the CPU worker with TensorFlow, onnx2tf and PyTorch",
  },
  {
    tech: "Terraform",
    where: "Infrastructure",
    role: "Creates all AWS resources as code; one command to tear down",
  },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-border bg-background/80 px-4 backdrop-blur sm:px-6">
        <div className="flex items-center gap-2">
          <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Zap className="size-3.5" fill="currentColor" />
          </div>
          <span className="font-semibold tracking-tight">ModelForge</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            nativeButton={false}
            render={<Link href="/login" />}
          >
            Sign in
          </Button>
          <Button nativeButton={false} render={<Link href="/register" />}>
            Get started
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="border-b border-border px-4 py-20 text-center sm:px-6 sm:py-24">
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="mx-auto inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-xs text-muted-foreground">
            <span className="size-1.5 rounded-full bg-success" />
            Runs on AWS (S3 · SQS · ECS · RDS) or fully local
          </div>
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
            One trained model.
            <br />
            Every deployment target.
          </h1>
          <p className="mx-auto max-w-xl text-lg text-muted-foreground">
            Convert a PyTorch / ONNX model to TensorFlow Lite and TensorRT, then
            benchmark size, speed and fidelity of each version against the
            original, all from one dashboard.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Button
              size="lg"
              nativeButton={false}
              render={<Link href="/register" />}
            >
              Start Converting
              <ArrowRight className="size-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              nativeButton={false}
              render={<Link href="/login" />}
            >
              Explore Dashboard
            </Button>
          </div>
        </div>
      </section>

      {/* Conversion path */}
      <section className="border-b border-border px-4 py-10 sm:px-6">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-center gap-3 font-mono text-sm">
          <Chip>PyTorch</Chip>
          <ArrowRight className="size-3.5 text-muted-foreground" />
          <Chip>ONNX</Chip>
          <ArrowRight className="size-3.5 text-muted-foreground" />
          <div className="flex flex-wrap items-center gap-2">
            <Chip highlight>TFLite</Chip>
            <Chip highlight>TensorRT</Chip>
            <Chip muted>Core ML (macOS only)</Chip>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-b border-border px-4 py-20 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-10 text-center text-2xl font-semibold tracking-tight">
            How it works
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((step, i) => (
              <div
                key={step.title}
                className="rounded-xl border border-border bg-surface p-5"
              >
                <div className="mb-3 flex size-9 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <step.icon className="size-4.5" />
                </div>
                <p className="mb-1 font-mono text-xs text-muted-foreground">
                  Step {i + 1}
                </p>
                <h3 className="mb-1 font-medium">{step.title}</h3>
                <p className="text-sm text-muted-foreground">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow diagram */}
      <section className="border-b border-border bg-surface/40 px-4 py-20 sm:px-6">
        <div className="mx-auto max-w-4xl">
          <div className="mb-10 text-center">
            <h2 className="text-2xl font-semibold tracking-tight">
              Cloud workflow
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              What happens between clicking Convert and downloading the result.
            </p>
          </div>

          <div className="flex flex-col items-center gap-2">
            <Node
              title="Frontend (Next.js)"
              detail="Upload model · choose formats & precision"
            />
            <ArrowDown className="size-4 text-muted-foreground" />
            <Node
              title="FastAPI backend"
              detail="Validates the model, creates one job per format"
            />
            <ArrowDown className="size-4 text-muted-foreground" />
            <div className="grid w-full grid-cols-1 gap-3 sm:grid-cols-3">
              <Node title="Amazon S3" detail="Original model" cloud />
              <Node title="Amazon SQS" detail="job_id per format" cloud />
              <Node title="Amazon RDS" detail="Job status: queued" cloud />
            </div>
            <ArrowDown className="size-4 text-muted-foreground" />
            <div className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
              <Node
                title="CPU worker · ECS Fargate"
                detail="Queue modelforge-cpu → TFLite + ONNX baseline"
                cloud
              />
              <Node
                title="GPU worker · RTX laptop"
                detail="Queue modelforge-tensorrt → TensorRT engine"
              />
            </div>
            <p className="font-mono text-xs text-muted-foreground">
              validate → convert → optimize → benchmark (size · latency ·
              fidelity)
            </p>
            <ArrowDown className="size-4 text-muted-foreground" />
            <div className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
              <Node
                title="Amazon S3"
                detail="Converted .tflite / .engine files"
                cloud
              />
              <Node
                title="Amazon RDS"
                detail="Benchmarks, logs, status: completed"
                cloud
              />
            </div>
            <ArrowDown className="size-4 text-muted-foreground" />
            <Node
              title="Compare & Download"
              detail="Every format vs the ONNX baseline, in the dashboard"
              highlight
            />
          </div>
        </div>
      </section>

      {/* Benchmarks */}
      <section className="border-b border-border px-4 py-20 sm:px-6">
        <div className="mx-auto grid max-w-6xl grid-cols-1 items-start gap-6 md:grid-cols-2 lg:grid-cols-[1fr_1.25fr_1.25fr]">
          <div className="md:col-span-2 lg:col-span-1">
            <BarChart3 className="mb-3 size-6 text-primary" />
            <h2 className="mb-2 text-xl font-semibold tracking-tight">
              Real benchmarks, not guesses
            </h2>
            <p className="text-sm text-muted-foreground">
              Measured with our ResNet-18 trained on CIFAR-10. Every converted
              model gave the same prediction as the original on all test inputs
              (100% fidelity), and on the full labelled test set the TFLite
              model scores the same accuracy as the original PyTorch model: the
              conversion loses nothing. Metrics that can&apos;t be measured on a
              machine are shown as N/A, never invented.
            </p>
          </div>
          <>
            <div className="overflow-x-auto rounded-xl border border-border bg-surface p-3">
              <p className="px-2 pb-2 text-xs text-muted-foreground">
                Speed and size per format
              </p>
              <table className="w-full font-mono text-xs">
                <thead>
                  <tr className="text-left text-muted-foreground">
                    <th className="px-2 py-1.5 font-normal">Format</th>
                    <th className="px-2 py-1.5 font-normal">Device</th>
                    <th className="px-2 py-1.5 text-right font-normal">
                      Latency
                    </th>
                    <th className="px-2 py-1.5 text-right font-normal">Size</th>
                  </tr>
                </thead>
                <tbody>
                  {BENCHMARKS.map((b) => (
                    <tr
                      key={b.label}
                      className={
                        b.highlight ? "bg-success/10 text-success" : ""
                      }
                    >
                      <td className="px-2 py-1.5">{b.label}</td>
                      <td className="px-2 py-1.5">{b.device}</td>
                      <td className="px-2 py-1.5 text-right tabular-nums">
                        {b.latency}
                      </td>
                      <td className="px-2 py-1.5 text-right tabular-nums">
                        {b.size}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="overflow-x-auto rounded-xl border border-border bg-surface p-3">
              <p className="px-2 pb-2 text-xs text-muted-foreground">
                Accuracy on 10,000 CIFAR-10 test images: no drop after
                conversion
              </p>
              <table className="w-full font-mono text-xs">
                <thead>
                  <tr className="text-left text-muted-foreground">
                    <th className="px-2 py-1.5 font-normal">Metric</th>
                    <th className="px-2 py-1.5 text-right font-normal">
                      Original (PyTorch)
                    </th>
                    <th className="px-2 py-1.5 text-right font-normal">
                      TFLite FP32
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {ACCURACY.map((a) => (
                    <tr key={a.metric}>
                      <td className="px-2 py-1.5">{a.metric}</td>
                      <td className="px-2 py-1.5 text-right tabular-nums">
                        {a.original}
                      </td>
                      <td className="px-2 py-1.5 text-right tabular-nums text-success">
                        {a.tflite}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        </div>
      </section>

      {/* Technologies */}
      <section className="border-b border-border px-4 py-20 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-2 text-center text-2xl font-semibold tracking-tight">
            Technologies used
          </h2>
          <p className="mb-8 text-center text-sm text-muted-foreground">
            Where each one runs and what it does.
          </p>
          <div className="overflow-x-auto rounded-xl border border-border bg-surface">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="px-4 py-3 font-medium">Technology</th>
                  <th className="px-4 py-3 font-medium">Used in</th>
                  <th className="px-4 py-3 font-medium">What it does</th>
                </tr>
              </thead>
              <tbody>
                {TECHNOLOGIES.map((t) => (
                  <tr
                    key={t.tech}
                    className="border-b border-border last:border-0 align-top"
                  >
                    <td className="whitespace-nowrap px-4 py-2.5 font-mono text-primary">
                      {t.tech}
                    </td>
                    <td className="px-4 py-2.5 text-muted-foreground">
                      {t.where}
                    </td>
                    <td className="px-4 py-2.5">{t.role}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Security */}
      <section className="border-b border-border px-4 py-20 sm:px-6">
        <div className="mx-auto grid max-w-4xl grid-cols-1 gap-6 sm:grid-cols-3">
          <SecurityCard
            icon={Lock}
            title="JWT authentication"
            description="Passwords hashed with bcrypt, signed tokens, every route protected."
          />
          <SecurityCard
            icon={Shield}
            title="Validated uploads"
            description="Extension, size and ONNX graph checks plus a test inference before any job runs."
          />
          <SecurityCard
            icon={Cloud}
            title="Least-privilege AWS"
            description="Private S3 bucket, scoped IAM roles, database reachable only from the workers and the API."
          />
        </div>
      </section>

      {/* CTA */}
      <section className="px-4 py-24 text-center sm:px-6">
        <h2 className="text-2xl font-semibold tracking-tight">
          Ready to convert your first model?
        </h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
          Upload an ONNX model and get TFLite and TensorRT versions with
          benchmarks in a few minutes.
        </p>
        <Button
          size="lg"
          className="mt-6"
          nativeButton={false}
          render={<Link href="/register" />}
        >
          Start Converting
          <ArrowRight className="size-4" />
        </Button>
      </section>

      <footer className="border-t border-border px-4 py-6 text-center text-xs text-muted-foreground sm:px-6">
        ModelForge AI: cloud-based deep learning model conversion & benchmarking
        platform.
      </footer>
    </div>
  );
}

function Chip({
  children,
  highlight,
  muted,
}: {
  children: React.ReactNode;
  highlight?: boolean;
  muted?: boolean;
}) {
  return (
    <span
      className={`rounded-md border px-3 py-1.5 ${
        highlight
          ? "border-primary/40 bg-primary/10 text-primary"
          : muted
            ? "border-border bg-surface text-muted-foreground"
            : "border-border bg-surface"
      }`}
    >
      {children}
    </span>
  );
}

function Node({
  title,
  detail,
  cloud,
  highlight,
}: {
  title: string;
  detail: string;
  cloud?: boolean;
  highlight?: boolean;
}) {
  return (
    <div
      className={`w-full max-w-md justify-self-center rounded-lg border px-4 py-3 text-center ${
        highlight
          ? "border-success/40 bg-success/10"
          : cloud
            ? "border-primary/30 bg-primary/5"
            : "border-border bg-surface"
      }`}
    >
      <p
        className={`text-sm font-medium ${highlight ? "text-success" : cloud ? "text-primary" : ""}`}
      >
        {cloud && <Cloud className="mr-1.5 inline size-3.5" />}
        {title}
      </p>
      <p className="mt-0.5 text-xs text-muted-foreground">{detail}</p>
    </div>
  );
}

function SecurityCard({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5 text-center">
      <Icon className="mx-auto mb-3 size-5 text-primary" />
      <h3 className="mb-1 font-medium">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
