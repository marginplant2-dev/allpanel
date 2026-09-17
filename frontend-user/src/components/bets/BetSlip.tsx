import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import { placeBet } from "@/api/bets";
import type { ApiError } from "@/api/client";
import { cn, formatCredits } from "@/lib/utils";

export interface BetSelection {
  eventId: string;
  eventName: string;
  bookmakerKey: string;
  bookmakerTitle: string;
  outcomeName: string;
  price: number;
}

const QUICK_AMOUNTS = [1000, 2000, 5000, 10000, 20000, 25000, 50000, 75000, 90000, 95000];
const MIN_STAKE = 100;
const MAX_STAKE = 50000;

function quickLabel(v: number) {
  return `+${v / 1000}k`;
}

/**
 * Exchange bet slip. Sits in the right rail on desktop and as a bottom sheet on
 * mobile — the parent supplies the positioning, this only owns the form.
 *
 * The odds box is read-only: the server re-reads the live price at placement and
 * locks that onto the bet, so an editable field would promise a price the API
 * ignores.
 */
export function BetSlip({
  selection,
  onClose,
  className,
}: {
  selection: BetSelection;
  onClose: () => void;
  className?: string;
}) {
  const queryClient = useQueryClient();
  const [stake, setStake] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      placeBet({
        event_id: selection.eventId,
        bookmaker_key: selection.bookmakerKey,
        outcome_name: selection.outcomeName,
        stake: Number(stake),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      queryClient.invalidateQueries({ queryKey: ["bets"] });
      setStake("");
    },
  });

  const stakeNum = Number(stake) || 0;
  const profit = stakeNum > 0 ? stakeNum * (selection.price - 1) : 0;
  const tooSmall = stakeNum > 0 && stakeNum < MIN_STAKE;
  const tooBig = stakeNum > MAX_STAKE;
  const canSubmit = stakeNum >= MIN_STAKE && !tooBig && !mutation.isPending;
  const error = mutation.error as ApiError | null;

  return (
    <section className={cn("border border-ex-line bg-white shadow-lg lg:shadow-none", className)}>
      <div className="flex items-center justify-between bg-ex-nav px-3 py-1.5">
        <h2 className="text-[13px] font-bold text-white">Place Bet</h2>
        <button type="button" onClick={onClose} aria-label="Close bet slip" className="text-white/80 hover:text-white">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="grid grid-cols-[1fr_60px_72px_56px] sm:grid-cols-[1fr_74px_84px_64px] items-center border-b border-ex-line bg-ex-head px-2 py-1 text-[11px] font-bold text-slate-600">
        <span>(Bet for)</span>
        <span className="text-center">Odds</span>
        <span className="text-center">Stake</span>
        <span className="text-right">Profit</span>
      </div>

      <div className="grid grid-cols-[1fr_60px_72px_56px] sm:grid-cols-[1fr_74px_84px_64px] items-center gap-1 bg-ex-back3 px-2 py-2">
        <span className="pr-1 text-[12px] font-bold leading-tight text-slate-800">{selection.outcomeName}</span>
        <span className="grid h-8 place-items-center rounded-sm border border-ex-line bg-white text-[13px] font-bold text-slate-900">
          {selection.price.toFixed(2)}
        </span>
        <input
          type="number"
          inputMode="numeric"
          min={MIN_STAKE}
          max={MAX_STAKE}
          value={stake}
          onChange={(e) => setStake(e.target.value)}
          aria-label="Stake"
          autoFocus
          className="h-8 w-full rounded-sm border border-ex-line px-2 text-[13px] font-bold text-slate-900 focus:outline-none focus:ring-1 focus:ring-ex-brand"
        />
        <span className="text-right text-[13px] font-bold text-slate-900">{formatCredits(Math.round(profit))}</span>
      </div>

      <div className="grid grid-cols-5 gap-1 bg-ex-back3 px-2 pb-1">
        {QUICK_AMOUNTS.map((v) => (
          <button
            key={v}
            type="button"
            onClick={() => setStake((s) => String(Math.min((Number(s) || 0) + v, MAX_STAKE)))}
            className="border border-ex-line bg-white py-1.5 text-[11px] font-bold text-slate-700 hover:bg-ex-back2"
          >
            {quickLabel(v)}
          </button>
        ))}
      </div>

      <div className="bg-ex-back3 px-2 pb-2 text-right">
        <button type="button" onClick={() => setStake("")} className="text-[12px] text-ex-brand hover:underline">
          clear
        </button>
      </div>

      <div className="px-2 pb-2 text-[11px]">
        <p className="text-slate-500">
          Min {formatCredits(MIN_STAKE)} · Max {formatCredits(MAX_STAKE)} · {selection.bookmakerTitle}
        </p>
        {tooSmall && <p className="text-red-600">Minimum stake is {formatCredits(MIN_STAKE)}.</p>}
        {tooBig && <p className="text-red-600">Maximum stake is {formatCredits(MAX_STAKE)}.</p>}
        {error && <p className="text-red-600">{error.message}</p>}
        {mutation.isSuccess && <p className="font-bold text-green-700">Bet placed — stake moved to exposure.</p>}
      </div>

      <div className="grid grid-cols-2 gap-1 border-t border-ex-line p-1">
        <button
          type="button"
          onClick={() => {
            setStake("");
            mutation.reset();
          }}
          className="bg-red-600 py-2 text-[13px] font-bold text-white hover:bg-red-700"
        >
          Reset
        </button>
        <button
          type="button"
          disabled={!canSubmit}
          onClick={() => mutation.mutate()}
          className="bg-emerald-600 py-2 text-[13px] font-bold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {mutation.isPending ? "Submitting…" : "Submit"}
        </button>
      </div>
    </section>
  );
}
