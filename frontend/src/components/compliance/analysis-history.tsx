"use client";

import Link from "next/link";
import { Loader2, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { RiskBadge } from "./risk-badge";
import { EmptyState } from "@/components/ui/empty-state";
import { formatDateFr } from "@/lib/utils";
import { useAnalyses } from "@/hooks/use-analyses";
import { FileSearch } from "lucide-react";
import type { AnalysisStatus } from "@/types/compliance";

const STATUS_META: Record<
  AnalysisStatus,
  { label: string; variant: "secondary" | "warning" | "success" | "destructive" }
> = {
  en_attente: { label: "En attente", variant: "secondary" },
  en_cours: { label: "En cours", variant: "warning" },
  termine: { label: "Terminé", variant: "success" },
  partiel: { label: "Partiel", variant: "warning" },
  erreur: { label: "Erreur", variant: "destructive" },
};

export function AnalysisHistory() {
  const { data, isLoading } = useAnalyses();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" /> Chargement…
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={FileSearch}
        title="Aucune analyse"
        description="Importez une facture pour lancer une première analyse de conformité."
      />
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border">
      <table className="w-full min-w-[820px] border-collapse text-sm">
        <thead>
          <tr className="border-b bg-secondary/40 text-left text-xs font-medium text-muted-foreground">
            {["Facture", "Fournisseur", "Date", "Statut", "Risque", "Progression", ""].map(
              (h) => (
                <th key={h} className="whitespace-nowrap px-4 py-3">
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody>
          {data.map((a) => {
            const status = STATUS_META[a.status];
            const pct = a.total_items
              ? Math.round((100 * a.processed_items) / a.total_items)
              : 0;
            const active = a.status === "en_cours" || a.status === "en_attente";
            return (
              <tr key={a.id} className="border-b last:border-0 hover:bg-secondary/30">
                <td className="px-4 py-3 font-medium">
                  {a.invoice_number ?? a.original_filename}
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  {a.supplier_name_raw ?? "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                  {formatDateFr(a.created_at)}
                </td>
                <td className="px-4 py-3">
                  <Badge variant={status.variant}>{status.label}</Badge>
                </td>
                <td className="px-4 py-3">
                  <RiskBadge level={a.overall_risk} />
                </td>
                <td className="px-4 py-3">
                  {active ? (
                    <div className="w-28">
                      <Progress value={pct} />
                      <span className="text-[11px] text-muted-foreground">
                        {a.processed_items}/{a.total_items}
                      </span>
                    </div>
                  ) : (
                    <span className="text-xs text-muted-foreground">
                      {a.total_items} ligne(s)
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/analyse-importation/${a.id}`}
                    className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                  >
                    Ouvrir <ChevronRight className="size-4" />
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
