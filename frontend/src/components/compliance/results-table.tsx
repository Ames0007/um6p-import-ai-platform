"use client";

import { Badge } from "@/components/ui/badge";
import type { AnalysisItem } from "@/types/compliance";

const HEADERS = [
  "Ligne", "Produit (facture)", "Produit rapproché", "Confiance", "Code SH",
  "Droit %", "TVA %", "Autorisations", "Documents", "Historique", "Statut",
];

const STATUS: Record<
  AnalysisItem["status"],
  { label: string; variant: "success" | "warning" | "secondary" }
> = {
  rapproche: { label: "Rapproché", variant: "success" },
  a_valider: { label: "À valider", variant: "warning" },
  sans_donnees: { label: "Sans données", variant: "secondary" },
};

function pct(v: number | null): string {
  return v == null ? "—" : `${Math.round(v * 100)} %`;
}

export function ResultsTable({
  items,
  onSelect,
}: {
  items: AnalysisItem[];
  onSelect: (item: AnalysisItem) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-2xl border">
      <table className="w-full min-w-[980px] border-collapse text-sm">
        <thead>
          <tr className="border-b bg-secondary/40 text-left text-xs font-medium text-muted-foreground">
            {HEADERS.map((h) => (
              <th key={h} className="whitespace-nowrap px-3 py-3">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((it) => {
            const status = STATUS[it.status];
            return (
              <tr
                key={it.id}
                onClick={() => onSelect(it)}
                className="cursor-pointer border-b last:border-0 hover:bg-accent/40"
              >
                <td className="px-3 py-2.5 tabular-nums">{it.line_number}</td>
                <td className="px-3 py-2.5 font-medium">{it.raw_product_name ?? "—"}</td>
                <td className="px-3 py-2.5 text-muted-foreground">
                  {it.matched_product_id ? it.match_reason : "—"}
                </td>
                <td className="px-3 py-2.5 tabular-nums">{pct(it.match_confidence)}</td>
                <td className="px-3 py-2.5">{it.hs_code ?? "—"}</td>
                <td className="px-3 py-2.5 tabular-nums">
                  {it.import_duty != null ? it.import_duty : "—"}
                </td>
                <td className="px-3 py-2.5 tabular-nums">
                  {it.vat != null ? it.vat : "—"}
                </td>
                <td className="px-3 py-2.5">
                  {it.authorizations && it.authorizations.length > 0 ? (
                    <Badge variant="warning">{it.authorizations.length}</Badge>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-3 py-2.5">
                  {it.required_documents && it.required_documents.length > 0
                    ? it.required_documents.length
                    : "—"}
                </td>
                <td className="px-3 py-2.5 tabular-nums">
                  {it.purchase_count > 0 ? `${it.purchase_count} achat(s)` : "—"}
                </td>
                <td className="px-3 py-2.5">
                  <Badge variant={status.variant}>{status.label}</Badge>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
