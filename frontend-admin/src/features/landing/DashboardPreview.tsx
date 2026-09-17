import { useQuery } from "@tanstack/react-query";
import { Activity, CreditCard, Gamepad2, Users } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getMeta } from "@/api/meta";

const stats = [
  { icon: Users, label: "Total Users", value: "—" },
  { icon: Activity, label: "Active Agents", value: "—" },
  { icon: CreditCard, label: "Credits Transferred", value: "—" },
  { icon: Gamepad2, label: "Active Games", value: "—" },
];

const sample = Array.from({ length: 12 }, (_, i) => ({
  name: `W${i + 1}`,
  users: Math.round(200 + Math.sin(i / 2) * 80 + i * 30),
}));

export default function DashboardPreview() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["meta"], queryFn: getMeta });

  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 hidden w-60 flex-col border-r border-border bg-card/60 p-4 backdrop-blur-xl lg:flex">
        <div className="mb-8 flex items-center gap-2 text-lg font-bold">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-accent-foreground">S</span>
          SportX Admin
        </div>
        <nav className="space-y-1 text-sm text-muted-foreground">
          {["Dashboard", "Users", "Hierarchy", "Credits", "Content", "Reports", "System", "Security"].map(
            (item, idx) => (
              <div
                key={item}
                className={`rounded-md px-3 py-2 ${idx === 0 ? "bg-secondary text-foreground" : "hover:bg-secondary/50"}`}
              >
                {item}
              </div>
            ),
          )}
        </nav>
      </aside>

      <main className="lg:pl-60">
        <header className="flex items-center justify-between border-b border-border px-6 py-4">
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <span className="text-xs text-muted-foreground">
            API:{" "}
            {isLoading ? "checking…" : isError ? (
              <span className="text-destructive">offline</span>
            ) : (
              <span className="text-primary">{data?.app} v{data?.version}</span>
            )}
          </span>
        </header>

        <div className="grid gap-4 p-6 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="glass rounded-xl p-5">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{s.label}</span>
                <s.icon className="h-5 w-5 text-accent" />
              </div>
              <div className="text-2xl font-bold">{s.value}</div>
            </div>
          ))}
        </div>

        <div className="px-6 pb-10">
          <div className="glass rounded-xl p-5">
            <h2 className="mb-4 font-semibold">User Growth</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sample}>
                  <defs>
                    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(262 83% 62%)" stopOpacity={0.5} />
                      <stop offset="95%" stopColor="hsl(262 83% 62%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 18%)" />
                  <XAxis dataKey="name" stroke="hsl(215 16% 60%)" fontSize={12} />
                  <YAxis stroke="hsl(215 16% 60%)" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(222 44% 8%)",
                      border: "1px solid hsl(217 33% 18%)",
                      borderRadius: 8,
                    }}
                  />
                  <Area type="monotone" dataKey="users" stroke="hsl(262 83% 62%)" fill="url(#g)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
