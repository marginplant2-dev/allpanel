import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { fetchAuditLogs } from "@/api/misc";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable, type Column } from "@/components/data/DataTable";
import { Pagination } from "@/components/data/Pagination";
import { Badge } from "@/components/ui/badge";
import type { AuditLog } from "@/types";
import { formatDateTime } from "@/lib/utils";

export default function AuditLogsPage() {
  const [page, setPage] = useState(1);
  const query = useQuery({
    queryKey: ["audit", page],
    queryFn: () => fetchAuditLogs({ page, page_size: 20 }),
    placeholderData: keepPreviousData,
  });

  const cols: Column<AuditLog>[] = [
    { key: "action", header: "Action", render: (a) => <Badge variant="muted">{a.action.replace(/_/g, " ")}</Badge> },
    { key: "actor", header: "Actor", render: (a) => <span className="font-mono text-xs">{a.actor_id?.slice(0, 10) ?? "—"}</span> },
    { key: "target", header: "Target", render: (a) => <span className="font-mono text-xs">{a.target_id?.slice(0, 10) ?? "—"}</span> },
    { key: "ip", header: "IP", render: (a) => <span className="text-muted-foreground">{a.ip_address ?? "—"}</span> },
    { key: "date", header: "When", render: (a) => <span className="text-muted-foreground">{formatDateTime(a.created_at)}</span> },
  ];

  return (
    <div>
      <PageHeader title="Audit Logs" description="Security-relevant actions across your hierarchy" />
      <DataTable
        columns={cols}
        rows={query.data?.items}
        rowKey={(a) => a.id}
        isLoading={query.isLoading}
        isError={query.isError}
        onRetry={() => query.refetch()}
        emptyTitle="No audit records"
      />
      <Pagination meta={query.data?.meta} page={page} onPageChange={setPage} />
    </div>
  );
}
