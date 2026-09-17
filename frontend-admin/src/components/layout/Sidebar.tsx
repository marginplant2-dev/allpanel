import { NavLink } from "react-router-dom";
import {
  Activity,
  BarChart3,
  Coins,
  Gamepad2,
  LayoutDashboard,
  ListTree,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ROLE_LABELS, childRoleOf } from "@/lib/roles";
import { useAuthStore } from "@/store/auth";
import type { Role } from "@/types";

interface NavItem {
  to: string;
  label: string;
  icon: typeof Users;
  end?: boolean;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const ROLE_ROUTE: Record<Role, string> = {
  MOTHER_ADMIN: "mother-admins",
  SUPER_ADMIN: "super-admins",
  ADMIN: "admins",
  MASTER: "masters",
  AGENT: "agents",
  USER: "players",
};

/** The nav mirrors the chain: you manage the level directly under you, and your own players. */
function groupsFor(role: Role | undefined): NavGroup[] {
  const child = role ? childRoleOf(role) : null;
  const isOwner = role === "MOTHER_ADMIN";

  return [
    { title: "", items: [{ to: "/", label: "Dashboard", icon: LayoutDashboard, end: true }] },
    {
      title: "My Team",
      items: [
        { to: "/users", label: "All Accounts", icon: Users },
        ...(child
          ? [{ to: `/hierarchy/${ROLE_ROUTE[child]}`, label: `${ROLE_LABELS[child]}s`, icon: Users }]
          : []),
        { to: "/hierarchy/players", label: "My Players", icon: Users },
        { to: "/users/create", label: "Create Account", icon: Users },
        { to: "/hierarchy", label: "Downline Tree", icon: ListTree },
      ],
    },
    {
      title: "Coins",
      items: [
        { to: "/credits/transfer", label: "Give Coins", icon: Coins },
        { to: "/credits/requests", label: "Deposit / Withdraw", icon: Coins },
        { to: "/credits/ledger", label: "Coin Ledger", icon: Coins },
      ],
    },
    { title: "Reports", items: [{ to: "/reports", label: "Reports", icon: BarChart3 }] },
    ...(isOwner
      ? [
          { title: "Sports & Content", items: [{ to: "/content/games", label: "Games", icon: Gamepad2 }] },
          { title: "System", items: [{ to: "/system/settings", label: "General Settings", icon: Settings }] },
          {
            title: "Security",
            items: [
              { to: "/security/audit", label: "Audit Logs", icon: ShieldCheck },
              { to: "/security/activity", label: "Activity", icon: Activity },
            ],
          },
        ]
      : []),
  ];
}

export function Sidebar({ collapsed, onNavigate }: { collapsed: boolean; onNavigate?: () => void }) {
  const role = useAuthStore((s) => s.user?.role);
  const groups = groupsFor(role);

  return (
    <div className="flex h-full flex-col overflow-y-auto p-3">
      <div className="mb-6 flex items-center gap-2 px-2 py-1 text-lg font-bold">
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground">
          S
        </span>
        {!collapsed && <span>SportX Admin</span>}
      </div>

      <nav className="flex-1 space-y-5">
        {groups.map((group, i) => (
          <div key={i}>
            {!collapsed && group.title && (
              <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                {group.title}
              </p>
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={onNavigate}
                  title={item.label}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-secondary text-foreground"
                        : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground",
                      collapsed && "justify-center px-2",
                    )
                  }
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </div>
  );
}
