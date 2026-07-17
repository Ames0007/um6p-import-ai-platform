/** Types du moteur d'ingestion et de la base de connaissances (Phase 2). */

export type DocumentStatus =
  | "en_attente"
  | "en_traitement"
  | "termine"
  | "partiel"
  | "erreur"
  | "doublon";

export type ImportStatus =
  | "en_cours"
  | "reussi"
  | "partiel"
  | "echoue"
  | "interrompu";

export type DocumentCategory =
  | "code_des_douanes"
  | "nomenclature_douaniere"
  | "produits_chimiques"
  | "engrais"
  | "machines_et_appareils"
  | "matieres_plastiques"
  | "produits_controles"
  | "circulaires"
  | "annexes_reglementaires"
  | "autre";

export interface ImportRun {
  id: string;
  status: ImportStatus;
  start_time: string | null;
  end_time: string | null;
  current_page: number;
  total_pages: number;
  message: string | null;
  errors: Array<{ page: number | null; message: string }> | null;
  stats: Record<string, number> | null;
  duration_seconds: number | null;
}

export interface DocumentItem {
  id: string;
  title: string;
  filename: string;
  category: DocumentCategory;
  version: string | null;
  publication_date: string | null;
  upload_date: string;
  number_of_pages: number;
  processed_pages: number;
  language: string;
  status: DocumentStatus;
  checksum: string;
  mime_type: string | null;
  size_bytes: number | null;
  is_scanned: boolean;
  ocr_used: boolean;
  error_message: string | null;
  extracted_hs_count: number;
  extraction_errors_count: number;
  processing_time_seconds: number | null;
  progress_percent: number;
  last_import: ImportRun | null;
}

export interface ImportDispatchResult {
  documents: DocumentItem[];
  mode: "queued" | "inline";
  duplicates: string[];
}

export interface Citation {
  document_id: string;
  document_title: string;
  chapter: string | null;
  section: string | null;
  page: number | null;
}

export interface SearchHit {
  chunk_id: string;
  excerpt: string;
  score: number | null;
  hs_codes: string[];
  citation: Citation;
}

export interface SearchResponse {
  query: string;
  mode: "semantique" | "texte";
  total: number;
  hits: SearchHit[];
}

/** Index de connaissance unifié (recherche par concept, sans IA). */
export type KnowledgeType =
  | "HS_CODE"
  | "PRODUCT"
  | "CHAPTER"
  | "SECTION"
  | "DOCUMENT"
  | "SUPPLIER"
  | "AUTHORIZATION"
  | "TAX";

export interface KnowledgeResult {
  id: string;
  type: KnowledgeType;
  reference: string | null;
  title: string | null;
  chapter: string | null;
  section: string | null;
  document_id: string | null;
  document_title: string | null;
  page: number | null;
  description: string | null;
  taxes: string | null;
  authorizations: string | null;
  source_table: string;
  source_pk: string | null;
  score: number;
}

export type LookupMode =
  | "exact_hs"
  | "chapter"
  | "hs_code"
  | "product"
  | "document"
  | "ranked"
  | "empty";

export interface LookupResponse {
  query: string;
  mode: LookupMode;
  results: KnowledgeResult[];
  chapter_codes: KnowledgeResult[];
}

export interface Suggestion {
  label: string;
  sublabel: string | null;
  type: KnowledgeType;
  reference: string | null;
}

export interface SuggestResponse {
  query: string;
  suggestions: Suggestion[];
}
