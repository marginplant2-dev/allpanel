import { useQuery } from "@tanstack/react-query";
import { Activity, Gamepad2, Trophy, Wallet } from "lucide-react";
import { getMeta } from "@/api/meta";
import { Button } from "@/components/ui/button";

const features = [
  { icon: Trophy, title: "Live Sports", desc: "Cricket, football, tennis and more in real time." },
  { icon: Gamepad2, title: "Casino & Games", desc: "A dynamic, ever-growing game catalogue." },
  { icon: Wallet, title: "Virtual Wallet", desc: "Track demo credits with a full ledger." },
  { icon: Activity, title: "Realtime", desc: "Instant updates powered by WebSockets." },
];

export default function LandingPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["meta"], queryFn: getMeta });

  return (
    <main className="min-h-screen">
      <header className="container flex items-center justify-between py-6">
        <div className="flex items-center gap-2 text-xl font-bold">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary text-primary-foreground">S</span>
          SportX
        </div>
        <nav className="flex items-center gap-3">
          <Button variant="ghost" size="sm">Sign in</Button>
          <Button size="sm">Get started</Button>
        </nav>
      </header>

      <section className="container flex flex-col items-center gap-6 py-24 text-center">
        <span className="rounded-full border border-primary/30 bg-primary/10 px-4 py-1 text-xs font-medium text-primary">
          Virtual credits · Entertainment simulation
        </span>
        <h1 className="max-w-3xl text-balance text-5xl font-extrabold leading-tight md:text-6xl">
          The premium <span className="text-primary">sports & games</span> dashboard
        </h1>
        <p className="max-w-xl text-lg text-muted-foreground">
          A modern, dark, glassmorphic experience for live events and a dynamic game catalogue.
        </p>
        <div className="flex gap-3">
          <Button size="lg">Explore platform</Button>
          <Button size="lg" variant="outline">View sports</Button>
        </div>

        <div className="mt-4 rounded-lg border border-border bg-card/50 px-4 py-2 text-sm">
          Backend status:{" "}
          {isLoading ? (
            <span className="text-muted-foreground">checking…</span>
          ) : isError ? (
            <span className="text-destructive">unreachable</span>
          ) : (
            <span className="text-primary">
              connected · {data?.app} v{data?.version} ({data?.environment})
            </span>
          )}
        </div>
      </section>

      <section className="container grid gap-4 pb-24 sm:grid-cols-2 lg:grid-cols-4">
        {features.map((f) => (
          <div key={f.title} className="glass rounded-xl p-6 transition-transform hover:-translate-y-1">
            <f.icon className="mb-4 h-8 w-8 text-primary" />
            <h3 className="mb-1 font-semibold">{f.title}</h3>
            <p className="text-sm text-muted-foreground">{f.desc}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
