"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { FileDropzone } from "@/components/upload/file-dropzone";
import { useUploadModel } from "@/hooks/use-models";
import { apiErrorMessage } from "@/lib/api-client";

export default function UploadModelPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [uploadedId, setUploadedId] = useState<string | null>(null);
  const upload = useUploadModel();

  const handleUpload = async () => {
    if (!file) return;
    try {
      const model = await upload.mutateAsync({ name: name || file.name, file });
      setUploadedId(model.id);
      toast.success("Model successfully uploaded");
    } catch (error) {
      toast.error(apiErrorMessage(error, "Upload failed"));
    }
  };

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <Link href="/models" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" />
        Back to models
      </Link>

      <div>
        <h1 className="text-xl font-semibold tracking-tight">Upload Model</h1>
        <p className="text-sm text-muted-foreground">Supported formats: TorchScript (.pt) and ONNX (.onnx).</p>
      </div>

      {uploadedId ? (
        <div className="space-y-4 rounded-xl border border-success/25 bg-success/5 p-6 text-center">
          <CheckCircle2 className="mx-auto size-8 text-success" />
          <p className="font-medium">Model successfully uploaded</p>
          <p className="text-sm text-muted-foreground">Your model is being validated. Continue to configure a conversion.</p>
          <div className="flex justify-center gap-2">
            <Button variant="outline" onClick={() => router.push("/models")}>
              View all models
            </Button>
            <Button onClick={() => router.push(`/models/${uploadedId}`)}>Start Conversion</Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4 rounded-xl border border-border bg-surface p-6">
          <div className="space-y-1.5">
            <Label htmlFor="model-name">Model name</Label>
            <Input
              id="model-name"
              placeholder="ResNet18 Image Classifier"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Model file</Label>
            <FileDropzone file={file} onFileSelected={setFile} disabled={upload.isPending} />
          </div>

          {upload.isPending && (
            <div className="space-y-1.5">
              <p className="text-xs text-muted-foreground">Uploading...</p>
              <Progress value={66} className="h-1.5" />
            </div>
          )}

          <Button className="w-full" disabled={!file || upload.isPending} onClick={handleUpload}>
            {upload.isPending ? "Uploading..." : "Upload Model"}
          </Button>
        </div>
      )}
    </div>
  );
}
