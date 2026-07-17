"use client";

import * as React from "react";
import { AlertTriangle, CheckCircle2, FileSpreadsheet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FileDropzone } from "@/components/upload/file-dropzone";
import { ADMIN_RESOURCES, ADMIN_SECTIONS } from "@/config/admin-resources";
import {
  useImportCommit,
  useImportPreview,
  type ImportCommitBody,
} from "@/hooks/use-admin";
import type { ImportPreview, ImportReport } from "@/types/admin";

const selectClass =
  "h-9 w-full rounded-lg border border-input bg-background px-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";
const IMPORT_EXT = [".csv", ".xlsx"] as const;
const IMPORT_MIME = [
  "text/csv",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
];

export function ImportWizard() {
  const [resource, setResource] = React.useState<string>(ADMIN_SECTIONS[0]);
  const [files, setFiles] = React.useState<File[]>([]);
  const [preview, setPreview] = React.useState<ImportPreview | null>(null);
  const [mapping, setMapping] = React.useState<Record<string, string>>({});
  const [updateExisting, setUpdateExisting] = React.useState(true);
  const [report, setReport] = React.useState<ImportReport | null>(null);

  const previewM = useImportPreview();
  const commitM = useImportCommit();

  const runPreview = async () => {
    if (!files[0]) return;
    const res = await previewM.mutateAsync({ resource, file: files[0] });
    setPreview(res);
    setMapping(res.suggested_mapping ?? {});
    setReport(null);
  };

  const runCommit = async () => {
    if (!preview) return;
    const cleanMapping = Object.fromEntries(
      Object.entries(mapping).filter(([, target]) => target)
    );
    const body: ImportCommitBody = {
      token: preview.token,
      resource: preview.resource,
      mapping: cleanMapping,
      update_existing: updateExisting,
    };
    const res = await commitM.mutateAsync(body);
    setReport(res);
  };

  const reset = () => {
    setPreview(null);
    setFiles([]);
    setReport(null);
    setMapping({});
  };

  return (
    <div className="space-y-6">
      {/* Étape 1 — sélection */}
      {!preview && (
        <Card className="space-y-4 p-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium">
              Type de données
            </label>
            <select
              className={selectClass + " sm:max-w-xs"}
              value={resource}
              onChange={(e) => setResource(e.target.value)}
            >
              {ADMIN_SECTIONS.map((name) => (
                <option key={name} value={name}>
                  {ADMIN_RESOURCES[name].label}
                </option>
              ))}
            </select>
          </div>

          <FileDropzone
            files={files}
            onFilesSelected={(f) => setFiles(f.slice(0, 1))}
            onRemove={() => setFiles([])}
            multiple={false}
            extensions={IMPORT_EXT}
            mimeTypes={IMPORT_MIME}
            hint="Excel (.xlsx) ou CSV"
          />

          <div className="flex justify-end">
            <Button
              onClick={runPreview}
              disabled={files.length === 0 || previewM.isPending}
            >
              {previewM.isPending ? "Analyse…" : "Analyser le fichier"}
            </Button>
          </div>
        </Card>
      )}

      {/* Étape 2 — mapping + aperçu */}
      {preview && !report && (
        <div className="space-y-5">
          <Card className="p-5">
            <div className="mb-3 flex items-center gap-2 text-sm">
              <FileSpreadsheet className="size-4 text-primary" />
              <span className="font-medium">
                {preview.total_rows} ligne(s) détectée(s)
              </span>
              <span className="text-muted-foreground">
                · {preview.columns.length} colonne(s)
              </span>
            </div>

            <h4 className="mb-2 text-sm font-medium">Correspondance des colonnes</h4>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {preview.columns.map((col) => (
                <div key={col} className="flex items-center gap-2">
                  <span
                    className="w-1/2 truncate text-sm text-muted-foreground"
                    title={col}
                  >
                    {col}
                  </span>
                  <select
                    className={selectClass}
                    value={mapping[col] ?? ""}
                    onChange={(e) =>
                      setMapping((prev) => ({ ...prev, [col]: e.target.value }))
                    }
                  >
                    <option value="">— Ignorer —</option>
                    {preview.target_fields.map((tf) => (
                      <option key={tf.name} value={tf.name}>
                        {tf.label}
                        {tf.required ? " *" : ""}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            <label className="mt-4 flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={updateExisting}
                onChange={(e) => setUpdateExisting(e.target.checked)}
                className="size-4 accent-[color:hsl(var(--primary))]"
              />
              Mettre à jour les enregistrements existants (sans créer de doublon)
            </label>
          </Card>

          {preview.sample_rows.length > 0 && (
            <Card className="p-5">
              <h4 className="mb-2 text-sm font-medium">Aperçu (10 premières lignes)</h4>
              <div className="overflow-x-auto rounded-xl border">
                <table className="w-full min-w-[600px] text-xs">
                  <thead>
                    <tr className="border-b bg-secondary/40 text-left text-muted-foreground">
                      {preview.columns.map((c) => (
                        <th key={c} className="px-3 py-2 font-medium">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.sample_rows.map((row, i) => (
                      <tr key={i} className="border-b last:border-0">
                        {preview.columns.map((c) => (
                          <td key={c} className="px-3 py-1.5">
                            {row[c] ?? ""}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          <div className="flex justify-between">
            <Button variant="outline" onClick={reset}>
              Recommencer
            </Button>
            <Button onClick={runCommit} disabled={commitM.isPending}>
              {commitM.isPending ? "Import en cours…" : "Lancer l'import"}
            </Button>
          </div>
        </div>
      )}

      {/* Étape 3 — rapport */}
      {report && (
        <Card className="space-y-4 p-5">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="size-5 text-emerald-600" />
            <h3 className="text-base font-semibold">Rapport d&apos;import</h3>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "Total", value: report.total },
              { label: "Créés", value: report.created },
              { label: "Mis à jour", value: report.updated },
              { label: "Ignorés", value: report.skipped },
            ].map((s) => (
              <div key={s.label} className="rounded-xl border bg-secondary/30 p-3">
                <div className="text-2xl font-semibold tabular-nums">
                  {s.value}
                </div>
                <div className="text-xs text-muted-foreground">{s.label}</div>
              </div>
            ))}
          </div>

          {report.errors.length > 0 && (
            <div>
              <p className="mb-2 flex items-center gap-1.5 text-sm font-medium text-amber-600">
                <AlertTriangle className="size-4" />
                {report.errors.length} erreur(s)
              </p>
              <ul className="max-h-48 space-y-1 overflow-y-auto text-xs text-muted-foreground">
                {report.errors.map((e, i) => (
                  <li key={i}>
                    Ligne {e.row} : {e.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex justify-end">
            <Button onClick={reset}>Nouvel import</Button>
          </div>
        </Card>
      )}
    </div>
  );
}
