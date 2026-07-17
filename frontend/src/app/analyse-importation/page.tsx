"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/layout/page-header";
import { FileDropzone } from "@/components/upload/file-dropzone";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AnalysisHistory } from "@/components/compliance/analysis-history";
import { useUploadInvoices } from "@/hooks/use-analyses";

const INVOICE_EXT = [
  ".pdf", ".docx", ".xlsx", ".csv", ".png", ".jpg", ".jpeg", ".tif", ".tiff",
] as const;
const INVOICE_MIME = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "text/csv",
  "image/png",
  "image/jpeg",
  "image/tiff",
];

export default function AnalyseImportationPage() {
  const router = useRouter();
  const [files, setFiles] = React.useState<File[]>([]);
  const upload = useUploadInvoices();

  const launch = async () => {
    if (files.length === 0) return;
    const res = await upload.mutateAsync(files);
    setFiles([]);
    if (res.analyses.length === 1) {
      router.push(`/analyse-importation/${res.analyses[0].id}`);
    }
  };

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8">
      <PageHeader
        title="Analyse d'importation"
        description="Analysez automatiquement les factures fournisseurs avant importation : OCR, rapprochement produit, taxes, autorisations et conformité."
      />

      <Card className="mt-6 p-5">
        <FileDropzone
          files={files}
          onFilesSelected={(f) => setFiles((prev) => [...prev, ...f])}
          onRemove={(i) => setFiles((prev) => prev.filter((_, idx) => idx !== i))}
          extensions={INVOICE_EXT}
          mimeTypes={INVOICE_MIME}
          maxSizeMb={50}
          hint="PDF, Excel, Word, CSV (texte) analysés directement. Images et PDF scannés : OCR requis (non activé sur cette instance)."
        />
        {files.length > 0 && (
          <div className="mt-4 flex justify-end">
            <Button onClick={launch} disabled={upload.isPending}>
              {upload.isPending
                ? "Envoi en cours…"
                : `Analyser ${files.length} facture(s)`}
            </Button>
          </div>
        )}
      </Card>

      <section className="mt-10">
        <h2 className="mb-3 text-sm font-medium text-foreground">
          Analyses récentes
        </h2>
        <AnalysisHistory />
      </section>
    </div>
  );
}
