import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchCreditMovement, fetchDashboard, fetchUserGrowth } from "@/api/misc";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCredits } from "@/lib/utils";

const axis = { stroke: "hsl(215 16% 60%)", fontSize: 12 };
const tip = { background: "hsl(222 44% 8%)", border: "1px solid hsl(217 33% 18%)", borderRadius: 8 };

export default function ReportsPage() {
  const stats = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });
  const growth = useQuery({ queryKey: ["user-growth-30"], queryFn: () => fetchUserGrowth(30) });
  const movement = useQuery({ queryKey: ["credit-movement-30"], queryFn: () => fetchCreditMovement(30) });

  return (
    <div>
      <PageHeader title="Reports" description="Hierarchy performance over the last 30 days" />

      <div className="grid gap-4 sm:grid-cols-3">
        <Summary label="Total Users" value={stats.data?.total_users ?? 0} />
        <Summary label="Total Virtual Credits" value={formatCredits(stats.data?.total_virtual_credits ?? 0)} />
        <Summary label="Active Agents" value={stats.data?.active_agents ?? 0} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>New Users (30d)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={growth.data ?? []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 18%)" />
                  <XAxis dataKey="date" {...axis} tickFormatter={(d) => d.slice(5)} />
                  <YAxis {...axis} allowDecimals={false} />
                  <Tooltip contentStyle={tip} />
                  <Line type="monotone" dataKey="users" stroke="hsl(152 76% 45%)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Credit Movement (30d)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={movement.data ?? []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 18%)" />
                  <XAxis dataKey="date" {...axis} tickFormatter={(d) => d.slice(5)} />
                  <YAxis {...axis} />
                  <Tooltip contentStyle={tip} />
                  <Line type="monotone" dataKey="amount" stroke="hsl(262 83% 62%)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Summary({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <CardContent className="py-5">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="mt-1 text-2xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}
