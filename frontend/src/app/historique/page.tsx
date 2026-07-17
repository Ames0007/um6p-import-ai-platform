import { History } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/ui/empty-state";

export default function HistoriquePage() {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8">
      <PageHeader
        title="Historique des achats"
        description="Consultez les derniers prix d'achat et les fournisseurs utilisés."
      />
      <div className="mt-8">
        <EmptyState
          icon={History}
          title="Bientôt disponible"
          description="L'historique des achats (prix, fournisseurs et dates issus de PostgreSQL) sera activé dans une prochaine version."
        />
      </div>
    </div>
  );
}
