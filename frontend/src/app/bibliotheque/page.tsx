"use client";

import { Library, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { ImportDialog } from "@/components/documents/import-dialog";
import { DocumentTable } from "@/components/documents/document-table";
import { KnowledgeSearch } from "@/components/documents/knowledge-search";
import { useDocuments } from "@/hooks/use-documents";

export default function BibliothequePage() {
  const { data: documents, isLoading, isError } = useDocuments();

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8">
      <PageHeader
        title="Bibliothèque documentaire"
        description="Documentation douanière officielle — source unique de vérité de l'assistant."
        actions={<ImportDialog />}
      />

      <section className="mt-6">
        <KnowledgeSearch />
      </section>

      <section className="mt-10">
        <h2 className="mb-3 text-sm font-medium text-foreground">
          Documents importés
        </h2>

        {isLoading ? (
          <div className="flex items-center justify-center gap-2 rounded-2xl border border-dashed py-16 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> Chargement…
          </div>
        ) : isError ? (
          <EmptyState
            icon={Library}
            title="Impossible de charger la bibliothèque"
            description="Vérifiez que l'API est démarrée puis réessayez."
          />
        ) : !documents || documents.length === 0 ? (
          <EmptyState
            icon={Library}
            title="Aucun document"
            description="Importez les documents officiels de la douane marocaine (PDF, DOCX, XLSX, CSV ou ZIP) pour alimenter la base de connaissances."
            action={<ImportDialog />}
          />
        ) : (
          <DocumentTable documents={documents} />
        )}
      </section>
    </div>
  );
}
