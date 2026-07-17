"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Hash, Package, FileText, BookOpen, Percent, ShieldCheck, Layers,
  Boxes, Sparkles, ArrowRight,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { KnowledgeResult, KnowledgeType } from "@/types/knowledge";

const TYPE_META: Record<KnowledgeType, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  HS_CODE: { label: "Code SH", icon: Hash },
  PRODUCT: { label: "Produit", icon: Package },
  DOCUMENT: { label: "Document", icon: FileText },
  CHAPTER: { label: "Chapitre", icon: BookOpen },
  SECTION: { label: "Section", icon: Layers },
  TAX: { label: "Taxes", icon: Percent },
  AUTHORIZATION: { label: "Autorisation", icon: ShieldCheck },
  SUPPLIER: { label: "Fournisseur", icon: Boxes },
};

function chapterNum(chapter: string | null): string | null {
  const d = (chapter || "").match(/(\d{1,2})/);
  return d ? d[1] : null;
}

function parseTaxes(taxes: string | null) {
  const di = taxes?.match(/DI\s*([\d.,]+)\s*%/i)?.[1] ?? null;
  const tva = taxes?.match(/TVA\s*([\d.,]+)\s*%/i)?.[1] ?? null;
  return { di, tva };
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-0.5 text-sm font-medium text-foreground">{value}</div>
    </div>
  );
}

interface ResultCardProps {
  result: KnowledgeResult;
  compact?: boolean;
}

/** Carte de résultat façon recherche d'entreprise (SAP Fiori). */
export function ResultCard({ result, compact = false }: ResultCardProps) {
  const router = useRouter();
  const meta = TYPE_META[result.type] ?? TYPE_META.HS_CODE;
  const Icon = meta.icon;
  const { di, tva } = parseTaxes(result.taxes);
  const chNum = chapterNum(result.chapter);
  const hasTaxData = Boolean(di || tva);
  // Un code SH / une entrée TAX devrait porter des droits & taxes ; leur absence
  // est signalée honnêtement plutôt que par un « — » ambigu ou une case masquée.
  const isTariffType = result.type === "HS_CODE" || result.type === "TAX";

  if (compact) {
    return (
      <button
        type="button"
        onClick={() => result.reference && router.push(`/recherche?q=${encodeURIComponent(result.reference)}`)}
        className="group flex items-center gap-3 rounded-xl border bg-card p-3 text-left shadow-sm transition-colors hover:border-primary/40 hover:bg-accent/40"
      >
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="size-4" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block font-mono text-sm font-semibold text-foreground">{result.reference}</span>
          <span className="block truncate text-xs text-muted-foreground">{result.title}</span>
        </span>
        {di && <Badge variant="secondary" className="shrink-0">DI {di}%</Badge>}
      </button>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-col gap-4 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="mb-2 flex items-center gap-2">
              <Badge variant="secondary" className="gap-1">
                <Icon className="size-3" /> {meta.label}
              </Badge>
              {result.chapter && <Badge variant="outline">{result.chapter}</Badge>}
              {result.section && <Badge variant="outline">Section {result.section}</Badge>}
            </div>
            {result.reference && (
              <div className="font-mono text-2xl font-semibold tracking-tight text-foreground">
                {result.reference}
              </div>
            )}
            <div className={cn("text-foreground", result.reference ? "mt-1 text-base" : "text-xl font-semibold")}>
              {result.title}
            </div>
            {result.description && result.description !== result.title && (
              <p className="mt-1 text-sm text-muted-foreground">{result.description}</p>
            )}
          </div>
        </div>

        {(hasTaxData || result.authorizations || isTariffType) && (
          <div className="rounded-xl border bg-muted/40 p-4">
            {hasTaxData ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                <Field label="Droit d'importation" value={di ? `${di} %` : "—"} />
                <Field label="TVA" value={tva ? `${tva} %` : "—"} />
                <Field
                  label="Autorisations"
                  value={result.authorizations ?? "Non renseignée"}
                />
              </div>
            ) : (
              <div className="space-y-3">
                {isTariffType && (
                  <p className="text-sm text-muted-foreground">
                    <span className="font-medium text-foreground">
                      Droits &amp; taxes&nbsp;:
                    </span>{" "}
                    non disponibles dans la base documentaire actuelle (nomenclature
                    de classement, sans taux tarifaires). Consultez le tarif officiel
                    de l&apos;ADII pour les droits d&apos;importation et la TVA.
                  </p>
                )}
                <Field
                  label="Autorisations"
                  value={result.authorizations ?? "Non renseignée"}
                />
              </div>
            )}
          </div>
        )}

        {result.document_title && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="size-4" />
            <span>
              Source&nbsp;: <span className="font-medium text-foreground">{result.document_title}</span>
              {result.page != null && ` — Page ${result.page}`}
            </span>
          </div>
        )}

        <div className="flex flex-wrap gap-2 pt-1">
          {result.document_title && (
            <Button variant="outline" size="sm" onClick={() => router.push("/bibliotheque")}>
              <FileText /> Voir le document
            </Button>
          )}
          {chNum && (
            <Button variant="outline" size="sm" onClick={() => router.push(`/recherche?q=${encodeURIComponent("Chapitre " + chNum)}`)}>
              <BookOpen /> Voir le chapitre
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={() => router.push("/produits")}>
            <Boxes /> Produits associés
          </Button>
          {result.reference && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push(`/conversation?q=${encodeURIComponent("Explique le code SH " + result.reference + " et ses exigences d'importation.")}`)}
            >
              <Sparkles /> Expliquer avec l&apos;IA <ArrowRight />
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
