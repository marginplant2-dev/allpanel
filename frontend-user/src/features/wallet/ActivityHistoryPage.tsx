import { useQuery } from "@tanstack/react-query";
import { Activity } from "lucide-react";
import { fetchTransactions } from "@/api/wallet";
import { useAuthStore } from "@/store/auth";
import { TransactionList } from "@/components/wallet/TransactionList";
import { EmptyState } from "@/components/common/States";
import { Skeleton } from "@/components/ui/skeleton";

export default function ActivityHistoryPage() {
  const user = useAuthStore((s) => s.user);
  const query = useQuery({
    queryKey: ["wallet-transactions", "activity"],
    queryFn: () => fetchTransactions({ page: 1, page_size: 25 }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Activity className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">Activity History</h1>
      </div>
      <p className="text-sm text-muted-foreground">
        A record of your account&apos;s virtual credit activity.
      </p>

      {query.isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : query.data && query.data.items.length > 0 ? (
        <TransactionList items={query.data.items} currentUserId={user?.id} />
      ) : (
        <EmptyState title="No activity yet" description="Your account activity will appear here." />
      )}
    </div>
  );
}
