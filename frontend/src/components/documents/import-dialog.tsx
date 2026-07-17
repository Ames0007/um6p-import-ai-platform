"use client";

import * as React from "react";
import { Upload, AlertCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { FileDropzone } from "@/components/upload/file-dropzone";
import { ImportProgressItem } from "./import-progress-item";
import { CATEGORY_OPTIONS } from "@/lib/knowledge-labels";
import { useImportDocument } from "@/hooks/use-documents";
import { ApiError } from "@/lib/api/client";

const IMPORT_EXTENSIONS = [".pdf", ".docx", ".xlsx", ".csv", ".zip"] as const;
const IMPORT_MIME: readonly string[] = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "text/csv",
  "application/zip",
  "application/x-zip-compressed",
];

interface Started {
  id: string;
  title: string;
}

export function ImportDialog({ trigger }: { trigger?: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);
  const [files, setFiles] = React.useState<File[]>([]);
  const [category, setCategory] = React.useState<string>("");
  const [started, setStarted] = React.useState<Started[]>([]);
  const [duplicates, setDuplicates] = React.useState<string[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  const importDoc = useImportDocument();

  const reset = () => {
    setFiles([]);
    setCategory("");
    setStarted([]);
    setDuplicates([]);
    setError(null);
  };

  const handleImport = async () => {
    setError(null);
    setDuplicates([]);
    const collectedDups: string[] = [];
    const collectedStarted: Started[] = [];

    for (const file of files) {
      try {
        const res = await importDoc.mutateAsync({
          file,
          category: category || undefined,
        });
        res.documents.forEach((d) =>
          collectedStarted.push({ id: d.id, title: d.title })
        );
        collectedDups.push(...res.duplicates);
      } catch (e) {
        if (e instanceof ApiError && e.status === 409) {
          collectedDups.push(file.name);
        } else {
          setError(
            e instanceof ApiError
              ? `Échec de l'import : ${file.name}`
              : "Une erreur est survenue pendant l'import."
          );
        }
      }
    }
    setStarted(collectedStarted);
    setDuplicates(collectedDups);
    setFiles([]);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (!v) reset();
      }}
    >
      <DialogTrigger asChild>
        {trigger ?? (
          <Button>
            <Upload className="size-4" />
            Importer
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Importer des documents</DialogTitle>
          <DialogDescription>
            PDF, DOCX, XLSX, CSV ou archive ZIP de PDF. L&apos;ingestion démarre
            automatiquement en arrière-plan.
          </DialogDescription>
        </DialogHeader>

        {started.length === 0 ? (
          <div className="space-y-4">
            <FileDropzone
              files={files}
              onFilesSelected={(f) => setFiles((prev) => [...prev, ...f])}
              onRemove={(i) =>
                setFiles((prev) => prev.filter((_, idx) => idx !== i))
              }
              extensions={IMPORT_EXTENSIONS}
              mimeTypes={IMPORT_MIME}
              maxSizeMb={500}
              hint="PDF, DOCX, XLSX, CSV, ZIP · max 500 Mo"
            />

            <div>
              <label
                htmlFor="doc-category"
                className="mb-1.5 block text-sm font-medium"
              >
                Catégorie{" "}
                <span className="text-muted-foreground">(optionnel)</span>
              </label>
              <select
                id="doc-category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">Détection automatique</option>
                {CATEGORY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {error && (
              <p className="flex items-center gap-1.5 text-sm text-destructive">
                <AlertCircle className="size-4" /> {error}
              </p>
            )}

            <div className="flex justify-end gap-2">
              <Button
                onClick={handleImport}
                disabled={files.length === 0 || importDoc.isPending}
              >
                {importDoc.isPending
                  ? "Import en cours…"
                  : `Importer ${files.length || ""}`.trim()}
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Ingestion en cours — vous pouvez fermer cette fenêtre, le
              traitement continue en arrière-plan.
            </p>
            <div className="max-h-72 space-y-2 overflow-y-auto">
              {started.map((s) => (
                <ImportProgressItem
                  key={s.id}
                  documentId={s.id}
                  title={s.title}
                />
              ))}
            </div>
            {duplicates.length > 0 && (
              <p className="text-xs text-amber-600">
                Ignoré(s) (doublon) : {duplicates.join(", ")}
              </p>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={reset}>
                Importer d&apos;autres documents
              </Button>
              <Button onClick={() => setOpen(false)}>Terminer</Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
