import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Play, X } from "lucide-react";
import { fetchGameBySlug, fetchGames } from "@/api/games";
import { LazyImage } from "@/components/common/LazyImage";
import { GameTile } from "@/components/game/GameCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState, SectionHeader } from "@/components/common/States";
import { Skeleton } from "@/components/ui/skeleton";

export default function GameDetailPage() {
  const { slug = "" } = useParams();
  const [playing, setPlaying] = useState(false);
  const game = useQuery({ queryKey: ["game", slug], queryFn: () => fetchGameBySlug(slug) });
  const related = useQuery({
    queryKey: ["games", { category: game.data?.category }],
    queryFn: () => fetchGames({ category: game.data?.category }),
    enabled: !!game.data,
  });

  if (game.isLoading) return <Skeleton className="h-96 w-full" />;
  if (game.isError || !game.data) return <ErrorState onRetry={() => game.refetch()} />;

  const g = game.data;

  return (
    <div className="space-y-8">
      <Link to="/casino" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to casino
      </Link>

      <div className="overflow-hidden rounded-2xl border border-border">
        <div className="relative">
          <LazyImage src={g.banner_url ?? g.thumbnail_url} alt={g.name} aspect="aspect-[21/9]" />
          <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent" />
          <div className="absolute bottom-0 flex w-full flex-col gap-3 p-6 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="mb-2 flex gap-2">
                {g.category === "live" && <Badge variant="live">LIVE</Badge>}
                {g.featured && <Badge variant="accent">Featured</Badge>}
                <Badge variant="muted" className="capitalize">{g.category}</Badge>
              </div>
              <h1 className="text-3xl font-extrabold">{g.name}</h1>
              <p className="capitalize text-muted-foreground">{g.provider.replace(/_/g, " ")}</p>
            </div>
            <Button size="lg" onClick={() => setPlaying(true)}>
              <Play className="h-5 w-5 fill-current" /> Play demo
            </Button>
          </div>
        </div>
      </div>

      {playing &&
        (/aviator|crash/i.test(g.slug) || /aviator|crash/i.test(g.name) ? (
          <CrashDemo game={g} onClose={() => setPlaying(false)} />
        ) : (
          <GameDemo game={g} onClose={() => setPlaying(false)} />
        ))}

      <p className="max-w-2xl text-sm text-muted-foreground">
        This is a virtual, display-only game experience. No real money is involved and no wagering
        is executed — all play uses virtual credits for entertainment simulation.
      </p>

      {related.data && related.data.length > 1 && (
        <section>
          <SectionHeader title="Related Games" />
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {related.data
              .filter((r) => r.slug !== g.slug)
              .slice(0, 5)
              .map((r) => (
                <GameTile key={r.id} game={r} />
              ))}
          </div>
        </section>
      )}
    </div>
  );
}

const CRASH_PATH = { x1: 8, y1: 88, x2: 88, y2: 12 };

function generateCrashPoint() {
  const r = Math.random();
  if (r < 0.03) return 1; // instant crash, matches real crash-game house edge
  return Math.max(1, 0.97 / (1 - r));
}

