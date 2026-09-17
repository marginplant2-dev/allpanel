import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { activateUser, fetchUser, fetchUserActivity, suspendUser } from "@/api/users";
import { toast } from "@/store/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RoleBadge, StatusBadge } from "@/components/common/StatusBadge";
import { DataTable, type Column } from "@/components/data/DataTable";
import { ErrorState } from "@/components/common/States";
import { Skeleton } from "@/components/ui/skeleton";
import type { AuditLog } from "@/types";
import { formatCredits, formatDateTime } from "@/lib/utils";

export default function UserDetailPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const user = useQuery({ queryKey: ["user", id], queryFn: () => fetchUser(id) });
  const activity = useQuery({ queryKey: ["user-activity", id], queryFn: () => fetchUserActivity(id, { page_size: 15 }) });

  const statusMutation = useMutation({
    mutationFn: (suspend: boolean) => (suspend ? suspendUser(id) : activateUser(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", id] });
      toast.success("Status updated");
    },
  });

  if (user.isLoading) return <Skeleton className="h-64 w-full" />;
  if (user.isError || !user.data) return <ErrorState onRetry={() => user.refetch()} />;
  const u = user.data;

  const cols: Column<AuditLog>[] = [
    { key: "action", header: "Action", render: (a) => <span className="font-medium">{a.action.replace(/_/g, " ")}</span> },
    { key: "date", header: "When", render: (a) => <span className="text-muted-foreground">{formatDateTime(a.created_at)}</span> },
    { key: "ip", header: "IP", render: (a) => <span className="text-muted-foreground">{a.ip_address ?? "—"}</span> },
  ];

  return (
    <div>
      <button onClick={() => navigate("/users")} className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to users
      </button>

      <PageHeader
        title={u.full_name}
        description={`@${u.username}`}
        action={
          u.status === "suspended" ? (
            <Button onClick={() => statusMutation.mutate(false)}>Activate</Button>
          ) : (
            <Button variant="outline" className="text-destructive" onClick={() => statusMutation.mutate(true)}>
              Suspend
            </Button>
          )
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Account</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Role" value={<RoleBadge role={u.role} />} />
            <Row label="Status" value={<StatusBadge status={u.status} />} />
            <Row label="Credit limit" value={formatCredits(u.credit_limit)} />
            <Row label="Created" value={u.created_at ? formatDateTime(u.created_at) : "—"} />
            <Row label="Last login" value={u.last_login ? formatDateTime(u.last_login) : "—"} />
            <Row label="Notes" value={u.notes ?? "—"} />
          </CardContent>
        </Card>

        <div className="lg:col-span-2">
          <h2 className="mb-3 font-semibold">Activity</h2>
          <DataTable columns={cols} rows={activity.data?.items} rowKey={(a) => a.id} isLoading={activity.isLoading} emptyTitle="No activity" />
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
