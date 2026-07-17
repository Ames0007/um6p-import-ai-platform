/** Types du moteur de conformité à l'import (Phase 5). */

export type AnalysisStatus =
  | "en_attente"
  | "en_cours"
  | "termine"
  | "partiel"
  | "erreur";

export type RiskLevel = "faible" | "moyen" | "eleve";

export interface AnalysisListItem {
  id: string;
  original_filename: string;
  supplier_name_raw: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  currency: string | null;
  status: AnalysisStatus;
  overall_risk: RiskLevel | null;
  confidence: string | null;
  total_items: number;
  processed_items: number;
  created_at: string;
}

export interface AnalysisItem {
  id: string;
  line_number: number;
  raw_text: string | null;
  raw_product_name: string | null;
  raw_quantity: number | null;
  raw_unit_price: number | null;
  raw_currency: string | null;
  matched_product_id: string | null;
  match_confidence: number | null;
  match_reason: string | null;
  match_method: string;
  hs_code: string | null;
  import_duty: number | null;
  vat: number | null;
  parafiscal_tax: number | null;
  authorizations: Array<Record<string, unknown>> | null;
  required_documents: string[] | null;
  purchase_count: number;
  avg_price: number | null;
  min_price: number | null;
  max_price: number | null;
  last_price: number | null;
  last_date: string | null;
  price_variation_percent: number | null;
  price_alert_level: RiskLevel | null;
  status: "rapproche" | "a_valider" | "sans_donnees";
}

export interface Finding {
  id: string;
  item_id: string | null;
  type: string;
  risk: RiskLevel;
  message: string;
}

export interface ReportContent {
  supplier?: { raw?: string | null };
  invoice_summary?: Record<string, unknown>;
  detected_products?: Array<Record<string, unknown>>;
  compliance_analysis?: { overall_risk?: string; findings?: Finding[] };
  taxes?: Array<Record<string, unknown>>;
  required_documents?: string[];
  purchase_history?: Array<Record<string, unknown>>;
  price_comparison?: Array<Record<string, unknown>>;
  warnings?: Array<{ risk: string; message: string }>;
  recommendations?: string[];
  sources?: string[];
  citations?: Array<{ document_title: string; chapter?: string | null; page?: number | null }>;
  confidence?: string;
}

export interface AnalysisDetail extends AnalysisListItem {
  incoterm: string | null;
  ocr_provider: string | null;
  execution_ms: number | null;
  summary: string | null;
  error_message: string | null;
  items: AnalysisItem[];
  findings: Finding[];
  report: ReportContent | null;
}

export interface AnalysisProgress {
  id: string;
  status: AnalysisStatus;
  total_items: number;
  processed_items: number;
  progress_percent: number;
  overall_risk: RiskLevel | null;
}

export interface AnalysisDispatchResult {
  analyses: AnalysisListItem[];
  mode: "queued" | "inline";
}
