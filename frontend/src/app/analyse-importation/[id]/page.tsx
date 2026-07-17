"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  Download,
  Loader2,
  Lightbulb,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RiskBadge } from "@/components/compliance/risk-badge";
import { ResultsTable } from "@/components/compliance/results-table";
import { ItemDetailPanel } from "@/components/compliance/item-detail-panel";
import { BarChart } from "@/components/admin/bar-chart";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { useAnalysisDetail } from "@/hooks/use-analyses";
import type { AnalysisItem } from "@/types/compliance";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export default function AnalysisDetailPage() {
  const params = useParams();
  const id = String(params.id);
  const { data, isLoading, isError, refetch } = useAnalysisDetail(id);
  const [selected, setSelected] = React.useState<AnalysisItem | null>(null);
  const [open, setOpen] = React.useState(false);

  if (isLoading) {
    return (
      <div className="mx-auto flex max-w-6xl items-center justify-center gap-2 px-4 py-20 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" /> Chargement de l&apos;analyse…
      </div>
    );
  }

  // Ne jamais rester bloqué sur le spinner : id inconnu / supprimé ou API indisponible.
  if (isError || !data) {
    return (
      <div className="mx-auto flex max-w-lg flex-col items-center justify-center gap-4 px-4 py-20 text-center">
        <span className="flex size-12 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
          <AlertTriangle className="size-6" />
        </span>
        <div>
          <h2 className="text-base font-semibold text-foreground">Analyse introuvable</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Cette analyse n&apos;a pas pu être chargée. Elle a peut-être été supprimée,
            ou le service est momentanément indisponible.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            Réessayer
          </Button>
          <Button asChild>
            <Link href="/analyse-importation">Retour aux analyses</Link>
          </Button>
        </div>
      </div>
    );
  }

  const active = data.status === "en_cours" || data.status === "en_attente";
  const report = data.report;
  const isLikelyImage = /\.(png|jpe?g|tiff?|webp)$/i.test(data.original_filename ?? "");

  const priceChart =
    report?.price_comparison?.map((p) => ({
      label: String(p.product ?? "—").slice(0, 18),
      value: Number(p.invoice_price ?? 0),
    })) ?? [];
  const variationChart =
    report?.price_comparison
      ?.filter((p) => p.variation_percent != null)
      .map((p) => ({
        label: String(p.product ?? "—").slice(0, 18),
        value: Math.abs(Number(p.variation_percent ?? 0)),
      })) ?? [];

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8">
      <Link
        href="/analyse-importation"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-4" /> Retour aux analyses
      </Link>

      {/* En-tête + exports */}
      <div className="flex flex-col gap-3 border-b pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {data.invoice_number ?? data.original_filename}
          </h1>
          <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span>{data.supplier_name_raw ?? "Fournisseur inconnu"}</span>
            {data.currency && <span>· {data.currency}</span>}
            {data.incoterm && <span>· {data.incoterm}</span>}
            {data.invoice_date && <span>· {data.invoice_date}</span>}
          </p>
          <div className="mt-2 flex items-center gap-2">
            <RiskBadge level={data.overall_risk} />
            {data.confidence && (
              <Badge variant="secondary">Confiance : {data.confidence}</Badge>
            )}
            {active && (
              <Badge variant="warning">
                <Loader2 className="mr-1 size-3 animate-spin" /> En cours (
                {data.processed_items}/{data.total_items})
              </Badge>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {(["pdf", "xlsx", "csv"] as const).map((fmt) => (
            <Button key={fmt} variant="outline" size="sm" asChild>
              <a
                href={`${API_BASE}${API_ENDPOINTS.analysis.export(id, fmt)}`}
                target="_blank"
                rel="noreferrer"
              >
                <Download className="size-4" /> {fmt.toUpperCase()}
              </a>
            </Button>
          ))}
        </div>
      </div>

      {data.summary && (
        <p className="mt-4 rounded-xl bg-secondary/40 px-4 py-3 text-sm">
          {data.summary}
        </p>
      )}

      {/* Produits détectés */}
      <section className="mt-6">
        <h2 className="mb-3 text-sm font-medium">Produits détectés</h2>
        {data.items.length > 0 ? (
          <ResultsTable
            items={data.items}
            onSelect={(it) => {
              setSelected(it);
              setOpen(true);
            }}
          />
        ) : active ? (
          <p className="rounded-xl border border-dashed bg-secondary/30 px-4 py-8 text-center text-sm text-muted-foreground">
            Analyse en cours…
          </p>
        ) : (
          <div className="rounded-xl border border-dashed border-amber-300/70 bg-amber-50 px-4 py-6 text-sm text-amber-900 dark:border-amber-500/40 dark:bg-amber-950/40 dark:text-amber-100">
            <p className="flex items-center gap-2 font-medium">
              <AlertTriangle className="size-4 shrink-0" />
              Aucune ligne produit n&apos;a pu être extraite de ce document.
            </p>
            <p className="mt-1.5 text-amber-800 dark:text-amber-200/90">
              {isLikelyImage
                ? "Ce fichier est une image : la reconnaissance de caractères (OCR) est requise pour l'analyser, et l'OCR n'est pas activé sur cette instance."
                : "Si votre facture est une image ou un PDF scanné, l'OCR est requis (non activé sur cette instance). Vérifiez que le document contient du texte sélectionnable, puis relancez l'analyse."}
            </p>
          </div>
        )}
      </section>

      {/* Graphiques */}
      {priceChart.length > 0 && (
        <section className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <BarChart title="Prix facturés par produit" data={priceChart} />
          {variationChart.length > 0 && (
            <BarChart title="Écart de prix (%) par produit" data={variationChart} />
          )}
        </section>
      )}

      {/* Conformité + recommandations */}
      <section className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-medium">
            <AlertTriangle className="size-4 text-primary" /> Avertissements
          </h3>
          {report?.warnings && report.warnings.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {report.warnings.map((w, i) => (
                <li key={i} className="flex items-start gap-2">
                  <RiskBadge level={w.risk as never} />
                  <span>{w.message}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-muted-foreground">Aucun avertissement.</p>
          )}
        </Card>

        <Card className="p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-medium">
            <Lightbulb className="size-4 text-primary" /> Recommandations
          </h3>
          {report?.recommendations && report.recommendations.length > 0 ? (
            <ul className="list-inside list-disc space-y-1 text-sm">
              {report.recommendations.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-muted-foreground">Aucune recommandation.</p>
          )}
        </Card>
      </section>

      {/* Sources & citations */}
      {report && (report.sources?.length || report.citations?.length) ? (
        <section className="mt-8">
          <h3 className="mb-2 text-sm font-medium">Sources & références officielles</h3>
          <div className="flex flex-wrap gap-1.5">
            {report.sources?.map((s, i) => (
              <Badge key={i} variant="secondary">
                {s}
              </Badge>
            ))}
          </div>
          {report.citations && report.citations.length > 0 && (
            <div className="mt-3 space-y-1">
              {report.citations.map((c, i) => (
                <div
                  key={i}
                  className="flex items-center gap-1.5 text-xs text-muted-foreground"
                >
                  <FileText className="size-3.5 text-primary" />
                  <span className="font-medium text-foreground">Source :</span>
                  <span>{c.document_title}</span>
                  {c.chapter && <span>· {c.chapter}</span>}
                  {c.page != null && <span>· Page {c.page}</span>}
                </div>
              ))}
            </div>
          )}
        </section>
      ) : null}

      <ItemDetailPanel item={selected} open={open} onOpenChange={setOpen} />
    </div>
  );
}
