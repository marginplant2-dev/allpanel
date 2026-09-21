import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import {
  fetchCasinoTable,
  fetchMyCasinoBets,
  placeCasinoBet,
  type CasinoOption,
  type CasinoTable,
} from "@/api/casinoLive";
import type { ApiError } from "@/api/client";
import { ErrorState } from "@/components/common/States";
import { MainBets, SideBlock, classifyOptions } from "@/components/casino/TableLayout";
import { useAuthStore } from "@/store/auth";
import { cn, formatCredits } from "@/lib/utils";

const QUICK_STAKES = [100, 500, 1000, 2000, 5000, 10000];

/** Result badges read at a glance: one colour per selection. */
const RESULT_TONES = ["bg-red-600", "bg-blue-600", "bg-green-600", "bg-amber-500", "bg-purple-600", "bg-slate-600"];

function initials(name: string): string {
  const words = name.replace(/[^A-Za-z0-9 ]/g, " ").split(/\s+/).filter(Boolean);
  if (words.length === 0) return "?";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[words.length - 1][0]).toUpperCase();
}

/** "KCC" -> K♣ ; the feed writes the suit letter twice. */
function cardFace(card: string): { rank: string; suit: string; red: boolean } {
  const suitChar = card.slice(-2, -1).toUpperCase();
  const rank = card.slice(0, -2) || card;
  const suit = { S: "♠", H: "♥", D: "♦", C: "♣" }[suitChar] ?? "";
  return { rank, suit, red: suitChar === "H" || suitChar === "D" };
}

function DealtCard({ card }: { card: string }) {
  const { rank, suit, red } = cardFace(card);
  return (
    <span className="grid h-14 w-10 place-items-center rounded-sm border border-slate-300 bg-white leading-none shadow">
      <span className={cn("text-[15px] font-bold", red ? "text-red-600" : "text-slate-900")}>{rank}</span>
      <span className={cn("text-[15px]", red ? "text-red-600" : "text-slate-900")}>{suit}</span>
    </span>
  );
}