function CrashDemo({
  game,
  onClose,
}: {
  game: { name: string };
  onClose: () => void;
}) {
  const [credits, setCredits] = useState(1000);
  const [bet, setBet] = useState(100);
  const [phase, setPhase] = useState<"waiting" | "running" | "crashed">("waiting");
  const [multiplier, setMultiplier] = useState(1);
  const [cashedOutAt, setCashedOutAt] = useState<number | null>(null);
  const crashPoint = useRef(1);
  const startedAt = useRef(0);
  const frame = useRef(0);

  useEffect(() => {
    if (phase !== "running") return;
    const tick = () => {
      const elapsed = (performance.now() - startedAt.current) / 1000;
      const next = Math.min(Math.pow(1.6, elapsed), crashPoint.current);
      setMultiplier(next);
      if (next >= crashPoint.current) {
        setPhase("crashed");
        return;
      }
      frame.current = requestAnimationFrame(tick);
    };
    frame.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame.current);
  }, [phase]);

  function placeBet() {
    if (phase === "running" || bet > credits || bet <= 0) return;
    setCredits((c) => c - bet);
    setCashedOutAt(null);
    setMultiplier(1);
    crashPoint.current = generateCrashPoint();
    startedAt.current = performance.now();
    setPhase("running");
  }

  function cashOut() {
    if (phase !== "running" || cashedOutAt) return;
    setCashedOutAt(multiplier);
    setCredits((c) => c + bet * multiplier);
  }

  const progress = Math.min((multiplier - 1) / 4, 1);
  const planeX = CRASH_PATH.x1 + progress * (CRASH_PATH.x2 - CRASH_PATH.x1);
  const planeY = CRASH_PATH.y1 + progress * (CRASH_PATH.y2 - CRASH_PATH.y1);
  const trailLength = progress * Math.hypot(CRASH_PATH.x2 - CRASH_PATH.x1, CRASH_PATH.y1 - CRASH_PATH.y2);
  const trailAngle = Math.atan2(CRASH_PATH.y1 - CRASH_PATH.y2, CRASH_PATH.x2 - CRASH_PATH.x1) * (180 / Math.PI);

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/80 p-4" onClick={onClose}>
      <div
        className="w-full max-w-lg overflow-hidden rounded-2xl border border-border bg-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-3">
          <p className="font-semibold">{game.name} — Demo</p>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-5 p-6">
          <div className="relative aspect-video overflow-hidden rounded-xl border border-border bg-[radial-gradient(ellipse_at_bottom,_#1b1035,_#05030d)]">
            {phase !== "waiting" && (
              <>
                <div
                  className="absolute h-[3px] origin-left rounded-full bg-gradient-to-r from-orange-500 to-red-500"
                  style={{
                    left: `${CRASH_PATH.x1}%`,
                    top: `${CRASH_PATH.y1}%`,
                    width: `${trailLength}%`,
                    transform: `rotate(-${trailAngle}deg)`,
                  }}
                />
                <div
                  className="absolute text-3xl"
                  style={{ left: `${planeX}%`, top: `${planeY}%`, transform: "translate(-50%, -50%) rotate(-25deg)" }}
                >
                  ✈️
                </div>
              </>
            )}

            <div className="absolute inset-0 grid place-items-center">
              {phase === "waiting" ? (
                <p className="text-lg font-semibold text-muted-foreground">Place a bet to start</p>
              ) : phase === "crashed" ? (
                <div className="text-center">
                  <p className="text-3xl font-extrabold text-red-400">Crashed @ {crashPoint.current.toFixed(2)}x</p>
                  {cashedOutAt ? (
                    <p className="mt-1 text-sm text-emerald-400">
                      Cashed out at {cashedOutAt.toFixed(2)}x — won +{Math.floor(bet * cashedOutAt)}
                    </p>
                  ) : (
                    <p className="mt-1 text-sm text-muted-foreground">You lost {bet}</p>
                  )}
                </div>
              ) : (
                <p className={`text-4xl font-extrabold ${cashedOutAt ? "text-emerald-400" : "text-white"}`}>
                  {multiplier.toFixed(2)}x
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Credits</span>
            <span className="font-bold">{Math.floor(credits)}</span>
          </div>

          <div className="flex items-center gap-2">
            {[50, 100, 250].map((v) => (
              <Button
                key={v}
                variant={bet === v ? "default" : "outline"}
                size="sm"
                disabled={phase === "running"}
                onClick={() => setBet(v)}
              >
                {v}
              </Button>
            ))}
          </div>

          {phase === "running" && !cashedOutAt ? (
            <Button className="w-full" size="lg" onClick={cashOut}>
              Cash Out ({Math.floor(bet * multiplier)})
            </Button>
          ) : (
            <Button className="w-full" size="lg" disabled={bet > credits || phase === "running"} onClick={placeBet}>
              <Play className="h-5 w-5 fill-current" />
              Place Bet ({bet})
            </Button>
          )}

          {credits <= 0 && phase !== "running" && (
            <Button variant="outline" className="w-full" onClick={() => setCredits(1000)}>
              Reset credits
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function GameDemo({
  game,
  onClose,
}: {
  game: { name: string; thumbnail_url: string };
  onClose: () => void;
}) {
  const [credits, setCredits] = useState(1000);
  const [bet, setBet] = useState(50);
  const [spinning, setSpinning] = useState(false);
  const [result, setResult] = useState<{ won: boolean; amount: number } | null>(null);

  const play = () => {
    if (spinning || bet > credits || bet <= 0) return;
    setSpinning(true);
    setResult(null);
    setCredits((c) => c - bet);
    window.setTimeout(() => {
      const won = Math.random() > 0.5;
      const amount = won ? bet * 2 : 0;
      if (won) setCredits((c) => c + amount);
      setResult({ won, amount });
      setSpinning(false);
    }, 1000);
  };

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/80 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg overflow-hidden rounded-2xl border border-border bg-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-3">
          <p className="font-semibold">{game.name} — Demo</p>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-5 p-6">
          <div className="grid aspect-video place-items-center overflow-hidden rounded-xl border border-border bg-background">
            {spinning ? (
              <div className="animate-pulse text-lg font-semibold text-primary">Playing…</div>
            ) : result ? (
              <div className="text-center">
                <p
                  className={`text-2xl font-extrabold ${
                    result.won ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {result.won ? `You won +${result.amount}` : "You lost"}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">Virtual credits only</p>
              </div>
            ) : (
              <LazyImage
                src={game.thumbnail_url}
                alt={game.name}
                aspect="aspect-video"
                className="opacity-80"
              />
            )}
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Credits</span>
            <span className="font-bold">{credits}</span>
          </div>

          <div className="flex items-center gap-2">
            {[50, 100, 250].map((v) => (
              <Button
                key={v}
                variant={bet === v ? "default" : "outline"}
                size="sm"
                onClick={() => setBet(v)}
              >
                {v}
              </Button>
            ))}
          </div>

          <Button
            className="w-full"
            size="lg"
            disabled={spinning || bet > credits}
            onClick={play}
          >
            <Play className="h-5 w-5 fill-current" />
            {spinning ? "Playing…" : `Play (${bet})`}
          </Button>

          {credits <= 0 && (
            <Button variant="outline" className="w-full" onClick={() => setCredits(1000)}>
              Reset credits
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
