import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowDownToLine, ArrowUpFromLine, Check } from "lucide-react";
import { createCreditRequest, type CreditRequestType } from "@/api/creditRequests";
import type { ApiError } from "@/api/client";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

const QUICK_AMOUNTS = [100, 500, 1000, 5000];

export function DepositWithdrawDialog({
  open,
  onOpenChange,
  defaultType = "DEPOSIT",
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultType?: CreditRequestType;
}) {
  const queryClient = useQueryClient();
  const [type, setType] = useState<CreditRequestType>(defaultType);
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");

  const mutation = useMutation({
    mutationFn: () => createCreditRequest({ type, amount: Number(amount), note: note || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["credit-requests"] });
    },
  });

  const canSubmit = Number(amount) > 0;
  const error = mutation.error as ApiError | null;

  function reset() {
    setAmount("");
    setNote("");
    mutation.reset();
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        onOpenChange(next);
        if (!next) reset();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{type === "DEPOSIT" ? "Deposit credits" : "Withdraw credits"}</DialogTitle>
          <DialogDescription>
            {type === "DEPOSIT"
              ? "Request virtual credits from your agent. They'll review and approve it."
              : "Send virtual credits back to your agent's pool for approval."}
          </DialogDescription>
        </DialogHeader>

        {mutation.isSuccess ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <span className="grid h-12 w-12 place-items-center rounded-full bg-primary/15 text-primary">
              <Check className="h-6 w-6" />
            </span>
            <p className="font-medium">Request submitted</p>
            <p className="text-sm text-muted-foreground">
              Your {type.toLowerCase()} request is pending approval. You'll be notified once it's reviewed.
            </p>
            <Button className="mt-2 w-full" onClick={() => onOpenChange(false)}>
              Done
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2 rounded-lg bg-secondary/50 p-1">
              {(["DEPOSIT", "WITHDRAW"] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setType(t)}
                  className={cn(
                    "flex items-center justify-center gap-1.5 rounded-md py-2 text-sm font-semibold transition-colors",
                    type === t ? "bg-primary text-primary-foreground shadow" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {t === "DEPOSIT" ? <ArrowDownToLine className="h-4 w-4" /> : <ArrowUpFromLine className="h-4 w-4" />}
                  {t === "DEPOSIT" ? "Deposit" : "Withdraw"}
                </button>
              ))}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="amount">Amount</Label>
              <Input
                id="amount"
                type="number"
                min={1}
                placeholder="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                autoFocus
              />
              <div className="flex flex-wrap gap-2 pt-1">
                {QUICK_AMOUNTS.map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setAmount(String(v))}
                    className="rounded-full border border-border px-3 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-primary hover:text-primary"
                  >
                    +{v}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="note">Note (optional)</Label>
              <Input id="note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. weekly top-up" />
            </div>

            {error && <p className="text-sm text-destructive">{error.message}</p>}

            <Button className="w-full" size="lg" disabled={!canSubmit || mutation.isPending} onClick={() => mutation.mutate()}>
              {mutation.isPending ? "Submitting…" : `Request ${type === "DEPOSIT" ? "deposit" : "withdrawal"}`}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
