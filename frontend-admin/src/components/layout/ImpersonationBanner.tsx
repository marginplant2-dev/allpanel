import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Eye, LogOut } from "lucide-react";
import { endImpersonation } from "@/api/misc";
import { useAuthStore } from "@/store/auth";
import { toast } from "@/store/toast";
import { Button } from "@/components/ui/button";

export function ImpersonationBanner() {
  const impersonation = useAuthStore((s) => s.impersonation);
  const stopImpersonation = useAuthStore((s) => s.stopImpersonation);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: endImpersonation,
    onSuccess: (data) => {
      stopImpersonation(data.user, data.access_token);
      queryClient.clear();
      toast.success("Returned to your account");
    },
    onError: () => toast.error("Could not end impersonation"),
  });

  if (!impersonation) return null;

  return (
    <div className="flex items-center gap-3 border-b border-accent/40 bg-accent/15 px-4 py-2 text-sm">
      <Eye className="h-4 w-4 text-accent" />
      <span>
        Viewing as <strong>{impersonation.targetUser.full_name}</strong> (@
        {impersonation.targetUser.username}) — actions are performed as this account.
      </span>
      <Button
        size="sm"
        variant="outline"
        className="ml-auto"
        disabled={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        <LogOut className="h-4 w-4" /> Exit
      </Button>
    </div>
  );
}
