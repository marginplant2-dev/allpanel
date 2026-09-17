import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { fetchLedger } from "@/api/misc";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable, type Column } from "@/components/data/DataTable";
import { Pagination } from "@/components/data/Pagination";
import { StatusBadge } from "@/components/common/StatusBadge";
import type { Transaction } from "@/types";
import { formatCredits, formatDateTime } from "@/lib/utils";

export default function LedgerPage() {
  const [page, setPage] = useState(1);
  const query = useQuery({
    queryKey: ["ledger", page],
    queryFn: () => fetchLedger({ page, page_size: 20 }),
    placeholderData: keepPreviousData,
  });

  const cols: Column<Transaction>[] = [
    { key: "id", header: "Reference", render: (t) => <span className="font-mono text-xs">{t.transaction_id.slice(0, 12)}</span> },
    { key: "type", header: "Type", render: (t) => <span className="capitalize">{t.transaction_type.replace(/_/g, " ").toLowerCase()}</span> },
    { key: "amount", header: "Amount", render: (t) => <span className="font-semibold">{formatCredits(t.amount)}</span> },
    { key: "status", header: "Status", render: (t) => <StatusBadge status={t.status} /> },
    { key: "date", header: "Date", render: (t) => <span className="text-muted-foreground">{formatDateTime(t.created_at)}</span> },
  ];

  return (
    <div>
      <PageHeader title="Transaction Ledger" description="All virtual credit movements within your hierarchy" />
      <DataTable
        columns={cols}
        rows={query.data?.items}
        rowKey={(t) => t.transaction_id}
        isLoading={query.isLoading}
        isError={query.isError}
        onRetry={() => query.refetch()}
        emptyTitle="No transactions"
      />
      <Pagination meta={query.data?.meta} page={page} onPageChange={setPage} />
    </div>
  );
}
