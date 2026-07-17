import Link from "next/link";
import { FileSearch, ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

/**
 * L'analyse de factures est fournie par le module « Analyse d'importation ».
 * Cette page conserve l'URL /factures (liens/marque-pages) et oriente
 * l'utilisateur vers la fonctionnalité opérationnelle — pas de cul-de-sac.
 */
export default function FacturesPage() {
  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8">
      <PageHeader
        title="Factures"
        description="L'analyse de factures est intégrée au module « Analyse d'importation »."
      />

      <Card className="mt-6 flex flex-col items-start gap-4 p-6">
        <span className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <FileSearch className="size-5" />
        </span>
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Analyser une facture
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Téléversez vos factures fournisseurs dans « Analyse d&apos;importation » :
            extraction des lignes, rapprochement des codes SH, taxes, autorisations
            et rapport de conformité.
          </p>
        </div>
        <Button asChild>
          <Link href="/analyse-importation">
            Aller à l&apos;analyse d&apos;importation <ArrowRight className="size-4" />
          </Link>
        </Button>
      </Card>
    </div>
  );
}
