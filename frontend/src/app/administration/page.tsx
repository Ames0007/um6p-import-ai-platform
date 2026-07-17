"use client";

import {
  Boxes,
  FileText,
  Flag,
  Hash,
  Library,
  Loader2,
  Receipt,
  ShoppingCart,
  Tags,
  Truck,
} from "lucide-react";
import { StatCard } from "@/components/admin/stat-card";
import { BarChart } from "@/components/admin/bar-chart";
import { GlobalSearch } from "@/components/admin/global-search";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useDashboard } from "@/hooks/use-admin";

const AUDIT_LABELS: Record<string, string> = {
  creation: "Création",
  modification: "Modification",
  suppression: "Suppression",
  import: "Import",
};

export default function AdminDashboardPage() {
  const { data, isLoading } = useDashboard();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Tableau de bord
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Base de connaissances achats & import — vue d&apos;ensemble.
        </p>
      </div>

      <GlobalSearch />

      {isLoading || !data ? (
        <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> Chargement…
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatCard label="Produits" value={data.cards.products} icon={Boxes} />
            <StatCard label="Codes SH" value={data.cards.hs_codes} icon={Hash} />
            <StatCard label="Fournisseurs" value={data.cards.suppliers} icon={Truck} />
            <StatCard label="Factures" value={data.cards.invoices} icon={Receipt} />
            <StatCard label="Achats" value={data.cards.purchases} icon={ShoppingCart} />
            <StatCard label="Pays" value={data.cards.countries} icon={Flag} />
            <StatCard label="Documents" value={data.cards.documents} icon={Library} />
            <StatCard label="Alias" value={data.cards.aliases} icon={Tags} />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <BarChart title="Produits par catégorie" data={data.products_by_category} />
            <BarChart title="Achats par pays" data={data.purchases_by_country} />
            <BarChart title="Achats par fournisseur" data={data.purchases_by_supplier} />
            <BarChart title="Codes SH les plus utilisés" data={data.top_hs_codes} />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card className="p-5">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-medium">
                <FileText className="size-4 text-primary" /> Imports récents
              </h3>
              {data.recent_imports.length === 0 ? (
                <p className="text-xs text-muted-foreground">Aucun import.</p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {data.recent_imports.map((imp, i) => (
                    <li key={i} className="flex items-center justify-between gap-2">
                      <span className="truncate">{imp.document_title}</span>
                      <Badge variant="secondary">{imp.status}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card className="p-5">
              <h3 className="mb-3 text-sm font-medium">Modifications récentes</h3>
              {data.recent_modifications.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  Aucune modification enregistrée.
                </p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {data.recent_modifications.map((log) => (
                    <li
                      key={log.id}
                      className="flex items-center justify-between gap-2"
                    >
                      <span className="truncate">
                        <span className="font-medium">
                          {AUDIT_LABELS[log.action] ?? log.action}
                        </span>{" "}
                        <span className="text-muted-foreground">
                          · {log.entity_type}
                        </span>
                      </span>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {log.actor}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
