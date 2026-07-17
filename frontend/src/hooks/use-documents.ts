"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type {
  DocumentItem,
  ImportDispatchResult,
  ImportRun,
} from "@/types/knowledge";

const DOCUMENTS_KEY = ["documents"] as const;

/** Liste des documents. Rafraîchit automatiquement tant qu'un import est actif. */
export function useDocuments() {
  return useQuery({
    queryKey: DOCUMENTS_KEY,
    queryFn: () => apiClient.get<DocumentItem[]>(API_ENDPOINTS.documents.list),
    refetchInterval: (query) => {
      const data = query.state.data as DocumentItem[] | undefined;
      const active = data?.some(
        (d) => d.status === "en_traitement" || d.status === "en_attente"
      );
      return active ? 2000 : false;
    },
  });
}

export interface ImportInput {
  file: File;
  title?: string;
  category?: string;
  version?: string;
  publicationDate?: string;
  allowDuplicate?: boolean;
}

/** Importe un document (ou une archive ZIP). */
export function useImportDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: ImportInput) => {
      const form = new FormData();
      form.append("file", input.file);
      if (input.title) form.append("title", input.title);
      if (input.category) form.append("category", input.category);
      if (input.version) form.append("version", input.version);
      if (input.publicationDate)
        form.append("publication_date", input.publicationDate);
      if (input.allowDuplicate) form.append("allow_duplicate", "true");
      return apiClient.post<ImportDispatchResult>(
        API_ENDPOINTS.documents.import,
        form
      );
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: DOCUMENTS_KEY }),
  });
}

export function useReimportDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.post(API_ENDPOINTS.documents.reimport(id)),
    onSuccess: () => qc.invalidateQueries({ queryKey: DOCUMENTS_KEY }),
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.delete<void>(API_ENDPOINTS.documents.byId(id)),
    onSuccess: () => qc.invalidateQueries({ queryKey: DOCUMENTS_KEY }),
  });
}

const TERMINAL_IMPORT: ImportRun["status"][] = [
  "reussi",
  "echoue",
  "partiel",
  "interrompu",
];

/** Progression d'un document (polling jusqu'à un état terminal). */
export function useDocumentProgress(id: string, enabled = true) {
  return useQuery({
    queryKey: ["document-progress", id],
    queryFn: () =>
      apiClient.get<ImportRun | null>(API_ENDPOINTS.documents.progress(id)),
    enabled,
    refetchInterval: (query) => {
      const run = query.state.data as ImportRun | null | undefined;
      if (run && TERMINAL_IMPORT.includes(run.status)) return false;
      return 1500;
    },
  });
}
