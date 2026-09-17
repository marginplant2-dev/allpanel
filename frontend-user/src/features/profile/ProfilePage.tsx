import { useQuery } from "@tanstack/react-query";
import { Moon, Sun } from "lucide-react";
import { fetchWallet } from "@/api/wallet";
import { useAuthStore } from "@/store/auth";
import { useThemeStore } from "@/store/theme";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn, formatCredits } from "@/lib/utils";

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const wallet = useQuery({ queryKey: ["wallet"], queryFn: fetchWallet });
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">My Profile</h1>

      <Card>
        <CardContent className="flex items-center gap-4 py-6">
          <span className="grid h-16 w-16 place-items-center rounded-full bg-accent/20 text-2xl font-bold text-accent">
            {(user?.full_name ?? user?.username ?? "?").charAt(0).toUpperCase()}
          </span>
          <div>
            <p className="text-xl font-bold">{user?.full_name}</p>
            <p className="text-sm text-muted-foreground">@{user?.username}</p>
          </div>
          <Badge variant="muted" className="ml-auto">{user?.role}</Badge>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account Details</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <Field label="Username" value={user?.username ?? "—"} />
          <Field label="Full name" value={user?.full_name ?? "—"} />
          <Field label="Role" value={user?.role ?? "—"} />
          <Field label="Status" value={user?.status ?? "—"} />
          <Field label="Available credits" value={formatCredits(wallet.data?.available_balance ?? 0)} />
          <Field label="Locked credits" value={formatCredits(wallet.data?.locked_balance ?? 0)} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">Choose how SportX looks on this device.</p>
          <div className="flex gap-2 rounded-lg border border-border p-1">
            <button
              type="button"
              onClick={() => setTheme("dark")}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                theme === "dark" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Moon className="h-4 w-4" /> Dark
            </button>
            <button
              type="button"
              onClick={() => setTheme("light")}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                theme === "light" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Sun className="h-4 w-4" /> Light
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 font-medium capitalize">{value}</p>
    </div>
  );
}
