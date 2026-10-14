import axios from "axios";
import { toast } from "sonner";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_URL,
});

const TOKEN_KEY = "modelforge_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      clearToken();
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

// Plain <a href> links can't send the bearer token, so fetch the file through apiClient and save the blob.
// The API first fetches the file from S3, so a big model takes a few seconds: show progress meanwhile.
// On failure the toast is dismissed and the error re-thrown, so callers keep showing the reason.
export async function downloadArtifact(artifact: { id: string; file_path: string }): Promise<void> {
  const filename = artifact.file_path.split("/").pop() ?? artifact.id;
  const toastId = toast.loading(`Preparing download: ${filename}`);
  try {
    const { data } = await apiClient.get<Blob>(`/api/artifacts/${artifact.id}/download`, { responseType: "blob" });
    const url = URL.createObjectURL(data);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Download started: ${filename}`, { id: toastId });
  } catch (error) {
    toast.dismiss(toastId);
    throw error;
  }
}

export function apiErrorMessage(error: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    // FastAPI validation errors (422) are a list: [{ loc: ["body", "email"], msg: "..." }, ...]
    if (Array.isArray(detail) && detail[0]?.msg) {
      const field = detail[0].loc?.at(-1);
      return field ? `${field}: ${detail[0].msg}` : detail[0].msg;
    }
    if (error.message) return error.message;
  }
  return fallback;
}
