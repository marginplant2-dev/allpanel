import { ArrowDownToLine, ArrowUpFromLine, Clock } from "lucide-react";
import type { CreditRequest } from "@/api/creditRequests";
import { Badge } from "@/components/ui/badge";
import { formatCredits, formatDateTime } from "@/lib/utils";

const STATUS_VARIANT: Record<CreditRequest["status"], "default" | "accent" | "muted" | "live"> = {
  PENDING: "accent",
  PROCESSING: "accent",
  APPROVED: "default",
  REJECTED: "live",
};

export function RequestList({ items }: { items: CreditRequest[] }) {
  return (
    <div className="divide-y divide-border rounded-xl border border-border">
      {items.map((r) => {
        const isDeposit = r.type === "DEPOSIT";
        return (
          <div key={r.id} className="flex items-center gap-4 p-4">
            <span
              className={`grid h-10 w-10 place-items-center rounded-full ${
                isDeposit ? "bg-primary/15 text-primary" : "bg-secondary text-muted-foreground"
              }`}
            >
              {isDeposit ? <ArrowDownToLine className="h-5 w-5" /> : <ArrowUpFromLine className="h-5 w-5" />}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{isDeposit ? "Deposit request" : "Withdraw request"}</p>
              <p className="flex items-center gap-1 truncate text-xs text-muted-foreground">
                <Clock className="h-3 w-3" /> {formatDateTime(r.created_at)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold">{formatCredits(r.amount)}</p>
              <Badge variant={STATUS_VARIANT[r.status]} className="mt-1">
                {r.status}
              </Badge>
            </div>
          </div>
        );
      })}
    </div>
  );
}
