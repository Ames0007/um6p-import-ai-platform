"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { RiskBadge } from "./risk-badge";
import type { AnalysisItem } from "@/types/compliance";

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 border-b py-1.5 text-sm last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value ?? "—"}</span>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      {children}
    </div>
  );
}

export function ItemDetailPanel({
  item,
  open,
  onOpenChange,
}: {
  item: AnalysisItem | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  if (!item) return null;

  // Mini-tendance de prix (min / moyen / max / dernier).
  const prices = [item.min_price, item.avg_price, item.max_price, item.last_price];
  const maxPrice = Math.max(1, ...prices.map((p) => p ?? 0));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{item.raw_product_name ?? "Ligne de facture"}</DialogTitle>
          <DialogDescription>Détail de la ligne #{item.line_number}</DialogDescription>
        </DialogHeader>

        <div className="space-y-5">
          <Section title="Texte original de la facture">
            <p className="rounded-lg bg-secondary px-3 py-2 text-xs text-muted-foreground">
              {item.raw_text ?? item.raw_product_name ?? "—"}
            </p>
          </Section>

          <Section title="Rapprochement produit">
            <Row
              label="Confiance"
              value={
                item.match_confidence != null
                  ? `${Math.round(item.match_confidence * 100)} %`
                  : "—"
              }
            />
            <Row label="Méthode" value={item.match_reason ?? item.match_method} />
          </Section>

          <Section title="Conformité douanière">
            <Row label="Code SH" value={item.hs_code} />
            <Row label="Droit d'importation" value={item.import_duty != null ? `${item.import_duty} %` : "—"} />
            <Row label="TVA" value={item.vat != null ? `${item.vat} %` : "—"} />
            <Row
              label="Taxe parafiscale"
              value={item.parafiscal_tax != null ? `${item.parafiscal_tax} %` : "—"}
            />
            {item.authorizations && item.authorizations.length > 0 && (
              <div className="pt-2">
                {item.authorizations.map((a, i) => (
                  <Badge key={i} variant="warning" className="mr-1">
                    {String((a as Record<string, unknown>).status ?? "autorisation")}
                  </Badge>
                ))}
              </div>
            )}
            {item.required_documents && item.required_documents.length > 0 && (
              <p className="pt-2 text-xs text-muted-foreground">
                Documents requis : {item.required_documents.join(", ")}
              </p>
            )}
          </Section>

          <Section title="Historique & prix">
            <Row label="Achats enregistrés" value={item.purchase_count || "—"} />
            <Row
              label="Prix facturé"
              value={item.raw_unit_price != null ? item.raw_unit_price : "—"}
            />
            <Row label="Prix moyen" value={item.avg_price ?? "—"} />
            <Row
              label="Dernier prix"
              value={
                item.last_price != null
                  ? `${item.last_price}${item.last_date ? ` (${item.last_date})` : ""}`
                  : "—"
              }
            />
            {item.price_variation_percent != null && (
              <div className="flex items-center gap-2 pt-2">
                <span className="text-sm text-muted-foreground">Écart de prix</span>
                <RiskBadge level={item.price_alert_level} />
                <span className="text-sm font-medium tabular-nums">
                  {item.price_variation_percent > 0 ? "+" : ""}
                  {item.price_variation_percent} %
                </span>
              </div>
            )}
            {item.purchase_count > 0 && (
              <div className="mt-3 space-y-1.5">
                {[
                  ["Min", item.min_price],
                  ["Moyen", item.avg_price],
                  ["Max", item.max_price],
                  ["Dernier", item.last_price],
                ].map(([label, val]) => (
                  <div key={label as string} className="flex items-center gap-2">
                    <span className="w-16 text-xs text-muted-foreground">{label}</span>
                    <div className="h-3 flex-1 overflow-hidden rounded bg-secondary">
                      <div
                        className="h-full rounded bg-primary"
                        style={{
                          width: `${((Number(val) || 0) / maxPrice) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="w-20 text-right text-xs tabular-nums">
                      {val ?? "—"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Section>
        </div>
      </DialogContent>
    </Dialog>
  );
}
