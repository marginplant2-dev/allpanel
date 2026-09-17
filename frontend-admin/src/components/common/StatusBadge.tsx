import { Badge } from "@/components/ui/badge";

const MAP: Record<string, { variant: "default" | "muted" | "live" | "accent"; label: string }> = {
  active: { variant: "default", label: "Active" },
  suspended: { variant: "live", label: "Suspended" },
  inactive: { variant: "muted", label: "Inactive" },
  COMPLETED: { variant: "default", label: "Completed" },
  PENDING: { variant: "accent", label: "Pending" },
  PROCESSING: { variant: "accent", label: "Processing" },
  APPROVED: { variant: "default", label: "Approved" },
  REJECTED: { variant: "live", label: "Rejected" },
  FAILED: { variant: "live", label: "Failed" },
};

export function StatusBadge({ status }: { status: string }) {
  const cfg = MAP[status] ?? { variant: "muted" as const, label: status };
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
}

const ROLE_VARIANT: Record<string, "default" | "accent" | "muted"> = {
  MOTHER_ADMIN: "accent",
  SUPER_ADMIN: "accent",
  MASTER: "default",
  ADMIN: "default",
  AGENT: "default",
  USER: "muted",
};

export function RoleBadge({ role }: { role: string }) {
  return <Badge variant={ROLE_VARIANT[role] ?? "muted"}>{role.replace(/_/g, " ")}</Badge>;
}
