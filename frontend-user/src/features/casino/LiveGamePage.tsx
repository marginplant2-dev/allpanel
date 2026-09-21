import { useEffect, useState } from "react";
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
import { useAuthStore } from "@/store/auth";
import { cn, formatCredits } from "@/lib/utils";

const QUICK_STAKES = [100, 500, 1000, 2000, 5000, 10000];

/** "KCC" -> K♣ ; the feed writes rank + suit letter twice. */
function cardFace(card: string): { rank: string; suit: string; red: boolean } {
  const suitChar = card.slice(-2, -1).toUpperCase();
  const rank = card.slice(0, -2) || card;
  const suit = { S: "♠", H: "♥", D: "♦", C: "♣" }[suitChar] ?? "";
  return { rank, suit, red: suitChar === "H" || suitChar === "D" };
}

function Card({ card }: { card: string }) {
  const { rank, suit, red } = cardFace(card);
  return (
    <span className="grid h-12 w-9 place-items-center rounded-sm border border-ex-line bg-white leading-none shadow-sm">
      <span className={cn("text-[13px] font-bold", red ? "text-red-600" : "text-slate-900")}>{rank}</span>
      <span className={cn("text-[13px]", red ? "text-red-600" : "text-slate-900")}>{suit}</span>
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
    // the countdown and the cards move every second or two
    refetchInterval: 2000,
  });
  const bets = useQuery({
    queryKey: ["casino-bets", code],
    queryFn: () => fetchMyCasinoBets(code),
    enabled: isAuthenticated,
    refetchInterval: 5000,
  });

  const t = table.data as CasinoTable | undefined;

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

  const groups = [...new Set(t.options.map((o) => o.group || "Main"))];
  const stakeNum = Number(stake) || 0;

  return (
    <div className="grid gap-2 xl:grid-cols-[1fr_320px]">
      <div className="min-w-0">
        <Link to="/casino" className="mb-2 inline-flex items-center gap-1 text-[13px] text-slate-600 hover:text-ex-brand">
          <ArrowLeft className="h-4 w-4" /> Back to casino
        </Link>

        <div className="border border-ex-line bg-white">
          <div className="flex items-center justify-between gap-2 bg-ex-brand px-3 py-2 text-white">
            <h1 className="truncate text-[15px] font-bold uppercase">{t.name}</h1>
            <span className="shrink-0 text-[12px]">
              {t.live ? `Round ${t.round_id.slice(-6)}` : "Table closed"}
            </span>
          </div>

          {t.live ? (
            <div className="flex flex-wrap items-center gap-3 border-b border-ex-line bg-slate-800 px-3 py-2 text-white">
              <span
                className={cn(
                  "grid h-12 w-12 place-items-center rounded-full text-[18px] font-bold",
                  t.betting_open ? "bg-green-600" : "bg-red-600",
                )}
              >
                {t.timer}
              </span>
              <span className="text-[12px] text-white/80">
                {t.betting_open ? "Betting open" : "Dealing — bets closed"}
              </span>
              {t.cards.length > 0 && (
                <span className="ml-auto flex items-center gap-1">
                  {t.cards.map((c, i) => (
                    <Card key={`${c}-${i}`} card={c} />
                  ))}
                </span>
              )}
            </div>
          ) : (
            <p className="px-3 py-10 text-center text-sm text-slate-500">
              This table is not running right now. It opens on its own schedule — try another game.
            </p>
          )}

          {t.remark && <p className="border-b border-ex-line bg-yellow-50 px-3 py-1.5 text-[12px] text-slate-700">{t.remark}</p>}

          {groups.map((group) => (
            <section key={group}>
              <h2 className="bg-ex-nav px-3 py-1.5 text-[12px] font-bold uppercase text-white">{group}</h2>
              <div className="grid gap-1 p-1 sm:grid-cols-2 lg:grid-cols-3">
                {t.options
                  .filter((o) => (o.group || "Main") === group)
                  .map((o) => (
                    <button
                      key={String(o.sid)}
                      type="button"
                      onClick={() => choose(o)}
                      disabled={!o.open || !t.betting_open}
                      className={cn(
                        "relative flex items-center justify-between gap-2 border border-ex-line px-3 py-2 text-left",
                        o.open && t.betting_open
                          ? "bg-ex-back hover:brightness-105"
                          : "bg-slate-200 text-slate-500",
                        String(selected?.sid) === String(o.sid) && "ring-2 ring-inset ring-ex-brand",
                      )}
                    >
                      <span className="min-w-0">
                        <span className="block truncate text-[13px] font-semibold text-slate-900">{o.name}</span>
                        <span className="block text-[10px] text-slate-600">
                          Min {formatCredits(o.min_stake)} · Max {formatCredits(o.max_stake)}
                        </span>
                      </span>
                      <span className="shrink-0 text-[15px] font-bold text-slate-900">
                        {o.price ? o.price.toFixed(2) : "-"}
                      </span>
                      {!o.open && (
                        <span className="absolute inset-0 grid place-items-center bg-ex-suspend/85 text-[11px] font-bold uppercase text-white">
                          {o.status}
                        </span>
                      )}
                    </button>
                  ))}
              </div>
            </section>
          ))}

          {t.results.length > 0 && (
            <section>
              <h2 className="bg-ex-nav px-3 py-1.5 text-[12px] font-bold uppercase text-white">Last Results</h2>
              <div className="flex flex-wrap gap-1.5 p-2">
                {t.results.map((r) => (
                  <span
                    key={r.round_id}
                    title={`Round ${r.round_id}`}
                    className="grid h-8 w-8 place-items-center rounded-full bg-ex-brand text-[12px] font-bold text-white"
                  >
                    {r.winners.join("/") || "-"}
                  </span>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>

      <aside className="space-y-2">
        {selected && (
          <section className="border border-ex-line bg-white">
            <h2 className="bg-ex-nav px-3 py-1.5 text-[13px] font-bold text-white">Place Bet</h2>
            <div className="bg-ex-back3 px-3 py-2">
              <div className="flex items-center justify-between text-[13px] font-bold text-slate-900">
                <span className="truncate">{selected.name}</span>
                <span>{selected.price.toFixed(2)}</span>
              </div>
              <input
                type="number"
                inputMode="numeric"
                value={stake}
                onChange={(e) => setStake(e.target.value)}
                placeholder="Amount"
                aria-label="Stake"
                autoFocus
                className="mt-2 h-9 w-full rounded-sm border border-ex-line px-2 text-[13px] font-bold"
              />
              <div className="mt-1 grid grid-cols-3 gap-1">
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
              <p className="mt-1 text-[11px] text-slate-600">
                Returns {formatCredits(Math.round(stakeNum * selected.price))} if it wins
              </p>
            </div>
            {error && <p className="px-3 py-1 text-[12px] text-red-600">{error.message}</p>}
            <div className="grid grid-cols-2 gap-1 border-t border-ex-line p-1">
              <button
                type="button"
                onClick={() => {
                  setSelected(null);
                  setStake("");
                }}
                className="bg-red-600 py-2 text-[13px] font-bold text-white hover:bg-red-700"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={stakeNum < selected.min_stake || place.isPending || !t.betting_open}
                onClick={() => place.mutate()}
                className="bg-emerald-600 py-2 text-[13px] font-bold text-white hover:bg-emerald-700 disabled:bg-slate-300"
              >
                {place.isPending ? "Placing…" : "Place Bet"}
              </button>
            </div>
          </section>
        )}

        <section className="border border-ex-line bg-white">
          <h2 className="bg-ex-nav px-3 py-1.5 text-[13px] font-bold text-white">My Bets</h2>
          {!isAuthenticated ? (
            <p className="px-3 py-5 text-center text-[12px] text-slate-500">Log in to place a bet.</p>
          ) : (bets.data?.items ?? []).length === 0 ? (
            <p className="px-3 py-5 text-center text-[12px] text-slate-500">No bets on this table yet.</p>
          ) : (
            bets.data!.items.map((b) => (
              <div key={b.id} className="border-b border-ex-line px-3 py-2 text-[12px]">
                <div className="flex justify-between font-semibold text-slate-800">
                  <span className="truncate">{b.selection}</span>
                  <span>{b.price.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Stake {formatCredits(b.stake)}</span>
                  <span
                    className={cn(
                      "font-bold",
                      b.status === "WON" && "text-green-700",
                      b.status === "LOST" && "text-red-600",
                      b.status === "PENDING" && "text-slate-500",
                    )}
                  >
                    {b.status === "PENDING" ? "Pending" : `${b.status} ${formatCredits(b.payout ?? 0)}`}
                  </span>
                </div>
              </div>
            ))
          )}
        </section>
      </aside>
    </div>
  );
}
