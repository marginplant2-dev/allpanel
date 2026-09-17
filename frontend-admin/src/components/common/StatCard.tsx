import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function StatCard({
  icon: Icon,
  label,
  value,
  loading,
  accent = "primary",
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  loading?: boolean;
  accent?: "primary" | "accent";
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between py-5">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          {loading ? (
            <Skeleton className="mt-2 h-7 w-20" />
          ) : (
            <p className="mt-1 text-2xl font-bold">{value}</p>
          )}
        </div>
        <span
          className={`grid h-11 w-11 place-items-center rounded-xl ${
            accent === "accent" ? "bg-accent/15 text-accent" : "bg-primary/15 text-primary"
          }`}
        >
          <Icon className="h-5 w-5" />
        </span>
      </CardContent>
    </Card>
  );
}
