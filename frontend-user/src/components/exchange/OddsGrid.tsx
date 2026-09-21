import { Fragment } from "react";
import { Link } from "react-router-dom";
import { Monitor } from "lucide-react";
import type { EventOdds, SportEvent } from "@/types";
import type { BetSelection } from "@/components/bets/BetSlip";
import { cn } from "@/lib/utils";

/**
 * ponytail: the feed is a bookmaker h2h price, not a two-sided exchange book, so the
 * lay column is derived from the back price with a fixed spread and is display-only
 * (clicking it does nothing — the backend settles back bets only). Wire a real lay
 * side when the provider exposes one and the wallet can lock liability.
 */
const LAY_SPREAD = 0.02;

/** Long odds drop their pennies: "140" fits a phone cell, "140.00" does not. */
export function formatPrice(price: number) {
  return price >= 100 ? price.toFixed(0) : price.toFixed(2);
}

export function layPrice(price: number) {
  return Math.round(price * (1 + LAY_SPREAD) * 100) / 100;
}

/** Feed outcomes are named by team; the grid columns are 1 / X / 2. */
export function columnOdds(event: SportEvent): (EventOdds | undefined)[] {
  const by = (name?: string) => event.odds?.find((o) => o.name === name);
  const home = event.home_team ?? event.participants[0];
  const away = event.away_team ?? event.participants[1];
  return [by(home), by("Draw"), by(away)];
}

function formatStart(value: string) {
  const d = new Date(value);
  const today = new Date();
  const sameDay = d.toDateString() === today.toDateString();
  const time = d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  return sameDay ? time : `${d.toLocaleDateString("en-GB", { day: "2-digit", month: "2-digit" })} ${time}`;
}

function PriceCell({
  odds,
  side,
  onSelect,
}: {
  odds?: EventOdds;
  side: "back" | "lay";
  onSelect?: () => void;
}) {
  // a real exchange feed sends its own lay; bookmaker feeds get the derived one
  const price = odds ? (side === "back" ? odds.price : odds.lay ?? layPrice(odds.price)) : null;
  const clickable = price !== null && !!onSelect;

  return (
    <button
      type="button"
      disabled={!clickable}
      onClick={onSelect}
      title={odds ? `${odds.name} · ${odds.bookmaker_title}` : "Price not available"}
      className={cn(
        "ex-cell",
        side === "back" ? "bg-ex-back" : "bg-ex-lay",
        price === null && "text-slate-500/70",
        clickable ? "cursor-pointer hover:brightness-105 active:brightness-95" : "cursor-default",
      )}
    >
      {price === null ? "-" : formatPrice(price)}
    </button>
  );
}

export function OddsGridHeader({ title = "Game" }: { title?: string }) {
  return (
    <div className="ex-head grid grid-cols-[1fr_repeat(6,36px)] items-center border-b border-ex-line sm:grid-cols-[1fr_repeat(6,58px)]">
      <span className="px-2 py-1.5">{title}</span>
      {["1", "X", "2"].map((label) => (
        <span key={label} className="col-span-2 grid h-full place-items-center border-l border-ex-line py-1.5">
          {label}
        </span>
      ))}
    </div>
  );
}

export function OddsRow({
  event,
  onSelect,
}: {
  event: SportEvent;
  onSelect?: (selection: BetSelection) => void;
}) {
  const isLive = event.status === "live";
  const cols = columnOdds(event);
  const bookmaker = event.odds?.[0]?.bookmaker_title;

  function select(odds: EventOdds | undefined, side: "back" | "lay") {
    if (!odds || !onSelect) return;
    onSelect({
      eventId: event.id,
      eventName: event.name,
      bookmakerKey: odds.bookmaker_key,
      bookmakerTitle: odds.bookmaker_title,
      outcomeName: odds.name,
      price: side === "lay" ? odds.lay ?? layPrice(odds.price) : odds.price,
      side: side === "lay" ? "LAY" : "BACK",
    });
  }

  return (
    <div className="grid grid-cols-[1fr_repeat(6,36px)] items-center border-b border-ex-line bg-ex-row hover:bg-ex-rowalt sm:grid-cols-[1fr_repeat(6,58px)]">
      <div className="flex min-w-0 items-center gap-2 px-2 py-1.5">
        <Link
          to={`/events/${event.id}`}
          title={event.name}
          className="min-w-0 flex-1 text-[12px] leading-tight text-slate-800 hover:text-ex-brand sm:text-[13px]"
        >
          <span className="block truncate hover:underline">{event.name}</span>
          <span className="block text-[11px] text-slate-500">{formatStart(event.start_time)}</span>
        </Link>
        <span className="flex shrink-0 items-center gap-1.5 pl-1">
          {isLive && <span className="h-2.5 w-2.5 rounded-full bg-green-500 animate-blink" title="In-play" />}
          {isLive && <Monitor className="hidden h-3.5 w-3.5 text-slate-600 sm:block" />}
          {bookmaker && (
            <span className="rounded-sm bg-slate-700 px-1 text-[10px] font-bold text-white" title={bookmaker}>
              BM
            </span>
          )}
        </span>
      </div>
      {cols.map((odds, i) => (
        <Fragment key={i}>
          <PriceCell odds={odds} side="back" onSelect={() => select(odds, "back")} />
          <PriceCell odds={odds} side="lay" onSelect={() => select(odds, "lay")} />
        </Fragment>
      ))}
    </div>
  );
}

export function OddsGrid({
  events,
  isLoading,
  title,
  onSelect,
  emptyLabel = "No events available right now.",
}: {
  events?: SportEvent[];
  isLoading?: boolean;
  title?: string;
  onSelect?: (selection: BetSelection) => void;
  emptyLabel?: string;
}) {
  return (
    <div className="overflow-hidden border border-ex-line bg-ex-row">
      <OddsGridHeader title={title} />
      {isLoading ? (
        Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-9 animate-pulse border-b border-ex-line bg-ex-rowalt" />
        ))
      ) : events && events.length > 0 ? (
        events.map((e) => <OddsRow key={e.id} event={e} onSelect={onSelect} />)
      ) : (
        <p className="px-3 py-8 text-center text-sm text-slate-500">{emptyLabel}</p>
      )}
    </div>
  );
}
