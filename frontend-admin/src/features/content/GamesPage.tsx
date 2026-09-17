import { useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Star, Trash2 } from "lucide-react";
import {
  createGame,
  deleteGame,
  fetchGamesAdmin,
  updateGame,
  type GamePayload,
} from "@/api/misc";
import type { ApiError } from "@/api/client";
import { toast } from "@/store/toast";
import type { Game } from "@/types";
import { PageHeader } from "@/components/common/PageHeader";
import { DataTable, type Column } from "@/components/data/DataTable";
import { Pagination } from "@/components/data/Pagination";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const EMPTY: GamePayload = {
  name: "",
  slug: "",
  provider: "mock_provider",
  category: "live",
  thumbnail_url: "",
  banner_url: "",
  status: "active",
  featured: false,
  sort_order: 0,
};

export default function GamesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Game | null>(null);
  const [form, setForm] = useState<GamePayload>(EMPTY);

  const query = useQuery({
    queryKey: ["games-admin", page],
    queryFn: () => fetchGamesAdmin({ page, page_size: 15 }),
    placeholderData: keepPreviousData,
  });

  const saveMutation = useMutation({
    mutationFn: () => (editing ? updateGame(editing.id, form) : createGame(form)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["games-admin"] });
      toast.success(editing ? "Game updated" : "Game created");
      setOpen(false);
    },
    onError: (e) => toast.error("Save failed", (e as unknown as ApiError)?.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteGame(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["games-admin"] });
      toast.success("Game deleted");
    },
  });

  function openCreate() {
    setEditing(null);
    setForm(EMPTY);
    setOpen(true);
  }

  function openEdit(g: Game) {
    setEditing(g);
    setForm({
      name: g.name,
      slug: g.slug,
      provider: g.provider,
      category: g.category,
      thumbnail_url: g.thumbnail_url,
      banner_url: g.banner_url ?? "",
      status: g.status,
      featured: g.featured,
      sort_order: g.sort_order,
    });
    setOpen(true);
  }

  const cols: Column<Game>[] = [
    {
      key: "name",
      header: "Game",
      render: (g) => (
        <div className="flex items-center gap-3">
          <img src={g.thumbnail_url} alt="" className="h-10 w-14 rounded object-cover" loading="lazy" />
          <div>
            <p className="font-medium">{g.name}</p>
            <p className="text-xs text-muted-foreground">{g.slug}</p>
          </div>
        </div>
      ),
    },
    { key: "category", header: "Category", render: (g) => <span className="capitalize">{g.category}</span> },
    { key: "provider", header: "Provider", render: (g) => <span className="capitalize">{g.provider.replace(/_/g, " ")}</span> },
    { key: "featured", header: "Featured", render: (g) => (g.featured ? <Badge variant="accent"><Star className="mr-1 h-3 w-3" />Yes</Badge> : <span className="text-muted-foreground">—</span>) },
    { key: "status", header: "Status", render: (g) => <StatusBadge status={g.status} /> },
    {
      key: "actions",
      header: "",
      className: "text-right",
      render: (g) => (
        <div className="flex justify-end gap-1">
          <Button size="icon" variant="ghost" onClick={() => openEdit(g)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="ghost" className="text-destructive" onClick={() => deleteMutation.mutate(g.id)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Games"
        description="Manage the game catalogue — changes appear on the user site instantly"
        action={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" /> Add Game
          </Button>
        }
      />
      <DataTable
        columns={cols}
        rows={query.data?.items}
        rowKey={(g) => g.id}
        isLoading={query.isLoading}
        isError={query.isError}
        onRetry={() => query.refetch()}
        emptyTitle="No games yet"
      />
      <Pagination meta={query.data?.meta} page={page} onPageChange={setPage} />

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "Edit Game" : "Add Game"}</DialogTitle>
          </DialogHeader>
          <form
            className="grid gap-3 sm:grid-cols-2"
            onSubmit={(e) => {
              e.preventDefault();
              saveMutation.mutate();
            }}
          >
            <Field label="Name">
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </Field>
            <Field label="Slug">
              <Input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} required disabled={!!editing} />
            </Field>
            <Field label="Category">
              <Input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} required />
            </Field>
            <Field label="Provider">
              <Input value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} required />
            </Field>
            <Field label="Thumbnail URL" full>
              <Input value={form.thumbnail_url} onChange={(e) => setForm({ ...form, thumbnail_url: e.target.value })} required />
            </Field>
            <Field label="Banner URL" full>
              <Input value={form.banner_url} onChange={(e) => setForm({ ...form, banner_url: e.target.value })} />
            </Field>
            <Field label="Sort order">
              <Input type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })} />
            </Field>
            <div className="flex items-end gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.featured} onChange={(e) => setForm({ ...form, featured: e.target.checked })} />
                Featured
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.status === "active"}
                  onChange={(e) => setForm({ ...form, status: e.target.checked ? "active" : "inactive" })}
                />
                Active
              </label>
            </div>
            <div className="sm:col-span-2 flex gap-3">
              <Button type="submit" disabled={saveMutation.isPending}>
                {saveMutation.isPending ? "Saving…" : "Save game"}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Field({ label, children, full }: { label: string; children: React.ReactNode; full?: boolean }) {
  return (
    <div className={`space-y-1.5 ${full ? "sm:col-span-2" : ""}`}>
      <Label>{label}</Label>
      {children}
    </div>
  );
}
