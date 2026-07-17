"use client";

import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { useDocumentProgress } from "@/hooks/use-documents";

interface ImportProgressItemProps {
  documentId: string;
  title: string;
}

/** Progression temps réel d'un document en cours d'ingestion. */
export function ImportProgressItem({
  documentId,
  title,
}: ImportProgressItemProps) {
  const { data: run } = useDocumentProgress(documentId);

  const total = run?.total_pages ?? 0;
  const current = run?.current_page ?? 0;
  const percent = total > 0 ? Math.round((100 * current) / total) : 0;
  const done = run?.status === "reussi";
  const failed = run?.status === "echoue";
  const errorsCount = run?.errors?.length ?? 0;

  return (
    <div className="rounded-xl border bg-card p-3">
      <div className="mb-2 flex items-center gap-2">
        {done ? (
          <CheckCircle2 className="size-4 text-emerald-600" />
        ) : failed ? (
          <AlertTriangle className="size-4 text-destructive" />
        ) : (
          <Loader2 className="size-4 animate-spin text-primary" />
        )}
        <span className="min-w-0 flex-1 truncate text-sm font-medium">
          {title}
        </span>
        <span className="text-xs text-muted-foreground">{percent}%</span>
      </div>
      <Progress value={percent} />
      <p className="mt-1.5 text-xs text-muted-foreground">
        {failed
          ? run?.message ?? "Échec de l'ingestion."
          : done
            ? `Terminé — ${total} page(s)` +
              (errorsCount ? ` · ${errorsCount} erreur(s)` : "")
            : run?.message ?? "Analyse en cours…"}
      </p>
    </div>
  );
}
