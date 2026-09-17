import { useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { fetchTransactions } from "@/api/wallet";
import { useAuthStore } from "@/store/auth";
import { TransactionList } from "@/components/wallet/TransactionList";
import { EmptyState, ErrorState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type Direction = "all" | "in" | "out";

export default function CreditHistoryPage() {
  const user = useAuthStore((s) => s.user);
  const [page, setPage] = useState(1);
  const [direction, setDirection] = useState<Direction>("all");

  const query = useQuery({
    queryKey: ["wallet-transactions", { page, direction }],
    queryFn: () =>
      fetchTransactions({
        page,
        page_size: 15,
        direction: direction === "all" ? undefined : direction,
      }),
    placeholderData: keepPreviousData,
  });

  const meta = query.data?.meta;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Virtual Credit History</h1>
        <div className="flex rounded-lg border border-border p-1">
          {(["all", "in", "out"] as const).map((d) => (
            <button
              key={d}
              onClick={() => {
                setDirection(d);
                setPage(1);
              }}
              className={cn(
                "rounded-md px-3 py-1 text-sm font-medium capitalize transition-colors",
                direction === d ? "bg-secondary text-foreground" : "text-muted-foreground",
              )}
            >
              {d === "in" ? "Received" : d === "out" ? "Sent" : "All"}
            </button>
          ))}
        </div>
      </div>

      {query.isError ? (
        <ErrorState onRetry={() => query.refetch()} />
      ) : query.isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : query.data && query.data.items.length > 0 ? (
        <>
          <TransactionList items={query.data.items} currentUserId={user?.id} />
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              Page {meta?.page} of {meta?.pages || 1} · {meta?.total} total
            </span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!!meta && page >= meta.pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      ) : (
        <EmptyState title="No transactions" description="Your credit history will appear here." />
      )}
    </div>
  );
}
