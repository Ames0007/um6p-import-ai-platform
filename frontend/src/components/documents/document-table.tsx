"use client";

import * as React from "react";
import {
  Download,
  Eye,
  FileWarning,
  Loader2,
  RotateCw,
  Trash2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { CATEGORY_LABELS, STATUS_META } from "@/lib/knowledge-labels";
import { formatDateFr, formatFileSize } from "@/lib/utils";
import { useDeleteDocument, useReimportDocument } from "@/hooks/use-documents";
import type { DocumentItem } from "@/types/knowledge";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function fileUrl(id: string, inline: boolean) {
  return `${API_BASE}${API_ENDPOINTS.documents.file(id, inline)}`;
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return "—";
  if (seconds < 60) return `${seconds.toFixed(1)} s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m} min ${s.toString().padStart(2, "0")} s`;
}

const HEADERS = [
  "Document",
  "Version",
  "Publication",
  "Import",
  "Statut",
  "Pages",
  "Codes SH",
  "Erreurs",
  "Durée",
  "Actions",
];

export function DocumentTable({ documents }: { documents: DocumentItem[] }) {
  const reimport = useReimportDocument();
  const remove = useDeleteDocument();

  return (
    <div className="overflow-x-auto rounded-2xl border">
      <table className="w-full min-w-[900px] border-collapse text-sm">
        <thead>
          <tr className="border-b bg-secondary/40 text-left text-xs font-medium text-muted-foreground">
            {HEADERS.map((h) => (
              <th key={h} className="whitespace-nowrap px-4 py-3">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => {
            const status = STATUS_META[doc.status];
            const processing = doc.status === "en_traitement";
            return (
              <tr
                key={doc.id}
                className="border-b last:border-0 hover:bg-secondary/30"
              >
                <td className="px-4 py-3">
                  <div className="font-medium text-foreground">{doc.title}</div>
                  <div className="text-xs text-muted-foreground">
                    {CATEGORY_LABELS[doc.category]}
                    {doc.size_bytes ? ` · ${formatFileSize(doc.size_bytes)}` : ""}
                    {doc.ocr_used ? " · OCR" : ""}
                  </div>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                  {doc.version ?? "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                  {doc.publication_date
                    ? formatDateFr(doc.publication_date)
                    : "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                  {formatDateFr(doc.upload_date)}
                </td>
                <td className="px-4 py-3">
                  <Badge variant={status.variant}>{status.label}</Badge>
                  {processing && (
                    <div className="mt-1.5 w-28">
                      <Progress value={doc.progress_percent} />
                      <span className="text-[11px] text-muted-foreground">
                        {doc.processed_pages}/{doc.number_of_pages}
                      </span>
                    </div>
                  )}
                  {doc.status === "erreur" && doc.error_message && (
                    <div className="mt-1 flex items-center gap-1 text-[11px] text-destructive">
                      <FileWarning className="size-3" />
                      <span className="max-w-[180px] truncate">
                        {doc.error_message}
                      </span>
                    </div>
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-3 tabular-nums">
                  {doc.number_of_pages}
                </td>
                <td className="whitespace-nowrap px-4 py-3 tabular-nums">
                  {doc.extracted_hs_count}
                </td>
                <td className="whitespace-nowrap px-4 py-3 tabular-nums">
                  {doc.extraction_errors_count > 0 ? (
                    <span className="text-amber-600">
                      {doc.extraction_errors_count}
                    </span>
                  ) : (
                    "0"
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                  {formatDuration(doc.processing_time_seconds)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <RowAction
                      label="Voir le document"
                      onClick={() =>
                        window.open(fileUrl(doc.id, true), "_blank")
                      }
                    >
                      <Eye className="size-4" />
                    </RowAction>
                    <RowAction
                      label="Télécharger"
                      onClick={() =>
                        window.open(fileUrl(doc.id, false), "_blank")
                      }
                    >
                      <Download className="size-4" />
                    </RowAction>
                    <RowAction
                      label="Réimporter"
                      disabled={reimport.isPending || processing}
                      onClick={() => reimport.mutate(doc.id)}
                    >
                      {reimport.isPending &&
                      reimport.variables === doc.id ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <RotateCw className="size-4" />
                      )}
                    </RowAction>
                    <RowAction
                      label="Supprimer"
                      destructive
                      disabled={remove.isPending}
                      onClick={() => {
                        if (
                          window.confirm(
                            `Supprimer « ${doc.title} » et ses données extraites ?`
                          )
                        )
                          remove.mutate(doc.id);
                      }}
                    >
                      <Trash2 className="size-4" />
                    </RowAction>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RowAction({
  label,
  onClick,
  disabled,
  destructive,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  destructive?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={destructive ? "text-muted-foreground hover:text-destructive" : "text-muted-foreground"}
          onClick={onClick}
          disabled={disabled}
          aria-label={label}
        >
          {children}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}
