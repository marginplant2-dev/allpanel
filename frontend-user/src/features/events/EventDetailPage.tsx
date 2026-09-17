import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchEvent, fetchLiveData } from "@/api/sports";
import type { Bookmaker, EventDetail } from "@/types";
import { ErrorState } from "@/components/common/States";
import { BetSlip, type BetSelection } from "@/components/bets/BetSlip";
import { MyBets } from "@/components/bets/MyBets";
import { layPrice } from "@/components/exchange/OddsGrid";
import { useAuthStore } from "@/store/auth";
import { cn, formatDateTime } from "@/lib/utils";

interface Runner {
  name: string;
  price: number;
  bookmakerKey: string;
  bookmakerTitle: string;
}

/** Best h2h price per runner across books — the headline "Match Odds" market. */
function bestRunners(bookmakers: Bookmaker[]): Runner[] {
  const best = new Map<string, Runner>();
  for (const b of bookmakers) {
    for (const m of b.markets) {
      if (m.key !== "h2h") continue;
      for (const o of m.outcomes) {
        const current = best.get(o.name);
        if (!current || o.price > current.price) {
          best.set(o.name, { name: o.name, price: o.price, bookmakerKey: b.key, bookmakerTitle: b.title });
        }
      }
    }
  }
  return [...best.values()];
}

function bookmakerRunners(b: Bookmaker): Runner[] {
  const market = b.markets.find((m) => m.key === "h2h");
  return (market?.outcomes ?? []).map((o) => ({
    name: o.name,
    price: o.price,
    bookmakerKey: b.key,
    bookmakerTitle: b.title,
  }));
}

const ROW = "grid-cols-[1fr_58px_58px_46px] sm:grid-cols-[1fr_84px_84px_58px]";

function MarketBox({
  title,
  runners,
  suspended,
  selected,
  onSelect,
}: {
  title: string;
  runners: Runner[];
  suspended: boolean;
  selected?: string;
  onSelect: (runner: Runner) => void;
}) {
  if (runners.length === 0) return null;
  return (
    <section className="border border-ex-line bg-white">
      <div className="bg-ex-nav px-3 py-1.5">
        <h2 className="truncate text-[13px] font-bold uppercase text-white">{title}</h2>
      </div>

      <div className={cn("ex-head grid items-center border-b border-ex-line", ROW)}>
        <span className="px-2 py-1.5">Runner</span>
        <span className="grid place-items-center border-l border-ex-line py-1.5">Back</span>
        <span className="grid place-items-center border-l border-ex-line py-1.5">Lay</span>
        <span className="grid place-items-center border-l border-ex-line py-1.5">Limit</span>
      </div>

      {runners.map((r) => (
        <div key={r.name} className={cn("relative grid items-center border-b border-ex-line", ROW)}>
          <span className="truncate px-2 py-2 text-[13px] font-semibold text-slate-800">{r.name}</span>
          <button
            type="button"
            disabled={suspended}
            onClick={() => onSelect(r)}
            className={cn(
              "ex-cell h-10 bg-ex-back",
              !suspended && "cursor-pointer hover:brightness-105",
              selected === r.name && "ring-2 ring-inset ring-ex-brand",
            )}
          >
            {r.price.toFixed(2)}
          </button>
          {/* lay is display-only — see the LAY_SPREAD note in OddsGrid */}
          <span className="ex-cell h-10 bg-ex-lay">{layPrice(r.price).toFixed(2)}</span>
          <span className="grid h-10 place-items-center border-l border-ex-line text-[10px] leading-tight text-slate-500">
            <span>Min 100</span>
            <span>Max 50K</span>
          </span>
          {suspended && (
            <span className="absolute inset-y-0 right-0 grid w-[162px] place-items-center bg-ex-suspend text-[11px] font-bold uppercase tracking-wide text-white sm:w-[226px]">
              Suspended
            </span>
          )}
        </div>
      ))}
    </section>
  );
}

export default function EventDetailPage() {
  const { eventId = "" } = useParams();
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [selection, setSelection] = useState<BetSelection | null>(null);

  const event = useQuery({ queryKey: ["event", eventId], queryFn: () => fetchEvent(eventId), refetchInterval: 30_000 });
  const live = useQuery({
    queryKey: ["event-live", eventId],
    queryFn: () => fetchLiveData(eventId),
    enabled: event.data?.status === "live",
    refetchInterval: 10_000,
  });

  if (event.isLoading) {
    return <div className="h-64 animate-pulse border border-ex-line bg-white" />;
  }
  if (event.isError || !event.data) return <ErrorState onRetry={() => event.refetch()} />;

  const e: EventDetail = event.data;
  const score = (live.data?.score ?? e.score ?? {}) as Record<string, number>;
  const isLive = (live.data?.status ?? e.status) === "live";
  const bookmakers = e.bookmakers ?? [];

  function select(runner: Runner) {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    setSelection({
      eventId: e.id,
      eventName: e.name,
      bookmakerKey: runner.bookmakerKey,
      bookmakerTitle: runner.bookmakerTitle,
      outcomeName: runner.name,
      price: runner.price,
    });
  }

  return (
    <div className="grid gap-2 xl:grid-cols-[1fr_320px]">
      <div className="min-w-0">
        <div className="mb-2 border border-ex-line bg-white">
          <div className="flex items-center justify-between gap-2 bg-ex-brand px-3 py-2 text-white">
            <h1 className="truncate text-[13px] font-bold uppercase sm:text-[15px]">{e.name}</h1>
            <span className="shrink-0 text-[12px]">
              {isLive ? (
                <span className="rounded-sm bg-yellow-400 px-2 py-0.5 font-bold text-slate-900">IN-PLAY</span>
              ) : (
                formatDateTime(e.start_time)
              )}
            </span>
          </div>
          <div className="grid grid-cols-2 divide-x divide-ex-line">
            {e.participants.map((p) => (
              <div key={p} className="flex items-center justify-between gap-2 px-3 py-2">
                <span className="truncate text-[13px] font-semibold text-slate-800">{p}</span>
                <span className="text-lg font-bold text-ex-brand">{isLive ? score[p] ?? 0 : "-"}</span>
              </div>
            ))}
          </div>
        </div>

        {bookmakers.length === 0 ? (
          <p className="border border-ex-line bg-white px-3 py-10 text-center text-sm text-slate-500">
            No prices published for this event yet.
          </p>
        ) : (
          <div className="grid gap-2 lg:grid-cols-2">
            <MarketBox
              title="Match Odds"
              runners={bestRunners(bookmakers)}
              suspended={isLive}
              selected={selection?.outcomeName}
              onSelect={select}
            />
            {/* one book only: its prices are the "Match Odds" box, so don't repeat it */}
            {(bookmakers.length > 1 ? bookmakers : []).map((b) => (
              <MarketBox
                key={b.key}
                title={`Bookmaker · ${b.title}`}
                runners={bookmakerRunners(b)}
                suspended={isLive}
                selected={selection?.outcomeName}
                onSelect={select}
              />
            ))}
          </div>
        )}
      </div>

      <aside className="space-y-2">
        {selection && (
          <BetSlip
            selection={selection}
            onClose={() => setSelection(null)}
            // desktop: right rail. mobile: sheet above the bottom nav.
            className="fixed inset-x-0 bottom-14 z-50 xl:static xl:bottom-auto"
          />
        )}
        <MyBets eventId={e.id} />
      </aside>
    </div>
  );
}
