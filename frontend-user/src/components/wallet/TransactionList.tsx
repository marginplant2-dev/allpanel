import { ArrowDownLeft, ArrowUpRight } from "lucide-react";
import type { Transaction } from "@/api/wallet";
import { Badge } from "@/components/ui/badge";
import { formatCredits, formatDateTime } from "@/lib/utils";

export function TransactionList({ items, currentUserId }: { items: Transaction[]; currentUserId?: string }) {
  return (
    <div className="divide-y divide-border rounded-xl border border-border">
      {items.map((t) => {
        const incoming = t.to_user_id === currentUserId;
        return (
          <div key={t.transaction_id} className="flex items-center gap-4 p-4">
            <span
              className={`grid h-10 w-10 place-items-center rounded-full ${
                incoming ? "bg-primary/15 text-primary" : "bg-destructive/15 text-destructive"
              }`}
            >
              {incoming ? <ArrowDownLeft className="h-5 w-5" /> : <ArrowUpRight className="h-5 w-5" />}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium capitalize">
                {t.transaction_type.replace(/_/g, " ").toLowerCase()}
              </p>
              <p className="truncate text-xs text-muted-foreground">{formatDateTime(t.created_at)}</p>
            </div>
            <div className="text-right">
              <p className={`text-sm font-bold ${incoming ? "text-primary" : "text-destructive"}`}>
                {incoming ? "+" : "-"}
                {formatCredits(t.amount)}
              </p>
              <Badge variant={t.status === "COMPLETED" ? "default" : "muted"} className="mt-1">
                {t.status}
              </Badge>
            </div>
          </div>
        );
      })}
    </div>
  );
}
