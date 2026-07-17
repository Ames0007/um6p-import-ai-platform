/**
 * Types de domaine partagés (contrats d'API côté frontend).
 * Ces types reflètent les schémas Pydantic exposés par le backend.
 */

export type UUID = string;
export type ISODateString = string;

export interface Country {
  id: UUID;
  code: string; // ISO 3166-1 alpha-2
  nameFr: string;
}

export interface HsCode {
  id: UUID;
  code: string; // Code SH (Système Harmonisé)
  descriptionFr: string;
  chapter: string | null;
}

export interface Tax {
  id: UUID;
  hsCodeId: UUID;
  label: string; // ex. "Droit d'importation", "TVA"
  ratePercent: number;
  countryId: UUID | null;
  notesFr: string | null;
}

export interface Authorization {
  id: UUID;
  hsCodeId: UUID;
  status: "requise" | "non_requise" | "conditionnelle";
  ministry: string | null; // Ministère émetteur
  descriptionFr: string | null;
}

export interface Supplier {
  id: UUID;
  name: string;
  countryId: UUID | null;
  email: string | null;
  phone: string | null;
}

export interface Product {
  id: UUID;
  name: string;
  descriptionFr: string | null;
  hsCodeId: UUID | null;
  reference: string | null;
}

export interface PurchaseHistoryEntry {
  id: UUID;
  productId: UUID;
  supplierId: UUID | null;
  unitPrice: number;
  currency: string;
  quantity: number;
  purchasedAt: ISODateString;
}

export interface Invoice {
  id: UUID;
  filename: string;
  status: "recue" | "en_traitement" | "analysee" | "erreur";
  uploadedAt: ISODateString;
}

/** Message de conversation avec l'assistant. */
export interface ChatMessage {
  id: UUID;
  role: "user" | "assistant";
  content: string;
  createdAt: ISODateString;
}
