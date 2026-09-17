import type { LiveBoard } from "@/types";
import { cn } from "@/lib/utils";

/** Colour for a ball in the last-six strip: wickets red, boundaries green. */
function ballTone(ball: string) {
  const b = ball.toUpperCase();
  if (b.includes("W") && !b.includes("WB")) return "bg-red-600 text-white";
  if (b === "4" || b === "6") return "bg-green-600 text-white";
  if (b === "0") return "bg-slate-200 text-slate-700";
  return "bg-ex-brand text-white";
}

/** Live scoreboard above the markets: totals, run rates and the last six balls. */
export function ScoreStrip({ board }: { board: LiveBoard }) {
  const { team1, team2, crr, rrr, last6, message } = board;

  return (
    <div className="border-b border-ex-line bg-slate-800 px-3 py-2 text-white">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <span className="text-[13px] font-bold">
          {team1.short} <span className="font-normal text-white/90">{team1.score ?? "-"}</span>
        </span>
        <span className="text-[13px] font-bold">
          {team2.short} <span className="font-normal text-white/90">{team2.score ?? "-"}</span>
        </span>
        {crr && <span className="text-[12px] text-white/70">CRR {crr}</span>}
        {rrr && rrr !== "0.00" && <span className="text-[12px] text-white/70">RRR {rrr}</span>}

        {last6.length > 0 && (
          <span className="ml-auto flex items-center gap-1">
            {last6.map((ball, i) => (
              <span
                key={`${ball}-${i}`}
                className={cn(
                  "grid h-6 min-w-6 place-items-center rounded-full px-1 text-[11px] font-bold",
                  ballTone(ball),
                )}
              >
                {ball}
              </span>
            ))}
          </span>
        )}
      </div>
      {message && <p className="mt-1 text-[12px] font-semibold text-yellow-300">{message}</p>}
    </div>
  );
}
