"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type {
  DashboardResponse,
  GlobalSearchResponse,
  ImportPreview,
  ImportReport,
  Page,
  ResourceRecord,
} from "@/types/admin";

export interface ListParams {
  page?: number;
  size?: number;
  sort?: string;
  order?: "asc" | "desc";
  q?: string;
  filters?: Record<string, string>;
}

function buildQuery(params: ListParams): string {
  const sp = new URLSearchParams();
  if (params.page) sp.set("page", String(params.page));
  if (params.size) sp.set("size", String(params.size));
  if (params.sort) sp.set("sort", params.sort);
  if (params.order) sp.set("order", params.order);
  if (params.q) sp.set("q", params.q);
  for (const [k, v] of Object.entries(params.filters ?? {})) {
    if (v) sp.set(k, v);
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export function useResourceList(resource: string, params: ListParams) {
  return useQuery({
    queryKey: ["admin", resource, params],
    queryFn: () =>
      apiClient.get<Page<ResourceRecord>>(
        `${API_ENDPOINTS.admin.resource(resource)}${buildQuery(params)}`
      ),
  });
}

/** Options pour un champ de type "relation" (liste réduite). */
export function useResourceOptions(
  resource: string | undefined,
  labelKey: string
) {
  return useQuery({
    queryKey: ["admin-options", resource],
    enabled: !!resource,
    staleTime: 60_000,
    queryFn: async () => {
      const page = await apiClient.get<Page<ResourceRecord>>(
        `${API_ENDPOINTS.admin.resource(resource!)}?size=200`
      );
      return page.items.map((item) => ({
        value: String(item.id),
        label: String(item[labelKey] ?? item.id),
      }));
    },
  });
}

function useInvalidate(resource: string) {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: ["admin", resource] });
}

export function useCreateResource(resource: string) {
  const invalidate = useInvalidate(resource);
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      apiClient.post(API_ENDPOINTS.admin.resource(resource), body),
    onSuccess: invalidate,
  });
}

export function useUpdateResource(resource: string) {
  const invalidate = useInvalidate(resource);
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) =>
      apiClient.patch(API_ENDPOINTS.admin.resourceItem(resource, id), body),
    onSuccess: invalidate,
  });
}

export function useDeleteResource(resource: string) {
  const invalidate = useInvalidate(resource);
  return useMutation({
    mutationFn: (id: string) =>
      apiClient.delete<void>(API_ENDPOINTS.admin.resourceItem(resource, id)),
    onSuccess: invalidate,
  });
}

export function useDashboard() {
  return useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: () =>
      apiClient.get<DashboardResponse>(API_ENDPOINTS.admin.dashboard),
  });
}

export function useGlobalSearch(query: string) {
  const q = query.trim();
  return useQuery({
    queryKey: ["admin-global-search", q],
    enabled: q.length >= 2,
    queryFn: () =>
      apiClient.get<GlobalSearchResponse>(
        `${API_ENDPOINTS.admin.search}?q=${encodeURIComponent(q)}`
      ),
  });
}

export function useImportPreview() {
  return useMutation({
    mutationFn: ({ resource, file }: { resource: string; file: File }) => {
      const form = new FormData();
      form.append("resource", resource);
      form.append("file", file);
      return apiClient.post<ImportPreview>(
        API_ENDPOINTS.admin.importPreview,
        form
      );
    },
  });
}

export interface ImportCommitBody {
  token: string;
  resource: string;
  mapping: Record<string, string>;
  update_existing: boolean;
  dedup_field?: string | null;
  reason?: string;
}

export function useImportCommit() {
  return useMutation({
    mutationFn: (body: ImportCommitBody) =>
      apiClient.post<ImportReport>(API_ENDPOINTS.admin.importCommit, body),
  });
}
