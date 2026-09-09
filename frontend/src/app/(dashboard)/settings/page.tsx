"use client";

import { useState } from "react";
import { useTheme } from "next-themes";
import { toast } from "sonner";
import { Copy, KeyRound, Plus, Trash2 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { StatusBadge } from "@/components/common/status-badge";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useAuth } from "@/lib/auth-context";
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from "@/hooks/use-api-keys";
import { useHealth } from "@/hooks/use-health";
import { formatDate } from "@/lib/format";
import { apiErrorMessage } from "@/lib/api-client";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage your account, API access and preferences.</p>
      </div>

      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
          <TabsTrigger value="cloud">Cloud</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="mt-4">
          <ProfileTab />
        </TabsContent>
        <TabsContent value="api" className="mt-4">
          <ApiTab />
        </TabsContent>
        <TabsContent value="cloud" className="mt-4">
          <CloudTab />
        </TabsContent>
        <TabsContent value="preferences" className="mt-4">
          <PreferencesTab />
        </TabsContent>
        <TabsContent value="notifications" className="mt-4">
          <NotificationsTab />
        </TabsContent>
        <TabsContent value="security" className="mt-4">
          <SecurityTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return <div className="max-w-xl rounded-xl border border-border bg-surface p-6">{children}</div>;
}

function ProfileTab() {
  const { user } = useAuth();
  return (
    <Card>
      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label>Name</Label>
          <Input value={user?.name ?? ""} disabled />
        </div>
        <div className="space-y-1.5">
          <Label>Email</Label>
          <Input value={user?.email ?? ""} disabled />
        </div>
        <p className="text-xs text-muted-foreground">Profile editing isn&apos;t available in this build yet.</p>
      </div>
    </Card>
  );
}

function ApiTab() {
  const { data: keys, isLoading } = useApiKeys();
  const createKey = useCreateApiKey();
  const revokeKey = useRevokeApiKey();
  const [name, setName] = useState("");
  const [revealedKey, setRevealedKey] = useState<string | null>(null);
  const [revokeTarget, setRevokeTarget] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim()) return;
    try {
      const created = await createKey.mutateAsync(name.trim());
      setRevealedKey(created.key);
      setName("");
    } catch (error) {
      toast.error(apiErrorMessage(error, "Failed to create API key"));
    }
  };

  return (
    <Card>
      <div className="space-y-4">
        <div className="flex gap-2">
          <Input placeholder="Key name, e.g. CI pipeline" value={name} onChange={(e) => setName(e.target.value)} />
          <Button onClick={handleCreate} disabled={createKey.isPending || !name.trim()}>
            <Plus className="size-4" />
            Generate
          </Button>
        </div>

        {revealedKey && (
          <div className="flex items-center justify-between gap-2 rounded-md border border-primary/25 bg-primary/5 p-3 font-mono text-xs">
            <span className="truncate">{revealedKey}</span>
            <button
              onClick={() => {
                navigator.clipboard.writeText(revealedKey);
                toast.success("Copied to clipboard");
              }}
              className="shrink-0 text-primary hover:opacity-80"
            >
              <Copy className="size-3.5" />
            </button>
          </div>
        )}
        {revealedKey && <p className="text-xs text-muted-foreground">Copy this now — it won&apos;t be shown again.</p>}

        <div className="space-y-2">
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : keys && keys.length > 0 ? (
            keys.map((key) => (
              <div key={key.id} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm">
                <div className="flex items-center gap-2">
                  <KeyRound className="size-4 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{key.name}</p>
                    <p className="font-mono text-xs text-muted-foreground">
                      {key.key_prefix}••••••••• · created {formatDate(key.created_at)}
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="icon" className="size-7 text-destructive" onClick={() => setRevokeTarget(key.id)}>
                  <Trash2 className="size-4" />
                </Button>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No API keys yet.</p>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={Boolean(revokeTarget)}
        onOpenChange={(open) => !open && setRevokeTarget(null)}
        title="Revoke this API key?"
        description="Any integration using this key will immediately lose access."
        confirmLabel="Revoke"
        destructive
        onConfirm={() => {
          if (revokeTarget) revokeKey.mutate(revokeTarget);
          setRevokeTarget(null);
        }}
      />
    </Card>
  );
}

function CloudTab() {
  const { data: health, isLoading } = useHealth();
  return (
    <Card>
      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : (
        <div className="space-y-4 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Environment</span>
            <span className="font-mono">{health?.app_env}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">AWS Mode</span>
            <span className="font-mono text-primary">{health?.aws_mode}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Database</span>
            <StatusBadge status={health?.database === "ok" ? "completed" : "failed"} />
          </div>
          <div className="border-t border-border pt-4">
            <p className="mb-2 font-medium">Converter capabilities in this environment</p>
            <div className="space-y-2">
              {health &&
                Object.entries(health.converter_capabilities).map(([name, available]) => (
                  <div key={name} className="flex items-center justify-between">
                    <span className="font-mono uppercase text-muted-foreground">{name}</span>
                    <StatusBadge status={available ? "ready" : "invalid"} />
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

function PreferencesTab() {
  const { theme, setTheme } = useTheme();
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">Dark mode</p>
          <p className="text-xs text-muted-foreground">ModelForge is optimized for a dark, low-glare workspace.</p>
        </div>
        <Switch checked={theme === "dark"} onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")} />
      </div>
    </Card>
  );
}

function NotificationsTab() {
  const [email, setEmail] = useState(true);
  const [browser, setBrowser] = useState(false);
  return (
    <Card>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Email notifications</p>
            <p className="text-xs text-muted-foreground">Get notified when a conversion completes or fails.</p>
          </div>
          <Switch checked={email} onCheckedChange={setEmail} />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Browser notifications</p>
            <p className="text-xs text-muted-foreground">Show a system notification for job updates.</p>
          </div>
          <Switch checked={browser} onCheckedChange={setBrowser} />
        </div>
        <p className="text-xs text-muted-foreground">Preferences are stored locally in this build.</p>
      </div>
    </Card>
  );
}

function SecurityTab() {
  return (
    <Card>
      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label>Current password</Label>
          <Input type="password" disabled />
        </div>
        <div className="space-y-1.5">
          <Label>New password</Label>
          <Input type="password" disabled />
        </div>
        <Button disabled>Update password</Button>
        <p className="text-xs text-muted-foreground">Password changes aren&apos;t available in this build yet.</p>
      </div>
    </Card>
  );
}
