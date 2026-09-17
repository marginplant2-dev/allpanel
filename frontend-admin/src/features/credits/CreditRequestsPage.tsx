import { useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDownToLine, ArrowUpFromLine, Check, X } from "lucide-react";
import { decideCreditRequest, fetchCreditRequests } from "@/api/misc";
import type { ApiError } from "@/api/client";
import { toast } from "@/store/toast";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable, type Column } from "@/components/data/DataTable";
import { Pagination } from "@/components/data/Pagination";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import type { CreditRequest } from "@/types";
import { formatCredits, formatDateTime } from "@/lib/utils";

export default function CreditRequestsPage() {
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["credit-requests", "inbox", page],
    queryFn: () => fetchCreditRequests({ page, page_size: 20 }),
    placeholderData: keepPreviousData,
  });

  const decide = useMutation({
    mutationFn: ({ id, action }: { id: string; action: "approve" | "reject" }) => decideCreditRequest(id, action),
    onSuccess: (_res, { action }) => {
      toast.success(action === "approve" ? "Request approved" : "Request rejected");
      queryClient.invalidateQueries({ queryKey: ["credit-requests"] });
      queryClient.invalidateQueries({ queryKey: ["ledger"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error("Action failed", (e as unknown as ApiError)?.message),
  });

  const cols: Column<CreditRequest>[] = [
    {
      key: "user",
      header: "Requester",
      render: (r) => <span className="font-medium">@{r.username}</span>,
    },
    {
      key: "type",
      header: "Type",
      render: (r) => (
        <span className="flex items-center gap-1.5">
          {r.type === "DEPOSIT" ? (
            <ArrowDownToLine className="h-4 w-4 text-primary" />
          ) : (
            <ArrowUpFromLine className="h-4 w-4 text-muted-foreground" />
          )}
          {r.type === "DEPOSIT" ? "Deposit" : "Withdraw"}
        </span>
      ),
    },
    { key: "amount", header: "Amount", render: (r) => <span className="font-semibold">{formatCredits(r.amount)}</span> },
    { key: "note", header: "Note", render: (r) => <span className="text-muted-foreground">{r.note || "—"}</span> },
    { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
    { key: "date", header: "Requested", render: (r) => <span className="text-muted-foreground">{formatDateTime(r.created_at)}</span> },
    {
      key: "actions",
      header: "",
      className: "text-right",
      render: (r) =>
        r.status === "PENDING" ? (
          <div className="flex justify-end gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={decide.isPending}
              onClick={() => decide.mutate({ id: r.id, action: "reject" })}
            >
              <X className="h-4 w-4" /> Reject
            </Button>
            <Button size="sm" disabled={decide.isPending} onClick={() => decide.mutate({ id: r.id, action: "approve" })}>
              <Check className="h-4 w-4" /> Approve
            </Button>
          </div>
        ) : null,
    },
  ];

  return (
    <div>
      <PageHeader title="Deposit & Withdraw Requests" description="Approve or reject credit requests from your direct downline" />
      <DataTable
        columns={cols}
        rows={query.data?.items}
        rowKey={(r) => r.id}
        isLoading={query.isLoading}
        isError={query.isError}
        onRetry={() => query.refetch()}
        emptyTitle="No requests"
        emptyDescription="Deposit and withdraw requests from your direct users will show up here."
      />
      <Pagination meta={query.data?.meta} page={page} onPageChange={setPage} />
    </div>
  );
}
