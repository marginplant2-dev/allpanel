import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/common/States";

export interface Column<T> {
  key: string;
  header: string;
  className?: string;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[] | undefined;
  rowKey: (row: T) => string;
  isLoading?: boolean;
  isError?: boolean;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  isLoading,
  isError,
  onRetry,
  emptyTitle = "No records",
  emptyDescription,
}: DataTableProps<T>) {
  if (isError) return <ErrorState onRetry={onRetry} />;

  return (
    <>
      {/* Phones get one card per row — a sideways-scrolling table is unreadable there. */}
      <div className="space-y-2 sm:hidden">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2 rounded-xl border border-border p-3">
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-4 w-1/3" />
              </div>
            ))
          : rows?.map((row) => (
              <div key={rowKey(row)} className="rounded-xl border border-border bg-card p-3">
                {columns.map((c) => (
                  <div key={c.key} className="flex items-start justify-between gap-3 py-1 text-sm">
                    <span className="shrink-0 text-xs uppercase tracking-wide text-muted-foreground">
                      {c.header}
                    </span>
                    <span className="min-w-0 text-right">{c.render(row)}</span>
                  </div>
                ))}
              </div>
            ))}
        {!isLoading && rows && rows.length === 0 && (
          <EmptyState title={emptyTitle} description={emptyDescription} />
        )}
      </div>

      <div className="hidden overflow-hidden rounded-xl border border-border sm:block">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-secondary/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
              {columns.map((c) => (
                <th key={c.key} className={`px-4 py-3 font-medium ${c.className ?? ""}`}>
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading
              ? Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i}>
                    {columns.map((c) => (
                      <td key={c.key} className="px-4 py-3">
                        <Skeleton className="h-4 w-full max-w-[140px]" />
                      </td>
                    ))}
                  </tr>
                ))
              : rows?.map((row) => (
                  <tr key={rowKey(row)} className="transition-colors hover:bg-secondary/30">
                    {columns.map((c) => (
                      <td key={c.key} className={`px-4 py-3 ${c.className ?? ""}`}>
                        {c.render(row)}
                      </td>
                    ))}
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
      {!isLoading && rows && rows.length === 0 && (
        <div className="p-4">
          <EmptyState title={emptyTitle} description={emptyDescription} />
        </div>
      )}
      </div>
    </>
  );
}
