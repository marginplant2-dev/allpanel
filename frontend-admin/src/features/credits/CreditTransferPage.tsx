import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Coins } from "lucide-react";
import { fetchUsers } from "@/api/users";
import { transferCredits } from "@/api/misc";
import type { ApiError } from "@/api/client";
import { toast } from "@/store/toast";
import { useDebounce } from "@/hooks/useDebounce";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RoleBadge } from "@/components/common/StatusBadge";
import type { ManagedUser } from "@/types";

export default function CreditTransferPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const debounced = useDebounce(search, 300);
  const [recipient, setRecipient] = useState<ManagedUser | null>(null);
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");

  const recipients = useQuery({
    queryKey: ["users", "transfer-search", debounced],
    queryFn: () => fetchUsers({ page: 1, page_size: 8, search: debounced || undefined }),
    enabled: debounced.length > 0,
  });

  const mutation = useMutation({
    mutationFn: () =>
      transferCredits({
        to_user_id: recipient!.id,
        amount: Number(amount),
        note: note || undefined,
        idempotency_key: crypto.randomUUID(),
      }),
    onSuccess: (txn) => {
      toast.success("Transfer completed", `Ref ${txn.transaction_id.slice(0, 8)}`);
      setAmount("");
      setNote("");
      queryClient.invalidateQueries({ queryKey: ["ledger"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error("Transfer failed", (e as unknown as ApiError)?.message),
  });

  const canSubmit = recipient && Number(amount) > 0;

  return (
    <div className="mx-auto max-w-xl">
      <PageHeader title="Credit Transfer" description="Allocate virtual credits to a downline account" />
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Coins className="h-5 w-5 text-primary" /> New Transfer
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label>Recipient</Label>
            {recipient ? (
              <div className="flex items-center justify-between rounded-md border border-border bg-secondary/40 px-3 py-2">
                <div>
                  <span className="font-medium">{recipient.full_name}</span>{" "}
                  <span className="text-sm text-muted-foreground">@{recipient.username}</span>
                </div>
                <div className="flex items-center gap-2">
                  <RoleBadge role={recipient.role} />
                  <Button size="sm" variant="ghost" onClick={() => setRecipient(null)}>
                    Change
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <Input placeholder="Search a user in your hierarchy…" value={search} onChange={(e) => setSearch(e.target.value)} />
                {recipients.data && recipients.data.items.length > 0 && (
                  <div className="mt-1 divide-y divide-border rounded-md border border-border">
                    {recipients.data.items.map((u) => (
                      <button
                        key={u.id}
                        className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-secondary/40"
                        onClick={() => {
                          setRecipient(u);
                          setSearch("");
                        }}
                      >
                        <span>
                          {u.full_name} <span className="text-muted-foreground">@{u.username}</span>
                        </span>
                        <RoleBadge role={u.role} />
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="amount">Amount (virtual credits)</Label>
            <Input id="amount" type="number" min={1} value={amount} onChange={(e) => setAmount(e.target.value)} />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="note">Note (optional)</Label>
            <Input id="note" value={note} onChange={(e) => setNote(e.target.value)} />
          </div>

          <Button className="w-full" disabled={!canSubmit || mutation.isPending} onClick={() => mutation.mutate()}>
            {mutation.isPending ? "Processing…" : "Transfer credits"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
