import { Fragment } from "react";
import type { Bookmaker, OddsOutcome, PriceLevel } from "@/types";
import type { BetSelection } from "@/components/bets/BetSlip";
import { cn } from "@/lib/utils";

/**
 * The market board an exchange shows: three back levels and three lay levels per
 * runner, each with the money available at that price.
 *
 * ponytail: only the best price (b1/l1) is clickable — the bet API prices a bet at
 * the best available, so offering the deeper rungs would promise a price it would
 * not honour. Wire per-price bets and they become clickable.
 */
function Cell({
  level,
  side,
  best,
  onSelect,
}: {
  level?: PriceLevel;
  side: "back" | "lay";
  best: boolean;
  onSelect?: () => void;
}) {
  const shade =
    side === "back"
      ? best
        ? "bg-ex-back"
        : "bg-ex-back2"
      : best
        ? "bg-ex-lay"
        : "bg-ex-lay2";
  const clickable = best && !!level?.price && !!onSelect;

  return (
    <button
      type="button"
      disabled={!clickable}
      onClick={onSelect}
      className={cn(
        "grid h-11 place-items-center border-l border-ex-line leading-none",
        shade,
        clickable ? "cursor-pointer hover:brightness-105" : "cursor-default",
      )}
    >
      <span className="text-[13px] font-bold text-slate-900">
        {level?.price ? level.price.toFixed(2) : "-"}
      </span>
      {level?.size ? <span className="text-[10px] text-slate-600">{level.size}</span> : null}
    </button>
  );
}

const ROW = "grid-cols-[1fr_repeat(6,44px)] sm:grid-cols-[1fr_repeat(6,62px)]";

export function MatchOddsBoard({
  book,
  suspended,
  selected,
  onSelect,
}: {
  book: Bookmaker;
  suspended: boolean;
  selected?: string;
  onSelect: (outcome: OddsOutcome, book: Bookmaker) => void;
}) {
  const outcomes = book.markets[0]?.outcomes ?? [];
  if (outcomes.length === 0) return null;
  const closed = suspended || book.suspended;

  return (
    <section className="mb-2 border border-ex-line bg-white">
      <div className="flex items-center justify-between gap-2 bg-ex-nav px-3 py-1.5">
        <h2 className="truncate text-[13px] font-bold uppercase text-white">{book.title}</h2>
        {!!book.max_stake && (
          <span className="shrink-0 text-[11px] text-white/70">Max: {book.max_stake}</span>
        )}
      </div>

      <div className={cn("ex-head grid items-center border-b border-ex-line", ROW)}>
        <span className="px-2 py-1.5">{book.min_stake ? `Min: ${book.min_stake}` : "Runner"}</span>
        <span className="col-span-3 grid h-full place-items-center border-l border-ex-line bg-ex-back py-1.5 text-slate-900">
          Back
        </span>
        <span className="col-span-3 grid h-full place-items-center border-l border-ex-line bg-ex-lay py-1.5 text-slate-900">
          Lay
        </span>
      </div>

      {outcomes.map((o) => (
        <div key={o.name} className={cn("relative grid items-center border-b border-ex-line", ROW)}>
          <span
            className={cn(
              "truncate px-2 py-2 text-[13px] font-semibold text-slate-800",
              selected === o.name && "text-ex-brand",
            )}
          >
            {o.name}
          </span>

          {/* deepest price first on the back side, best price nearest the middle */}
          {[2, 1, 0].map((i) => (
            <Cell
              key={`b${i}`}
              level={o.back_ladder?.[i]}
              side="back"
              best={i === 0}
              onSelect={() => onSelect(o, book)}
            />
          ))}
          {[0, 1, 2].map((i) => (
            <Cell key={`l${i}`} level={o.lay_ladder?.[i]} side="lay" best={i === 0} />
          ))}

          {(closed || o.status === "SUSPENDED") && (
            <span className="absolute inset-y-0 right-0 grid w-[264px] place-items-center bg-ex-suspend/95 text-[11px] font-bold uppercase tracking-wide text-white sm:w-[372px]">
              {o.status && o.status !== "ACTIVE" ? o.status : "Suspended"}
            </span>
          )}
        </div>
      ))}
    </section>
  );
}

