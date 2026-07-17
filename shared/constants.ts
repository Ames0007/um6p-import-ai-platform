/**
 * Constantes partagées entre le frontend et (via génération) le backend.
 * Tout est en français, conformément à l'identité de l'application.
 */

/** Identité visuelle officielle UM6P. */
export const UM6P_COLORS = {
  primary: "#D7492A",
  orangeSecondary: "#ED6E47",
  charcoal: "#3B3B3C",
  white: "#FFFFFF",
} as const;

/** Types de fichiers acceptés pour l'analyse de facture. */
export const ACCEPTED_UPLOAD_MIME_TYPES = [
  "application/pdf",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "image/png",
  "image/jpeg",
  "image/webp",
] as const;

export const ACCEPTED_UPLOAD_EXTENSIONS = [
  ".pdf",
  ".xls",
  ".xlsx",
  ".doc",
  ".docx",
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
] as const;

export const MAX_UPLOAD_SIZE_MB = 25;

/** Statuts métier partagés. */
export const INVOICE_STATUS = {
  RECEIVED: "recue",
  PROCESSING: "en_traitement",
  ANALYZED: "analysee",
  ERROR: "erreur",
} as const;

export const AUTHORIZATION_STATUS = {
  REQUIRED: "requise",
  NOT_REQUIRED: "non_requise",
  CONDITIONAL: "conditionnelle",
} as const;