export default function LiveGamePage() {
  const { code = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [selected, setSelected] = useState<CasinoOption | null>(null);
  const [stake, setStake] = useState("");

  const table = useQuery({
    queryKey: ["casino-table", code],
    queryFn: () => fetchCasinoTable(code),
    refetchInterval: 2000, // the countdown and the cards move every second or two
  });
  const bets = useQuery({
    queryKey: ["casino-bets", code],
    queryFn: () => fetchMyCasinoBets(code),
    enabled: isAuthenticated,
    refetchInterval: 5000,
  });

  const t = table.data as CasinoTable | undefined;
  const layout = useMemo(() => classifyOptions(t?.options ?? []), [t?.options]);

  // A selection belongs to one round; when the round turns over, drop the slip.
  useEffect(() => {
    setSelected(null);
  }, [t?.round_id]);

  const place = useMutation({
    mutationFn: () =>
      placeCasinoBet({
        code: t!.code,
        round_id: t!.round_id,
        sid: String(selected!.sid),
        stake: Number(stake),
      }),
    onSuccess: () => {
      setSelected(null);
      setStake("");
      queryClient.invalidateQueries({ queryKey: ["wallet"] });
      queryClient.invalidateQueries({ queryKey: ["casino-bets", code] });
    },
  });
  const error = place.error as ApiError | null;

  if (table.isError) return <ErrorState onRetry={() => table.refetch()} />;
  if (!t) return <div className="h-64 animate-pulse border border-ex-line bg-white" />;

  function choose(option: CasinoOption) {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    if (!option.open || !t!.betting_open) return;
    setSelected(option);
    place.reset();
  }

  const stakeNum = Number(stake) || 0;
  const profit = selected ? stakeNum * (selected.price - 1) : 0;

  return (
    <div className="grid gap-2 xl:grid-cols-[1fr_320px]">
      <div className="min-w-0">
        <Link to="/casino" className="mb-2 inline-flex items-center gap-1 text-[13px] text-slate-600 hover:text-ex-brand">
          <ArrowLeft className="h-4 w-4" /> Back to casino
        </Link>

        <div className="border border-ex-line bg-white">
          <div className="flex items-center justify-between gap-2 bg-ex-brand px-3 py-2 text-white">
            <span className="flex min-w-0 items-center gap-2">
              <img
                src={`/casino-art/${t.code}.webp`}
                alt=""
                aria-hidden
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
                className="hidden h-8 w-5 rounded-sm object-cover sm:block"
              />
              <h1 className="truncate text-[15px] font-bold uppercase">{t.name}</h1>
            </span>
            <span className="shrink-0 text-[12px]">
              {t.live ? `Round ID: ${t.round_id}` : "Table closed"}
            </span>
          </div>

          {t.live ? (
            <div className="relative flex min-h-[96px] items-center gap-3 bg-slate-900 px-3 py-3">
              {t.cards.length > 0 ? (
                <span className="flex flex-wrap items-center gap-1.5">
                  {t.cards.map((c, i) => (
                    <DealtCard key={`${c}-${i}`} card={c} />
                  ))}
                </span>
              ) : (
                <span className="text-[13px] text-white/60">Waiting for the deal…</span>
              )}

              <span className="ml-auto flex flex-col items-center">
                <span
                  className={cn(
                    "grid h-16 w-16 place-items-center rounded-lg text-[26px] font-bold text-white",
                    t.betting_open ? "bg-green-600" : "bg-red-600",
                  )}
                >
                  {t.timer}
                </span>
                <span className="mt-1 text-[11px] font-semibold uppercase text-white/80">
                  {t.betting_open ? "Betting open" : "Bets closed"}
                </span>
              </span>
            </div>
          ) : (
            <div className="px-3 py-8 text-center">
              <p className="text-sm font-semibold text-slate-700">This table is not dealing right now.</p>
              <p className="mt-1 text-[13px] text-slate-500">
                The feed marks it closed — these tables open on their own schedule. Its last rounds are below.
              </p>
              <Link
                to="/casino"
                className="mt-3 inline-block bg-ex-brand px-4 py-2 text-[13px] font-bold text-white hover:bg-ex-nav"
              >
                Pick a table that is running
              </Link>
            </div>
          )}

          {t.remark && (
            <p className="border-b border-ex-line bg-yellow-50 px-3 py-1.5 text-[12px] text-slate-700">{t.remark}</p>
          )}

          <MainBets
            options={layout.main}
            bettingOpen={t.betting_open}
            selectedSid={selected ? String(selected.sid) : undefined}
            onSelect={choose}
          />

          {layout.sides.length > 0 && (
            <div className="grid gap-1 p-1 lg:grid-cols-2">
              {layout.sides.map((side) => (
                <SideBlock
                  key={side.name}
                  side={side}
                  bettingOpen={t.betting_open}
                  selectedSid={selected ? String(selected.sid) : undefined}
                  onSelect={choose}
                />
              ))}
            </div>
          )}

          {t.results.length > 0 && (
            <section>
              <h2 className="bg-ex-nav px-3 py-1.5 text-[12px] font-bold uppercase text-white">Last Results</h2>
              <div className="flex flex-wrap items-center gap-2 p-2">
                {t.results.map((r) => {
                  const name = r.winner_names?.[0] || r.winners[0] || "-";
                  const tone = RESULT_TONES[Number(r.winners[0] ?? 0) % RESULT_TONES.length];
                  return (
                    <span
                      key={r.round_id}
                      title={`Round ${r.round_id} — ${r.winner_names?.join(", ") || name}`}
                      className={cn(
                        "grid h-8 w-8 place-items-center rounded-full text-[11px] font-bold text-white",
                        tone,
                      )}
                    >
                      {initials(name)}
                    </span>
                  );
                })}
              </div>
            </section>
          )}
        </div>
      </div>

      <aside className="space-y-2">
        {selected && (
          <section className="fixed inset-x-0 bottom-14 z-50 border border-ex-line bg-white shadow-lg xl:static xl:bottom-auto xl:shadow-none">
            <div className="flex items-center justify-between bg-ex-nav px-3 py-1.5">
              <h2 className="text-[13px] font-bold text-white">Place Bet</h2>
              <span className="text-[11px] text-white/70">
                Range: {formatCredits(selected.min_stake)} – {formatCredits(selected.max_stake)}
              </span>
            </div>

            <div className="grid grid-cols-[1fr_60px_72px_56px] items-center border-b border-ex-line bg-ex-head px-2 py-1 text-[11px] font-bold text-slate-600 sm:grid-cols-[1fr_74px_84px_64px]">
              <span>(Bet for)</span>
              <span className="text-center">Odds</span>
              <span className="text-center">Stake</span>
              <span className="text-right">Profit</span>
            </div>
            <div className="grid grid-cols-[1fr_60px_72px_56px] items-center gap-1 bg-ex-back3 px-2 py-2 sm:grid-cols-[1fr_74px_84px_64px]">
              <span className="pr-1 text-[12px] font-bold leading-tight text-slate-800">{selected.name}</span>
              <span className="grid h-8 place-items-center rounded-sm border border-ex-line bg-white text-[13px] font-bold text-slate-900">
                {selected.price.toFixed(2)}
              </span>
              <input
                type="number"
                inputMode="numeric"
                value={stake}
                onChange={(e) => setStake(e.target.value)}
                aria-label="Stake"
                autoFocus
                className="h-8 w-full rounded-sm border border-ex-line px-2 text-[13px] font-bold text-slate-900 focus:outline-none focus:ring-1 focus:ring-ex-brand"
              />
              <span className="text-right text-[13px] font-bold text-slate-900">
                {formatCredits(Math.round(profit))}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-1 bg-ex-back3 px-2 pb-1">
              {QUICK_STAKES.map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setStake((s) => String((Number(s) || 0) + v))}
                  className="border border-ex-line bg-white py-1.5 text-[11px] font-bold text-slate-700 hover:bg-ex-back2"
                >
                  +{v >= 1000 ? `${v / 1000}k` : v}
                </button>
              ))}
            </div>
            <div className="bg-ex-back3 px-2 pb-2 text-right">
              <button type="button" onClick={() => setStake("")} className="text-[12px] text-ex-brand hover:underline">
                clear
              </button>
            </div>

            {error && <p className="px-2 pb-1 text-[12px] text-red-600">{error.message}</p>}
            {!t.betting_open && (
              <p className="px-2 pb-1 text-[12px] text-red-600">Bets are closed for this round.</p>
            )}

            <div className="grid grid-cols-2 gap-1 border-t border-ex-line p-1">
              <button
                type="button"
                onClick={() => {
                  setSelected(null);
                  setStake("");
                }}
                className="bg-red-600 py-2 text-[13px] font-bold text-white hover:bg-red-700"
              >
                Reset
              </button>
              <button
                type="button"
                disabled={stakeNum < selected.min_stake || place.isPending || !t.betting_open}
                onClick={() => place.mutate()}
                className="bg-emerald-600 py-2 text-[13px] font-bold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {place.isPending ? "Submitting…" : "Submit"}
              </button>
            </div>
          </section>
        )}

        <section className="border border-ex-line bg-white">
          <h2 className="bg-ex-nav px-3 py-1.5 text-[13px] font-bold text-white">My Bet</h2>
          <div className="grid grid-cols-[1fr_58px_70px] border-b border-ex-line bg-ex-head px-2 py-1 text-[11px] font-bold text-slate-600">
            <span>Matched Bet</span>
            <span className="text-right">Odds</span>
            <span className="text-right">Stake</span>
          </div>
          {!isAuthenticated ? (
            <p className="px-3 py-5 text-center text-[12px] text-slate-500">Log in to place a bet.</p>
          ) : (bets.data?.items ?? []).length === 0 ? (
            <p className="px-3 py-5 text-center text-[12px] text-slate-500">No bets on this table yet.</p>
          ) : (
            bets.data!.items.map((b) => (
              <div
                key={b.id}
                className={cn(
                  "grid grid-cols-[1fr_58px_70px] items-center border-b border-ex-line px-2 py-1.5 text-[12px]",
                  b.status === "WON" && "bg-green-50",
                  b.status === "LOST" && "bg-red-50",
                  b.status === "PENDING" && "bg-ex-back3",
                )}
              >
                <span className="min-w-0">
                  <span className="block truncate font-semibold text-slate-800">{b.selection}</span>
                  <span className="block text-[10px] text-slate-500">
                    {b.status === "PENDING" ? "Pending" : `${b.status} ${formatCredits(b.payout ?? 0)}`}
                  </span>
                </span>
                <span className="text-right font-bold text-slate-900">{b.price.toFixed(2)}</span>
                <span className="text-right font-bold text-slate-900">{formatCredits(b.stake)}</span>
              </div>
            ))
          )}
        </section>
      </aside>
    </div>
  );
}
