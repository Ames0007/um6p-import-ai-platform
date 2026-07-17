"use client";

import { ImportWizard } from "@/components/admin/import-wizard";

export default function AdminImportPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">
          Assistant d&apos;import
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Importez vos données (Excel ou CSV) : aperçu, correspondance des
          colonnes, détection des doublons et rapport d&apos;import.
        </p>
      </div>
      <ImportWizard />
    </div>
  );
}
