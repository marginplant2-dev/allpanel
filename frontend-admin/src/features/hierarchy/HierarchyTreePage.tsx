import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight } from "lucide-react";
import { fetchTree } from "@/api/misc";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { RoleBadge, StatusBadge } from "@/components/common/StatusBadge";
import { ErrorState } from "@/components/common/States";
import { Skeleton } from "@/components/ui/skeleton";
import type { TreeNode } from "@/types";

function TreeRow({ node, depth }: { node: TreeNode; depth: number }) {
  const [open, setOpen] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;
  return (
    <div>
      <div
        className="flex items-center gap-2 rounded-md px-2 py-2 hover:bg-secondary/40"
        style={{ paddingLeft: depth * 20 + 8 }}
      >
        {hasChildren ? (
          <button onClick={() => setOpen((o) => !o)} className="text-muted-foreground">
            {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        ) : (
          <span className="inline-block w-4" />
        )}
        <span className="font-medium">{node.full_name}</span>
        <span className="text-sm text-muted-foreground">@{node.username}</span>
        <RoleBadge role={node.role} />
        <StatusBadge status={node.status} />
      </div>
      {open && hasChildren && node.children.map((c) => <TreeRow key={c.id} node={c} depth={depth + 1} />)}
    </div>
  );
}

export default function HierarchyTreePage() {
  const query = useQuery({ queryKey: ["hierarchy-tree"], queryFn: fetchTree });

  const roots: TreeNode[] = query.data
    ? query.data.root
      ? [query.data.root]
      : query.data.roots ?? []
    : [];

  return (
    <div>
      <PageHeader title="Downline Tree" description="Your hierarchy at a glance" />
      {query.isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : query.isError ? (
        <ErrorState onRetry={() => query.refetch()} />
      ) : (
        <Card>
          <CardContent className="py-3">
            {roots.map((r) => (
              <TreeRow key={r.id} node={r} depth={0} />
            ))}
            {roots.length === 0 && <p className="py-8 text-center text-sm text-muted-foreground">No downline yet.</p>}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
