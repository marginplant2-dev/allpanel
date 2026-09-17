import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchEvent, fetchLiveData } from "@/api/sports";
import type { Bookmaker, EventDetail, OddsOutcome } from "@/types";
import { ErrorState } from "@/components/common/States";
import { BetSlip, type BetSelection } from "@/components/bets/BetSlip";
import { MyBets } from "@/components/bets/MyBets";
import { FancySection, MatchOddsBoard, toSelection } from "@/components/exchange/MarketBoard";
import { ScoreStrip } from "@/components/exchange/ScoreStrip";
import { useAuthStore } from "@/store/auth";
import { formatDateTime } from "@/lib/utils";

/** Section headings, in the order the exchanges list them. */
const FANCY_TITLES: Record<string, string> = {
  normal: "Normal",
  "over by over": "Over By Over",
  overbyover: "Over By Over",
  "ball by ball": "Ball By Ball",
  ballbyball: "Ball By Ball",
  oddeven: "Odd Even",
  meter: "Meter",
  fancy1: "Fancy1",
  khadometer: "Khado Meter",
};
const FANCY_ORDER = ["Normal", "Over By Over", "Ball By Ball", "Fancy1", "Odd Even", "Meter"];

function rank(title: string) {
  const i = FANCY_ORDER.indexOf(title);
  return i < 0 ? 99 : i;
}

export default function EventDetailPage() {
  const { eventId = "" } = useParams();
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [selection, setSelection] = useState<BetSelection | null>(null);

  const event = useQuery({
    queryKey: ["event", eventId],
    queryFn: () => fetchEvent(eventId),
    // an in-play board moves constantly; this is the cadence the books run at
    refetchInterval: 5_000,
  });
  const live = useQuery({
    queryKey: ["event-live", eventId],
    queryFn: () => fetchLiveData(eventId),
    enabled: event.data?.status === "live",
    refetchInterval: 8_000,
    retry: false,
  });

  const e = event.data as EventDetail | undefined;
  const books = useMemo(() => e?.bookmakers ?? [], [e]);
  const matchBooks = useMemo(
    () => books.filter((b) => b.kind !== "fancy" && b.kind !== "other"),
    [books],
  );
  const fancyGroups = useMemo(() => {
    const groups = new Map<string, Bookmaker[]>();
    for (const b of books) {
      if (b.kind !== "fancy" && b.kind !== "other") continue;
      const title = FANCY_TITLES[(b.gtype ?? "").toLowerCase()] ?? b.gtype ?? "Fancy";
      groups.set(title, [...(groups.get(title) ?? []), b]);
    }
    return [...groups.entries()].sort((a, b) => rank(a[0]) - rank(b[0]));
  }, [books]);

  if (event.isLoading) return <div className="h-64 animate-pulse border border-ex-line bg-white" />;
  if (event.isError || !e) return <ErrorState onRetry={() => event.refetch()} />;

  const isLive = (live.data?.status ?? e.status) === "live";
  const board = live.data?.board;

  function select(outcome: OddsOutcome, book: Bookmaker, side: "BACK" | "LAY", price: number) {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    setSelection(toSelection({ id: e!.id, name: e!.name }, outcome, book, side, price));
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

          {board ? (
            <ScoreStrip board={board} />
          ) : (
            <div className="grid grid-cols-2 divide-x divide-ex-line">
              {e.participants.map((p) => (
                <div key={p} className="flex items-center justify-between gap-2 px-3 py-2">
                  <span className="truncate text-[13px] font-semibold text-slate-800">{p}</span>
                  <span className="text-lg font-bold text-ex-brand">-</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {books.length === 0 ? (
          <p className="border border-ex-line bg-white px-3 py-10 text-center text-sm text-slate-500">
            No markets open for this event right now.
          </p>
        ) : (
          <>
            {matchBooks.map((b) => (
              <MatchOddsBoard
                key={b.key}
                book={b}
                suspended={false}
                selected={selection?.outcomeName}
                onSelect={select}
              />
            ))}
            {fancyGroups.map(([title, group]) => (
              <FancySection key={title} title={title} books={group} onSelect={select} />
            ))}
          </>
        )}
      </div>

      <aside className="space-y-2">
        {selection && (
          <BetSlip
            selection={selection}
            onClose={() => setSelection(null)}
            className="fixed inset-x-0 bottom-14 z-50 xl:static xl:bottom-auto"
          />
        )}
        <MyBets eventId={e.id} />
      </aside>
    </div>
  );
}
