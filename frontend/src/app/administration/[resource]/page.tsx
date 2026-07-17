"use client";

import { useParams } from "next/navigation";
import { DataTable } from "@/components/admin/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { ADMIN_RESOURCES } from "@/config/admin-resources";
import { PackageX } from "lucide-react";

export default function AdminResourcePage() {
  const params = useParams();
  const key = String(params.resource);
  const resource = ADMIN_RESOURCES[key];

  if (!resource) {
    return (
      <EmptyState
        icon={PackageX}
        title="Section inconnue"
        description="Cette section d'administration n'existe pas."
      />
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">{resource.label}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Gestion des enregistrements — {resource.label.toLowerCase()}.
        </p>
      </div>
      <DataTable resource={resource} />
    </div>
  );
}
