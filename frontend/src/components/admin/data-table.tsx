"use client";

import * as React from "react";
import {
  ArrowDown,
  ArrowUp,
  ChevronLeft,
  ChevronRight,
  Download,
  Loader2,
  Pencil,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ResourceForm } from "./resource-form";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { formatDateFr } from "@/lib/utils";
import {
  useCreateResource,
  useDeleteResource,
  useResourceList,
  useUpdateResource,
} from "@/hooks/use-admin";
import type { AdminResource, ColumnConfig } from "@/config/admin-resources";
import type { ResourceRecord } from "@/types/admin";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const PAGE_SIZE = 25;

function renderCell(col: ColumnConfig, record: ResourceRecord): React.ReactNode {
  const value = record[col.key];
  if (value == null || value === "") return <span className="text-muted-foreground">—</span>;
  if (col.kind === "date") return formatDateFr(String(value));
  if (col.kind === "badge") return <Badge variant="secondary">{String(value)}</Badge>;
  return String(value);
}

export function DataTable({ resource }: { resource: AdminResource }) {
  const [page, setPage] = React.useState(1);
  const [rawQuery, setRawQuery] = React.useState("");
  const [q, setQ] = React.useState("");
  const [sort, setSort] = React.useState<string | undefined>(undefined);
  const [order, setOrder] = React.useState<"asc" | "desc">("asc");
  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<ResourceRecord | null>(null);

  React.useEffect(() => {
    const t = setTimeout(() => {
      setQ(rawQuery);
      setPage(1);
    }, 350);
    return () => clearTimeout(t);
  }, [rawQuery]);

  const { data, isLoading, isError } = useResourceList(resource.name, {
    page,
    size: PAGE_SIZE,
    sort,
    order,
    q,
  });
  const createM = useCreateResource(resource.name);
  const updateM = useUpdateResource(resource.name);
  const deleteM = useDeleteResource(resource.name);

  const toggleSort = (key: string) => {
    if (sort === key) setOrder((o) => (o === "asc" ? "desc" : "asc"));
    else {
      setSort(key);
      setOrder("asc");
    }
  };

  const handleSubmit = async (body: Record<string, unknown>) => {
    if (editing) await updateM.mutateAsync({ id: editing.id, body });
    else await createM.mutateAsync(body);
    setFormOpen(false);
    setEditing(null);
  };

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[220px] flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={rawQuery}
            onChange={(e) => setRawQuery(e.target.value)}
            placeholder={`Rechercher un ${resource.singular}…`}
            className="pl-9"
          />
        </div>
        <Button variant="outline" asChild>
          <a
            href={`${API_BASE}${API_ENDPOINTS.admin.resourceExport(resource.name)}`}
            target="_blank"
            rel="noreferrer"
          >
            <Download className="size-4" /> Exporter
          </a>
        </Button>
        <Button
          onClick={() => {
            setEditing(null);
            setFormOpen(true);
          }}
        >
          <Plus className="size-4" /> Nouveau
        </Button>
      </div>

      <div className="overflow-x-auto rounded-2xl border">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead>
            <tr className="border-b bg-secondary/40 text-left text-xs font-medium text-muted-foreground">
              {resource.columns.map((col) => (
                <th key={col.key} className="whitespace-nowrap px-4 py-3">
                  <button
                    type="button"
                    onClick={() => toggleSort(col.key)}
                    className="inline-flex items-center gap-1 hover:text-foreground"
                  >
                    {col.label}
                    {sort === col.key &&
                      (order === "asc" ? (
                        <ArrowUp className="size-3" />
                      ) : (
                        <ArrowDown className="size-3" />
                      ))}
                  </button>
                </th>
              ))}
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td
                  colSpan={resource.columns.length + 1}
                  className="px-4 py-10 text-center text-muted-foreground"
                >
                  <Loader2 className="mx-auto size-4 animate-spin" />
                </td>
              </tr>
            ) : isError ? (
              <tr>
                <td
                  colSpan={resource.columns.length + 1}
                  className="px-4 py-10 text-center text-sm text-muted-foreground"
                >
                  Impossible de charger les données (API démarrée ?).
                </td>
              </tr>
            ) : data && data.items.length > 0 ? (
              data.items.map((record) => (
                <tr
                  key={record.id}
                  className="border-b last:border-0 hover:bg-secondary/30"
                >
                  {resource.columns.map((col) => (
                    <td key={col.key} className="px-4 py-3">
                      {renderCell(col, record)}
                    </td>
                  ))}
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-muted-foreground"
                        onClick={() => {
                          setEditing(record);
                          setFormOpen(true);
                        }}
                        aria-label="Modifier"
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-muted-foreground hover:text-destructive"
                        onClick={() => {
                          if (window.confirm("Supprimer cet élément ?"))
                            deleteM.mutate(record.id);
                        }}
                        aria-label="Supprimer"
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={resource.columns.length + 1}
                  className="px-4 py-10 text-center text-sm text-muted-foreground"
                >
                  Aucun enregistrement. Utilisez « Nouveau » ou l&apos;import.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {data && data.pages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {data.total} élément(s) · page {data.page}/{data.pages}
          </span>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="icon"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              <ChevronLeft className="size-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              disabled={page >= data.pages}
              onClick={() => setPage((p) => p + 1)}
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      )}

      <ResourceForm
        title={
          editing
            ? `Modifier — ${resource.singular}`
            : `Nouveau — ${resource.singular}`
        }
        fields={resource.fields}
        initial={editing}
        open={formOpen}
        onOpenChange={setFormOpen}
        onSubmit={handleSubmit}
        pending={createM.isPending || updateM.isPending}
      />
    </div>
  );
}