const FANCY_ROW = "grid-cols-[1fr_52px_52px_56px] sm:grid-cols-[1fr_62px_62px_64px]";

/** Fancy/session markets: a No (lay) and a Yes (back) price with its own limits. */
function FancyRow({ outcome }: { outcome: OddsOutcome }) {
  const closed = !!outcome.status && outcome.status.toUpperCase() !== "ACTIVE";
  const no = outcome.lay_ladder?.[0];
  const yes = outcome.back_ladder?.[0];

  return (
    <div className={cn("relative grid items-center border-b border-ex-line", FANCY_ROW)}>
      <span className="truncate px-2 py-2 text-[13px] text-slate-800">{outcome.name}</span>
      <span className="grid h-11 place-items-center border-l border-ex-line bg-ex-lay leading-none">
        <span className="text-[13px] font-bold text-slate-900">{no?.price ?? "-"}</span>
        {no?.size ? <span className="text-[10px] text-slate-600">{no.size}</span> : null}
      </span>
      <span className="grid h-11 place-items-center border-l border-ex-line bg-ex-back leading-none">
        <span className="text-[13px] font-bold text-slate-900">{yes?.price ?? "-"}</span>
        {yes?.size ? <span className="text-[10px] text-slate-600">{yes.size}</span> : null}
      </span>
      <span className="grid h-11 place-items-center border-l border-ex-line text-[9px] leading-tight text-slate-500">
        <span>Min: {outcome.min_stake || 100}</span>
        <span>Max: {outcome.max_stake || "—"}</span>
      </span>
      {closed && (
        <span className="absolute inset-y-0 right-[56px] grid w-[104px] place-items-center bg-ex-suspend/95 text-[10px] font-bold uppercase text-white sm:right-[64px] sm:w-[124px]">
          {outcome.status}
        </span>
      )}
    </div>
  );
}

/** One titled section per fancy family (normal, over by over, ball by ball, …). */
export function FancySection({ title, books }: { title: string; books: Bookmaker[] }) {
  const rows = books.flatMap((b) => b.markets[0]?.outcomes ?? []);
  if (rows.length === 0) return null;

  return (
    <section className="mb-2 border border-ex-line bg-white">
      <h2 className="bg-ex-nav px-3 py-1.5 text-[13px] font-bold uppercase text-white">{title}</h2>
      <div className="grid lg:grid-cols-2">
        {/* two columns on desktop, exactly as the books lay these out */}
        <div>
          <div className={cn("ex-head grid items-center border-b border-ex-line", FANCY_ROW)}>
            <span className="px-2 py-1.5" />
            <span className="grid place-items-center border-l border-ex-line bg-ex-lay py-1.5 text-slate-900">No</span>
            <span className="grid place-items-center border-l border-ex-line bg-ex-back py-1.5 text-slate-900">Yes</span>
            <span className="border-l border-ex-line" />
          </div>
          {rows.filter((_, i) => i % 2 === 0).map((o) => (
            <FancyRow key={o.name} outcome={o} />
          ))}
        </div>
        <div className="border-t border-ex-line lg:border-l lg:border-t-0">
          <div className={cn("ex-head grid items-center border-b border-ex-line", FANCY_ROW)}>
            <span className="px-2 py-1.5" />
            <span className="grid place-items-center border-l border-ex-line bg-ex-lay py-1.5 text-slate-900">No</span>
            <span className="grid place-items-center border-l border-ex-line bg-ex-back py-1.5 text-slate-900">Yes</span>
            <span className="border-l border-ex-line" />
          </div>
          {rows.filter((_, i) => i % 2 === 1).map((o) => (
            <FancyRow key={o.name} outcome={o} />
          ))}
        </div>
      </div>
    </section>
  );
}

export function toSelection(
  event: { id: string; name: string },
  outcome: OddsOutcome,
  book: Bookmaker,
): BetSelection {
  return {
    eventId: event.id,
    eventName: event.name,
    bookmakerKey: book.key,
    bookmakerTitle: book.title,
    outcomeName: outcome.name,
    price: outcome.price,
  };
}

export { Fragment };
