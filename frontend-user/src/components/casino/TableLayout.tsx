import type { CasinoOption } from "@/api/casinoLive";
import { cn, formatCredits } from "@/lib/utils";

/**
 * Lay a casino table out the way the books do, driven by the selection names the
 * feed sends — no per-game hard-coding.
 *
 *   "Dragon A" … "Dragon K"   -> the card grid under DRAGON
 *   "Black D" / "Odd D"       -> the side-bet chips under that side
 *   "Winner D", "Player A"    -> the big buttons at the top
 *
 * A table we have never seen before still renders: anything unrecognised simply
 * lands in the main row.
 */
const RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];
const SIDE_WORDS = /^(odd|even|red|black)$/i;
/** "Under 7" ends in a rank and "Black B" starts with a colour, so both look like
 *  members of a group of one. A block only earns its own section once enough
 *  selections share the name; anything smaller belongs in the main row. */
const MIN_BLOCK = 4;

/** A colour per side block, so the sections of a table don't read as one flat sheet. */
const SIDE_TONES = [
  "from-indigo-700 to-indigo-500",
  "from-rose-700 to-rose-500",
  "from-emerald-700 to-emerald-500",
  "from-amber-600 to-amber-400",
  "from-sky-700 to-sky-500",
  "from-fuchsia-700 to-fuchsia-500",
];

export interface Classified {
  main: CasinoOption[];
  sides: { name: string; chips: CasinoOption[]; cards: CasinoOption[] }[];
}

export function classifyOptions(options: CasinoOption[]): Classified {
  const main: CasinoOption[] = [];
  const sides = new Map<string, { chips: CasinoOption[]; cards: CasinoOption[] }>();

  const bucket = (name: string) => {
    if (!sides.has(name)) sides.set(name, { chips: [], cards: [] });
    return sides.get(name)!;
  };

  for (const option of options) {
    const words = (option.name ?? "").trim().split(/\s+/);
    const last = words[words.length - 1] ?? "";
    const rest = words.slice(0, -1).join(" ");

    if (words.length > 1 && RANKS.includes(last.toUpperCase())) {
      bucket(rest).cards.push(option);
    } else if (words.length > 1 && SIDE_WORDS.test(words[0])) {
      // "Black D" -> side D, chip Black
      bucket(words.slice(1).join(" ")).chips.push(option);
    } else if (words.length > 1 && SIDE_WORDS.test(last)) {
      // "D Black" -> side D, chip Black
      bucket(rest).chips.push(option);
    } else {
      main.push(option);
    }
  }

  const kept: { name: string; chips: CasinoOption[]; cards: CasinoOption[] }[] = [];
  for (const [name, v] of sides) {
    if (v.chips.length + v.cards.length < MIN_BLOCK) main.push(...v.chips, ...v.cards);
    else kept.push({ name, ...v });
  }

  return { main: main.sort((a, b) => a.sort - b.sort), sides: kept };
}

function shortLabel(option: CasinoOption, side: string): string {
  const name = option.name ?? "";
  if (!side) return name;
  // "Dragon A" inside the DRAGON block reads better as just "A" — but only the whole
  // word comes off, or "Black B" would come back as "lack".
  const word = side.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return name.replace(new RegExp(`^${word}\\s+|\\s+${word}$`, "i"), "").trim() || name;
}

function Lock() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </svg>
  );
}

function cellState(option: CasinoOption, bettingOpen: boolean) {
  const open = option.open && bettingOpen;
  return {
    open,
    className: open
      ? "bg-gradient-to-b from-ex-back2 to-ex-back hover:brightness-105 cursor-pointer"
      : "bg-slate-300/80 text-slate-500 cursor-not-allowed",
  };
}

