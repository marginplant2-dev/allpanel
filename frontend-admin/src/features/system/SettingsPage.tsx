import { useQuery } from "@tanstack/react-query";
import { getMeta } from "@/api/meta";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const FEATURE_FLAGS = [
  { key: "realtime_updates", label: "Realtime updates", enabled: true },
  { key: "casino_catalogue", label: "Casino catalogue", enabled: true },
  { key: "sports_live", label: "Live sports feed", enabled: true },
  { key: "two_factor", label: "Two-factor auth", enabled: false },
];

export default function SettingsPage() {
  const meta = useQuery({ queryKey: ["meta"], queryFn: getMeta });

  return (
    <div>
      <PageHeader title="General Settings" description="Platform configuration and feature flags" />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>System</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Application" value={meta.data?.app ?? "—"} />
            <Row label="Version" value={meta.data?.version ?? "—"} />
            <Row label="Environment" value={meta.data?.environment ?? "—"} />
            <Row label="Credit mode" value="Virtual / demo only" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Feature Flags</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {FEATURE_FLAGS.map((f) => (
              <div key={f.key} className="flex items-center justify-between">
                <span className="text-sm">{f.label}</span>
                <Badge variant={f.enabled ? "default" : "muted"}>{f.enabled ? "Enabled" : "Off"}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium capitalize">{value}</span>
    </div>
  );
}
