import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowDownToLine, ArrowUpFromLine, ChevronRight, Lock, Wallet as WalletIcon } from "lucide-react";
import { fetchTransactions, fetchWallet } from "@/api/wallet";
import { fetchMyCreditRequests, type CreditRequestType } from "@/api/creditRequests";
import { useAuthStore } from "@/store/auth";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TransactionList } from "@/components/wallet/TransactionList";
import { RequestList } from "@/components/wallet/RequestList";
import { DepositWithdrawDialog } from "@/components/wallet/DepositWithdrawDialog";
import { EmptyState, SectionHeader } from "@/components/common/States";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCredits } from "@/lib/utils";

export default function WalletPage() {
  const user = useAuthStore((s) => s.user);
  const wallet = useQuery({ queryKey: ["wallet"], queryFn: fetchWallet });
  const txns = useQuery({
    queryKey: ["wallet-transactions", { page: 1 }],
    queryFn: () => fetchTransactions({ page: 1, page_size: 5 }),
  });
  const requests = useQuery({
    queryKey: ["credit-requests", { page: 1 }],
    queryFn: () => fetchMyCreditRequests({ page: 1, page_size: 5 }),
  });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<CreditRequestType>("DEPOSIT");

  function openDialog(type: CreditRequestType) {
    setDialogType(type);
    setDialogOpen(true);
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">My Virtual Wallet</h1>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="overflow-hidden">
          <div className="bg-gradient-to-br from-primary/20 to-transparent">
            <CardContent className="space-y-4 py-6">
              <div className="flex items-center gap-4">
                <span className="grid h-12 w-12 place-items-center rounded-xl bg-primary/20 text-primary">
                  <WalletIcon className="h-6 w-6" />
                </span>
                <div>
                  <p className="text-sm text-muted-foreground">Available Credits</p>
                  {wallet.isLoading ? (
                    <Skeleton className="mt-1 h-8 w-32" />
                  ) : (
                    <p className="text-3xl font-extrabold">{formatCredits(wallet.data?.available_balance ?? 0)}</p>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <Button className="flex-1" onClick={() => openDialog("DEPOSIT")}>
                  <ArrowDownToLine className="h-4 w-4" /> Deposit
                </Button>
                <Button variant="outline" className="flex-1" onClick={() => openDialog("WITHDRAW")}>
                  <ArrowUpFromLine className="h-4 w-4" /> Withdraw
                </Button>
              </div>
            </CardContent>
          </div>
        </Card>

        <Card>
          <CardContent className="flex items-center gap-4 py-6">
            <span className="grid h-12 w-12 place-items-center rounded-xl bg-secondary text-muted-foreground">
              <Lock className="h-6 w-6" />
            </span>
            <div>
              <p className="text-sm text-muted-foreground">Locked Credits</p>
              {wallet.isLoading ? (
                <Skeleton className="mt-1 h-8 w-24" />
              ) : (
                <p className="text-3xl font-extrabold">{formatCredits(wallet.data?.locked_balance ?? 0)}</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <section>
        <SectionHeader title="Deposit & Withdraw Requests" />
        {requests.isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : requests.data && requests.data.items.length > 0 ? (
          <RequestList items={requests.data.items} />
        ) : (
          <EmptyState title="No requests yet" description="Deposit or withdraw requests will appear here." />
        )}
      </section>

      <section>
        <SectionHeader
          title="Recent Activity"
          action={
            <Button variant="ghost" size="sm" asChild>
              <Link to="/wallet/history">
                View all <ChevronRight className="h-4 w-4" />
              </Link>
            </Button>
          }
        />
        {txns.isLoading ? (
          <Skeleton className="h-48 w-full" />
        ) : txns.data && txns.data.items.length > 0 ? (
          <TransactionList items={txns.data.items} currentUserId={user?.id} />
        ) : (
          <EmptyState title="No transactions yet" description="Credit transfers will appear here." />
        )}
      </section>

      <DepositWithdrawDialog key={dialogType} open={dialogOpen} onOpenChange={setDialogOpen} defaultType={dialogType} />
    </div>
  );
}
