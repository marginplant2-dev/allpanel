import { CheckCircle2, Info, X, XCircle } from "lucide-react";
import { useToastStore } from "@/store/toast";
import { cn } from "@/lib/utils";

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
};

export function Toaster() {
  const { toasts, dismiss } = useToastStore();
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2">
      {toasts.map((t) => {
        const Icon = ICONS[t.variant];
        return (
          <div
            key={t.id}
            className={cn(
              "flex items-start gap-3 rounded-lg border p-4 shadow-xl backdrop-blur-xl",
              t.variant === "success" && "border-primary/30 bg-primary/10",
              t.variant === "error" && "border-destructive/30 bg-destructive/10",
              t.variant === "info" && "border-border bg-card",
            )}
          >
            <Icon
              className={cn(
                "mt-0.5 h-5 w-5 shrink-0",
                t.variant === "success" && "text-primary",
                t.variant === "error" && "text-destructive",
                t.variant === "info" && "text-muted-foreground",
              )}
            />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">{t.title}</p>
              {t.description && <p className="text-xs text-muted-foreground">{t.description}</p>}
            </div>
            <button onClick={() => dismiss(t.id)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
