import { useQuery } from "@tanstack/react-query";
import { fetchMyBets } from "@/api/bets";
import { useAuthStore } from "@/store/auth";
import { cn, formatCredits } from "@/lib/utils";

/** Matched (pending) bets — all of them, or just one event's when `eventId` is given. */
export function MyBets({ eventId, className }: { eventId?: string; className?: string }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { data } = useQuery({
    queryKey: ["bets", "PENDING"],
    queryFn: () => fetchMyBets({ status: "PENDING", page_size: 50 }),
    enabled: isAuthenticated,
  });

  const bets = (data?.items ?? []).filter((b) => !eventId || b.event_id === eventId);

  return (
    <section className={cn("border border-ex-line bg-white", className)}>
      <h2 className="ex-sec py-1.5">My Bet</h2>
      <div className="grid grid-cols-[1fr_60px_74px] border-b border-ex-line bg-ex-head px-2 py-1 text-[11px] font-bold text-slate-600">
        <span>Matched Bet</span>
        <span className="text-right">Odds</span>
        <span className="text-right">Stake</span>
      </div>
      {!isAuthenticated ? (
        <p className="px-3 py-5 text-center text-[12px] text-slate-500">Log in to see your bets.</p>
      ) : bets.length === 0 ? (
        <p className="px-3 py-5 text-center text-[12px] text-slate-500">No matched bets yet.</p>
      ) : (
        bets.map((b) => (
          <div
            key={b.id}
            className="grid grid-cols-[1fr_60px_74px] items-center border-b border-ex-line bg-ex-back3 px-2 py-1.5 text-[12px]"
          >
            <span className="truncate font-semibold text-slate-800" title={b.event_name}>
              {b.outcome_name}
              <span className="block truncate text-[11px] font-normal text-slate-500">{b.event_name}</span>
            </span>
            <span className="text-right font-bold text-slate-900">{b.price.toFixed(2)}</span>
            <span className="text-right font-bold text-slate-900">{formatCredits(b.stake)}</span>
          </div>
        ))
      )}
    </section>
  );
}
