"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Input } from "@/components/ui/input";
import { useCreateConversion } from "@/hooks/use-conversions";
import { apiErrorMessage } from "@/lib/api-client";
import type { ModelFramework, OptimizationType, TargetFormat } from "@/types/api";

const FORMATS: { value: TargetFormat; label: string }[] = [
  { value: "tflite", label: "TFLite" },
  { value: "tensorrt", label: "TensorRT" },
  { value: "coreml", label: "Core ML" },
];

export function ConversionConfigDialog({
  modelId,
  modelFramework,
  trigger,
}: {
  modelId: string;
  modelFramework: ModelFramework;
  trigger: React.ReactElement;
}) {
  const [open, setOpen] = useState(false);
  const [formats, setFormats] = useState<TargetFormat[]>(["tflite"]);
  const [optimization, setOptimization] = useState<OptimizationType>("fp32");
  const [batchSize, setBatchSize] = useState(1);
  const [targetDevice, setTargetDevice] = useState("cpu");
  const [inputShape, setInputShape] = useState("1, 3, 224, 224");
  const createConversion = useCreateConversion();
  const router = useRouter();

  const toggleFormat = (format: TargetFormat) => {
    setFormats((prev) => (prev.includes(format) ? prev.filter((f) => f !== format) : [...prev, format]));
  };

  const handleSubmit = async () => {
    if (formats.length === 0) {
      toast.error("Select at least one target format");
      return;
    }
    const parsedShape = inputShape
      .split(",")
      .map((d) => parseInt(d.trim(), 10))
      .filter((d) => !Number.isNaN(d));

    try {
      const jobs = await createConversion.mutateAsync({
        model_id: modelId,
        target_formats: formats,
        optimization,
        batch_size: batchSize,
        target_device: targetDevice,
        input_shape: modelFramework === "pytorch" ? parsedShape : undefined,
      });
      toast.success(`Started ${jobs.length} conversion job${jobs.length > 1 ? "s" : ""}`);
      setOpen(false);
      router.push(`/conversions/${jobs[0].id}`);
    } catch (error) {
      toast.error(apiErrorMessage(error, "Failed to start conversion"));
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={trigger} />
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Configure Conversion</DialogTitle>
          <DialogDescription>Choose target formats and optimization for this model.</DialogDescription>
        </DialogHeader>

        <div className="space-y-5">
          <div className="space-y-2">
            <Label>Target Formats</Label>
            <div className="space-y-2">
              {FORMATS.map((format) => (
                <label key={format.value} className="flex items-center gap-2 text-sm">
                  <Checkbox
                    checked={formats.includes(format.value)}
                    onCheckedChange={() => toggleFormat(format.value)}
                  />
                  {format.label}
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Optimization</Label>
            <RadioGroup value={optimization} onValueChange={(v) => setOptimization(v as OptimizationType)}>
              {(["fp32", "fp16", "int8"] as const).map((opt) => (
                <label key={opt} className="flex items-center gap-2 text-sm">
                  <RadioGroupItem value={opt} />
                  {opt.toUpperCase()}
                </label>
              ))}
            </RadioGroup>
          </div>

          <details className="rounded-md border border-border p-3 text-sm">
            <summary className="cursor-pointer font-medium">Advanced options</summary>
            <div className="mt-3 space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="batch-size">Batch size</Label>
                <Input
                  id="batch-size"
                  type="number"
                  min={1}
                  value={batchSize}
                  onChange={(e) => setBatchSize(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="target-device">Target device</Label>
                <Input id="target-device" value={targetDevice} onChange={(e) => setTargetDevice(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="input-shape">
                  Input shape {modelFramework === "pytorch" && <span className="text-destructive">(required)</span>}
                </Label>
                <Input
                  id="input-shape"
                  placeholder="1, 3, 224, 224"
                  value={inputShape}
                  onChange={(e) => setInputShape(e.target.value)}
                />
                {modelFramework === "pytorch" && (
                  <p className="text-xs text-muted-foreground">
                    Required to export this TorchScript model to ONNX before conversion.
                  </p>
                )}
              </div>
            </div>
          </details>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={createConversion.isPending}>
            {createConversion.isPending ? "Starting..." : "Start Conversion"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
