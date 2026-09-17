import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Coins,
  Gamepad2,
  Radio,
  TrendingUp,
  UserCheck,
  UserPlus,
  Users,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchCreditMovement, fetchDashboard, fetchLedger, fetchMyWallet, fetchUserGrowth } from "@/api/misc";
import { fetchUsers } from "@/api/users";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DataTable, type Column } from "@/components/data/DataTable";
import { RoleBadge, StatusBadge } from "@/components/common/StatusBadge";
import type { ManagedUser, Transaction } from "@/types";
import { formatCredits, formatDateTime } from "@/lib/utils";
import { ROLE_LABELS, ROLE_ORDER } from "@/lib/roles";
import { useAuthStore } from "@/store/auth";

const chartAxis = { stroke: "hsl(215 16% 60%)", fontSize: 12 };
// theme-aware: recharts renders these into the DOM, so the CSS vars resolve live
const tooltipStyle = {
  background: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: 8,
  color: "hsl(var(--popover-foreground))",
};

export default function DashboardPage() {
  const stats = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });
  const wallet = useQuery({ queryKey: ["my-wallet"], queryFn: fetchMyWallet });
  const role = useAuthStore((s) => s.user?.role);
  const growth = useQuery({ queryKey: ["user-growth"], queryFn: () => fetchUserGrowth(14) });
  const movement = useQuery({ queryKey: ["credit-movement"], queryFn: () => fetchCreditMovement(14) });
  const recentUsers = useQuery({
    queryKey: ["users", "recent"],
    queryFn: () => fetchUsers({ page: 1, page_size: 5, sort_by: "created_at", order: "desc" }),
  });
  const recentTxns = useQuery({ queryKey: ["ledger", "recent"], queryFn: () => fetchLedger({ page: 1, page_size: 5 }) });

  const s = stats.data;
  const loading = stats.isLoading;

  const userCols: Column<ManagedUser>[] = [
    { key: "username", header: "Username", render: (u) => <span className="font-medium">{u.username}</span> },
    { key: "role", header: "Role", render: (u) => <RoleBadge role={u.role} /> },
    { key: "status", header: "Status", render: (u) => <StatusBadge status={u.status} /> },
    {
      key: "created",
      header: "Created",
      render: (u) => <span className="text-muted-foreground">{u.created_at ? formatDateTime(u.created_at) : "—"}</span>,
    },
  ];

  const txnCols: Column<Transaction>[] = [
    { key: "type", header: "Type", render: (t) => <span className="capitalize">{t.transaction_type.replace(/_/g, " ").toLowerCase()}</span> },
    { key: "amount", header: "Amount", render: (t) => <span className="font-semibold">{formatCredits(t.amount)}</span> },
    { key: "status", header: "Status", render: (t) => <StatusBadge status={t.status} /> },
    { key: "date", header: "Date", render: (t) => <span className="text-muted-foreground">{formatDateTime(t.created_at)}</span> },
  ];

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Your own accounts and coins. Accounts created by your downline live in their panel — use “Login as” to look."
      />

      <Card className="mb-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">My Team</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {ROLE_ORDER.filter((r) => (s?.team_by_role?.[r] ?? 0) > 0).map((r) => (
            <span key={r} className="rounded-lg border border-border bg-secondary/40 px-3 py-2 text-sm">
              <span className="font-bold">{s?.team_by_role?.[r]}</span>{" "}
              <span className="text-muted-foreground">{ROLE_LABELS[r]}{(s?.team_by_role?.[r] ?? 0) > 1 ? "s" : ""}</span>
            </span>
          ))}
          {!loading && Object.keys(s?.team_by_role ?? {}).length === 0 && (
            <p className="text-sm text-muted-foreground">
              You have not created any accounts yet{role ? ` — start with a ${ROLE_LABELS[role]} sub-account or a player.` : "."}
            </p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Users} label="Total Users" value={s?.total_users ?? 0} loading={loading} />
        <StatCard icon={UserCheck} label="Active Users" value={s?.active_users ?? 0} loading={loading} />
        <StatCard icon={UserPlus} label="New Today" value={s?.new_users_today ?? 0} loading={loading} />
        <StatCard icon={Activity} label="Active Agents" value={s?.active_agents ?? 0} loading={loading} />
        <StatCard
          icon={Coins}
          label="My Coins"
          value={formatCredits(wallet.data?.available_balance ?? 0)}
          loading={wallet.isLoading}
          accent="accent"
        />
        <StatCard icon={Coins} label="Team Coins" value={formatCredits(s?.total_virtual_credits ?? 0)} loading={loading} accent="accent" />
        <StatCard icon={TrendingUp} label="Transferred Today" value={formatCredits(s?.credits_transferred_today ?? 0)} loading={loading} accent="accent" />
        <StatCard icon={Radio} label="Active Events" value={s?.active_events ?? 0} loading={loading} accent="accent" />
        <StatCard icon={Gamepad2} label="Active Games" value={s?.active_games ?? 0} loading={loading} accent="accent" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>User Growth</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={growth.data ?? []}>
                  <defs>
                    <linearGradient id="ug" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(152 76% 45%)" stopOpacity={0.5} />
                      <stop offset="95%" stopColor="hsl(152 76% 45%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 18%)" />
                  <XAxis dataKey="date" {...chartAxis} tickFormatter={(d) => d.slice(5)} />
                  <YAxis {...chartAxis} allowDecimals={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="users" stroke="hsl(152 76% 45%)" fill="url(#ug)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Credit Movement</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={movement.data ?? []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 18%)" />
                  <XAxis dataKey="date" {...chartAxis} tickFormatter={(d) => d.slice(5)} />
                  <YAxis {...chartAxis} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="amount" fill="hsl(262 83% 62%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 font-semibold">Recent Users</h2>
          <DataTable
            columns={userCols}
            rows={recentUsers.data?.items}
            rowKey={(u) => u.id}
            isLoading={recentUsers.isLoading}
          />
        </div>
        <div>
          <h2 className="mb-3 font-semibold">Recent Transactions</h2>
          <DataTable
            columns={txnCols}
            rows={recentTxns.data?.items}
            rowKey={(t) => t.transaction_id}
            isLoading={recentTxns.isLoading}
          />
        </div>
      </div>
    </div>
  );
}
