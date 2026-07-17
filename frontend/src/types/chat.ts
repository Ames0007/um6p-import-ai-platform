/** Types du copilote IA (Phase 4). */

export type ConfidenceLevel = "elevee" | "moyenne" | "faible" | "aucune";

export interface Source {
  type: string;
  label: string;
  id?: string | null;
}

export interface DocumentCitation {
  document_title: string;
  chapter?: string | null;
  page?: number | null;
}

export interface Candidate {
  id: string;
  label: string;
  sublabel?: string | null;
}

export interface AssistantMeta {
  intent: string;
  confidence: ConfidenceLevel;
  sources: Source[];
  citations: DocumentCitation[];
  candidates: Candidate[];
  needs_clarification: boolean;
}

/** Événements Server-Sent Events émis par /chat/stream. */
export type StreamEvent =
  | ({ type: "meta"; conversation_id: string } & AssistantMeta)
  | { type: "delta"; text: string }
  | { type: "done"; conversation_id: string }
  | { type: "error"; error: string };

export interface CopilotMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta?: AssistantMeta;
  streaming?: boolean;
}
