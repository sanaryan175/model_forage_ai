import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  Cloud,
  Cpu,
  GitBranch,
  Layers,
  Lock,
  Shield,
  Sparkles,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const FORMATS = ["PyTorch", "ONNX", "TFLite", "TensorRT", "Core ML"];

const STEPS = [
  { title: "Upload", description: "Upload a TorchScript (.pt) or ONNX model — validated on arrival.", icon: Layers },
  { title: "Configure", description: "Pick target formats and an optimization: FP32, FP16 or INT8.", icon: Sparkles },
  { title: "Convert", description: "Parallel conversion pipelines run validation, conversion and optimization.", icon: Cpu },
  { title: "Compare", description: "Real benchmarks — latency, size, accuracy, memory — side by side.", icon: BarChart3 },
];

const ARCHITECTURE_LAYERS = [
  { label: "Amazon S3", detail: "Model storage, versioned by user/model/format" },
  { label: "EventBridge", detail: "Routes new uploads to format-specific pipelines" },
  { label: "SQS + Lambda", detail: "Isolated queues per format with dead-letter handling" },
  { label: "ECS / ECS+GPU", detail: "Containerized converters, GPU tasks for TensorRT" },
  { label: "RDS PostgreSQL", detail: "Jobs, artifacts, benchmarks and logs" },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur">
        <div className="flex items-center gap-2">
          <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Zap className="size-3.5" fill="currentColor" />
          </div>
          <span className="font-semibold tracking-tight">ModelForge</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" nativeButton={false} render={<Link href="/login" />}>
            Sign in
          </Button>
          <Button nativeButton={false} render={<Link href="/register" />}>
            Get started
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="border-b border-border px-6 py-24 text-center">
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="mx-auto inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-xs text-muted-foreground">
            <span className="size-1.5 rounded-full bg-success" />
            Local mock mode available — no AWS account required
          </div>
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
            From trained models
            <br />
            to deployment-ready intelligence.
          </h1>
          <p className="mx-auto max-w-xl text-lg text-muted-foreground">
            Convert, optimize, benchmark and compare your deep-learning models across deployment platforms from a
            single cloud-based workflow.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Button size="lg" nativeButton={false} render={<Link href="/register" />}>
              Start Converting
              <ArrowRight className="size-4" />
            </Button>
            <Button size="lg" variant="outline" nativeButton={false} render={<Link href="/login" />}>
              Explore Dashboard
            </Button>
          </div>
        </div>
      </section>

      {/* Supported formats */}
      <section className="border-b border-border px-6 py-10">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-center gap-3">
          {FORMATS.map((format, i) => (
            <div key={format} className="flex items-center gap-3">
              <span className="rounded-md border border-border bg-surface px-3 py-1.5 font-mono text-sm">
                {format}
              </span>
              {i < FORMATS.length - 1 && <ArrowRight className="size-3.5 text-muted-foreground" />}
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="border-b border-border px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-10 text-center text-2xl font-semibold tracking-tight">How it works</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((step, i) => (
              <div key={step.title} className="rounded-xl border border-border bg-surface p-5">
                <div className="mb-3 flex size-9 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <step.icon className="size-4.5" />
                </div>
                <p className="mb-1 font-mono text-xs text-muted-foreground">Step {i + 1}</p>
                <h3 className="mb-1 font-medium">{step.title}</h3>
                <p className="text-sm text-muted-foreground">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section className="border-b border-border bg-surface/40 px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <div className="mb-10 text-center">
            <h2 className="text-2xl font-semibold tracking-tight">Event-driven cloud architecture</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              The same pipeline runs locally in mock mode and in production on AWS.
            </p>
          </div>
          <div className="space-y-3">
            {ARCHITECTURE_LAYERS.map((layer, i) => (
              <div key={layer.label} className="flex items-center gap-4 rounded-lg border border-border bg-surface p-4">
                <span className="flex size-7 shrink-0 items-center justify-center rounded-full border border-border font-mono text-xs text-muted-foreground">
                  {i + 1}
                </span>
                <div className="flex-1">
                  <p className="font-mono text-sm text-primary">{layer.label}</p>
                  <p className="text-sm text-muted-foreground">{layer.detail}</p>
                </div>
                <GitBranch className="size-4 text-muted-foreground" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benchmarking */}
      <section className="border-b border-border px-6 py-20">
        <div className="mx-auto grid max-w-4xl grid-cols-1 gap-8 sm:grid-cols-2">
          <div>
            <BarChart3 className="mb-3 size-6 text-primary" />
            <h2 className="mb-2 text-xl font-semibold tracking-tight">Real benchmarks, not guesses</h2>
            <p className="text-sm text-muted-foreground">
              Every conversion runs an actual latency, size, accuracy and memory benchmark on this machine.
              Metrics that can&apos;t be measured in your environment are reported as N/A — never fabricated.
            </p>
          </div>
          <div className="space-y-2 rounded-xl border border-border bg-surface p-5 font-mono text-xs">
            <BenchRow label="ONNX" latency="18.4 ms" size="42 MB" />
            <BenchRow label="TFLite / FP16" latency="11.2 ms" size="18 MB" highlight />
            <BenchRow label="TensorRT / FP16" latency="N/A" size="N/A" />
            <BenchRow label="Core ML" latency="N/A" size="6.1 MB" />
          </div>
        </div>
      </section>

      {/* Security */}
      <section className="border-b border-border px-6 py-20">
        <div className="mx-auto grid max-w-4xl grid-cols-1 gap-6 sm:grid-cols-3">
          <SecurityCard icon={Lock} title="JWT authentication" description="Password hashing with bcrypt, signed tokens, protected routes." />
          <SecurityCard icon={Shield} title="Validated uploads" description="Extension, size and ONNX graph checks before anything runs." />
          <SecurityCard icon={Cloud} title="Least-privilege AWS" description="Scoped IAM roles per Lambda and ECS task in production." />
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-24 text-center">
        <h2 className="text-2xl font-semibold tracking-tight">Ready to convert your first model?</h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
          Runs entirely on your machine in local mock mode — no AWS credentials required.
        </p>
        <Button size="lg" className="mt-6" nativeButton={false} render={<Link href="/register" />}>
          Start Converting
          <ArrowRight className="size-4" />
        </Button>
      </section>

      <footer className="border-t border-border px-6 py-6 text-center text-xs text-muted-foreground">
        ModelForge AI — Cloud-based deep learning model compiler & deployment platform.
      </footer>
    </div>
  );
}

function BenchRow({ label, latency, size, highlight }: { label: string; latency: string; size: string; highlight?: boolean }) {
  return (
    <div className={`flex items-center justify-between rounded-md px-2 py-1.5 ${highlight ? "bg-success/10 text-success" : ""}`}>
      <span>{label}</span>
      <span className="tabular-nums">{latency}</span>
      <span className="tabular-nums">{size}</span>
    </div>
  );
}

function SecurityCard({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5 text-center">
      <Icon className="mx-auto mb-3 size-5 text-primary" />
      <h3 className="mb-1 font-medium">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
