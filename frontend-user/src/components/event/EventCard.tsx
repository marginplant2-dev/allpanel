import { Link } from "react-router-dom";
import { Clock } from "lucide-react";
import type { SportEvent } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/utils";

export function EventCard({ event }: { event: SportEvent }) {
  const isLive = event.status === "live";
  const score = (event.score ?? {}) as Record<string, number>;

  return (
    <Link
      to={`/events/${event.id}`}
      className="group block rounded-xl border border-border bg-card p-4 transition-all hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5"
    >
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {event.league ?? "Event"}
        </span>
        {isLive ? (
          <Badge variant="live">
            <span className="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-destructive" />
            LIVE
          </Badge>
        ) : (
          <Badge variant="muted">Upcoming</Badge>
        )}
      </div>

      <div className="space-y-2">
        {event.participants.map((p) => (
          <div key={p} className="flex items-center justify-between">
            <span className="text-sm font-medium">{p}</span>
            {isLive && <span className="text-sm font-bold text-primary">{score[p] ?? 0}</span>}
          </div>
        ))}
      </div>

      {!isLive && (
        <div className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
          <Clock className="h-3.5 w-3.5" />
          {formatDateTime(event.start_time)}
        </div>
      )}
    </Link>
  );
}

export function EventCardSkeleton() {
  return (
    <div className="rounded-xl border border-border p-4">
      <Skeleton className="mb-3 h-3 w-24" />
      <Skeleton className="mb-2 h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}
