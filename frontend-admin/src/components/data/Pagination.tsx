import { Button } from "@/components/ui/button";
import type { PageMeta } from "@/types";

export function Pagination({
  meta,
  page,
  onPageChange,
}: {
  meta: PageMeta | undefined;
  page: number;
  onPageChange: (page: number) => void;
}) {
  if (!meta) return null;
  return (
    <div className="mt-4 flex items-center justify-between">
      <span className="text-sm text-muted-foreground">
        Page {meta.page} of {meta.pages || 1} · {meta.total} total
      </span>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          Previous
        </Button>
        <Button variant="outline" size="sm" disabled={page >= meta.pages} onClick={() => onPageChange(page + 1)}>
          Next
        </Button>
      </div>
    </div>
  );
}
