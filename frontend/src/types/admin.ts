/** Types de la plateforme de gestion des connaissances (Phase 3). */

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AuditLog {
  id: string;
  entity_type: string;
  entity_id: string | null;
  action: "creation" | "modification" | "suppression" | "import";
  actor: string;
  changes: Record<string, { old: unknown; new: unknown }> | null;
  reason: string | null;
  created_at: string;
}

export interface DashboardCards {
  products: number;
  hs_codes: number;
  suppliers: number;
  invoices: number;
  purchases: number;
  countries: number;
  documents: number;
  aliases: number;
}

export interface ChartPoint {
  label: string;
  value: number;
}

export interface RecentImport {
  document_title: string;
  status: string;
  when: string | null;
}

export interface DashboardResponse {
  cards: DashboardCards;
  products_by_category: ChartPoint[];
  purchases_by_country: ChartPoint[];
  purchases_by_supplier: ChartPoint[];
  top_hs_codes: ChartPoint[];
  recent_imports: RecentImport[];
  recent_modifications: AuditLog[];
}

export interface SearchEntity {
  id: string;
  label: string;
  sublabel: string | null;
}

export interface GlobalSearchResponse {
  query: string;
  products: SearchEntity[];
  aliases: SearchEntity[];
  hs_codes: SearchEntity[];
  suppliers: SearchEntity[];
  purchases: SearchEntity[];
  authorizations: SearchEntity[];
}

export interface TargetField {
  name: string;
  label: string;
  required: boolean;
}

export interface ImportPreview {
  token: string;
  resource: string;
  columns: string[];
  sample_rows: Record<string, string>[];
  total_rows: number;
  target_fields: TargetField[];
  suggested_mapping: Record<string, string>;
}

export interface ImportReport {
  resource: string;
  total: number;
  created: number;
  updated: number;
  skipped: number;
  errors: { row: number; message: string }[];
}

/** Enregistrement générique renvoyé par les endpoints CRUD. */
export type ResourceRecord = Record<string, unknown> & {
  id: string;
  created_at: string;
  updated_at: string;
};
