import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Plus, Search, UserCog } from "lucide-react";
import {
  activateUser,
  fetchUsers,
  suspendUser,
  type UserListParams,
} from "@/api/users";
import { startImpersonation } from "@/api/misc";
import { useAuthStore } from "@/store/auth";
import { toast } from "@/store/toast";
import { ROLE_LABELS, ROLE_ORDER } from "@/lib/roles";
import type { ManagedUser, Role } from "@/types";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable, type Column } from "@/components/data/DataTable";
import { Pagination } from "@/components/data/Pagination";
import { RoleBadge, StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useDebounce } from "@/hooks/useDebounce";
import { formatCredits, formatDateTime } from "@/lib/utils";

export default function UsersListPage({ fixedRole, title }: { fixedRole?: Role; title?: string }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((s) => s.user);
  const startImp = useAuthStore((s) => s.startImpersonation);

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const debouncedSearch = useDebounce(search, 300);

  const params: UserListParams = {
    page,
    page_size: 15,
    search: debouncedSearch || undefined,
    role: (fixedRole ?? (role || undefined)) as Role | undefined,
    status: status || undefined,
  };

  const query = useQuery({
    queryKey: ["users", params],
    queryFn: () => fetchUsers(params),
    placeholderData: keepPreviousData,
  });

  const setStatusMutation = useMutation({
    mutationFn: ({ id, suspend }: { id: string; suspend: boolean }) =>
      suspend ? suspendUser(id) : activateUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      toast.success("User status updated");
    },
    onError: (e: any) => toast.error("Update failed", e?.message),
  });

  const impersonateMutation = useMutation({
    mutationFn: (id: string) => startImpersonation(id),
    onSuccess: (data) => {
      const adminToken = localStorage.getItem("sportx.accessToken")!;
      startImp(data.user, data.access_token, adminToken);
      queryClient.clear();
      toast.info(`Viewing as ${data.user.username}`);
      navigate("/");
    },
    onError: (e: any) => toast.error("Impersonation failed", e?.message),
  });

  const columns: Column<ManagedUser>[] = [
    {
      key: "username",
      header: "Username",
      render: (u) => (
        <Link to={`/users/${u.id}`} className="font-medium hover:text-primary">
          {u.username}
        </Link>
      ),
    },
    { key: "full_name", header: "Name", render: (u) => u.full_name },
    { key: "role", header: "Role", render: (u) => <RoleBadge role={u.role} /> },
    { key: "status", header: "Status", render: (u) => <StatusBadge status={u.status} /> },
    { key: "credit", header: "Credit Limit", render: (u) => formatCredits(u.credit_limit) },
    {
      key: "last_login",
      header: "Last Login",
      render: (u) => <span className="text-muted-foreground">{u.last_login ? formatDateTime(u.last_login) : "—"}</span>,
    },
    {
      key: "actions",
      header: "Actions",
      className: "text-right",
      render: (u) => (
        <div className="flex justify-end gap-1">
          <Button size="icon" variant="ghost" title="View" onClick={() => navigate(`/users/${u.id}`)}>
            <Eye className="h-4 w-4" />
          </Button>
          {u.role !== "USER" && u.id !== currentUser?.id && (
            <Button
              size="icon"
              variant="ghost"
              title="View as"
              onClick={() => impersonateMutation.mutate(u.id)}
            >
              <UserCog className="h-4 w-4" />
            </Button>
          )}
          {u.id !== currentUser?.id &&
            (u.status === "suspended" ? (
              <Button size="sm" variant="outline" onClick={() => setStatusMutation.mutate({ id: u.id, suspend: false })}>
                Activate
              </Button>
            ) : (
              <Button
                size="sm"
                variant="ghost"
                className="text-destructive"
                onClick={() => setStatusMutation.mutate({ id: u.id, suspend: true })}
              >
                Suspend
              </Button>
            ))}
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title={title ?? "Users"}
        description="Manage users within your hierarchy"
        action={
          <Button onClick={() => navigate("/users/create")}>
            <Plus className="h-4 w-4" /> Create User
          </Button>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search username or name…" className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        {!fixedRole && (
          <Select value={role} onChange={(e) => { setRole(e.target.value); setPage(1); }} className="sm:w-44">
            <option value="">All roles</option>
            {ROLE_ORDER.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r]}
              </option>
            ))}
          </Select>
        )}
        <Select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="sm:w-40">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
        </Select>
      </div>

      <DataTable
        columns={columns}
        rows={query.data?.items}
        rowKey={(u) => u.id}
        isLoading={query.isLoading}
        isError={query.isError}
        onRetry={() => query.refetch()}
        emptyTitle="No users found"
        emptyDescription="Create a user or adjust your filters."
      />
      <Pagination meta={query.data?.meta} page={page} onPageChange={setPage} />
    </div>
  );
}