/** Big buttons: the headline selections of the table. */
export function MainBets({
  options,
  bettingOpen,
  selectedSid,
  onSelect,
}: {
  options: CasinoOption[];
  bettingOpen: boolean;
  selectedSid?: string;
  onSelect: (o: CasinoOption) => void;
}) {
  if (options.length === 0) return null;
  return (
    <div className="grid grid-cols-2 gap-1 p-1 lg:grid-cols-4">
      {options.map((o) => {
        const state = cellState(o, bettingOpen);
        return (
          <button
            key={String(o.sid)}
            type="button"
            disabled={!state.open}
            onClick={() => onSelect(o)}
            className={cn(
              "relative flex min-h-[64px] flex-col items-center justify-center gap-0.5 rounded-md border border-ex-line px-2 py-2 shadow-sm",
              state.className,
              selectedSid === String(o.sid) && "ring-2 ring-inset ring-ex-brand",
            )}
          >
            <span className="text-center text-[12px] font-bold uppercase leading-tight text-slate-900 sm:text-[13px]">
              {o.name}
            </span>
            <span className="text-[15px] font-bold text-slate-900">{o.price.toFixed(2)}</span>
            <span className="text-[10px] text-slate-600">
              {formatCredits(o.min_stake)} – {formatCredits(o.max_stake)}
            </span>
            {!state.open && (
              <span className="absolute inset-0 grid place-items-center bg-slate-500/25 text-slate-700">
                <Lock />
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/** One side of the table: its odd/even/colour chips and its card grid. */
export function SideBlock({
  side,
  index = 0,
  bettingOpen,
  selectedSid,
  onSelect,
}: {
  side: { name: string; chips: CasinoOption[]; cards: CasinoOption[] };
  index?: number;
  bettingOpen: boolean;
  selectedSid?: string;
  onSelect: (o: CasinoOption) => void;
}) {
  return (
    <section className="overflow-hidden rounded-md border border-ex-line">
      <h3
        className={cn(
          "bg-gradient-to-r px-3 py-1.5 text-center text-[13px] font-bold uppercase text-white",
          SIDE_TONES[index % SIDE_TONES.length],
        )}
      >
        {side.name}
      </h3>

      {side.chips.length > 0 && (
        <div className="grid grid-cols-2 gap-1 p-1 sm:grid-cols-4">
          {side.chips.map((o) => {
            const state = cellState(o, bettingOpen);
            return (
              <button
                key={String(o.sid)}
                type="button"
                disabled={!state.open}
                onClick={() => onSelect(o)}
                className={cn(
                  "relative flex flex-col items-center justify-center border border-ex-line py-2",
                  state.className,
                  selectedSid === String(o.sid) && "ring-2 ring-inset ring-ex-brand",
                )}
              >
                <span className="text-[12px] font-bold text-slate-900">{shortLabel(o, side.name)}</span>
                <span className="text-[13px] font-bold text-slate-900">{o.price.toFixed(2)}</span>
                {!state.open && (
                  <span className="absolute inset-0 grid place-items-center bg-slate-500/25 text-slate-700">
                    <Lock />
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {side.cards.length > 0 && (
        <div className="flex flex-wrap gap-1 p-1">
          {side.cards.map((o) => {
            const state = cellState(o, bettingOpen);
            return (
              <button
                key={String(o.sid)}
                type="button"
                disabled={!state.open}
                onClick={() => onSelect(o)}
                title={`${o.name} @ ${o.price.toFixed(2)}`}
                className={cn(
                  "relative grid h-12 w-10 place-items-center rounded-sm border border-ex-line",
                  state.open ? "bg-white hover:bg-ex-back3 cursor-pointer" : "bg-slate-300/80 cursor-not-allowed",
                  selectedSid === String(o.sid) && "ring-2 ring-inset ring-ex-brand",
                )}
              >
                <span className="text-[14px] font-bold text-slate-900">{shortLabel(o, side.name)}</span>
                <span className="text-[9px] text-slate-600">{o.price.toFixed(2)}</span>
                {!state.open && (
                  <span className="absolute inset-0 grid place-items-center bg-slate-500/25 text-slate-700">
                    <Lock />
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
