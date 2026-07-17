import type { DocumentCategory, DocumentStatus } from "@/types/knowledge";

/** Libellés français des catégories de documents. */
export const CATEGORY_LABELS: Record<DocumentCategory, string> = {
  code_des_douanes: "Code des Douanes",
  nomenclature_douaniere: "Nomenclature Douanière",
  produits_chimiques: "Produits Chimiques",
  engrais: "Engrais",
  machines_et_appareils: "Machines et appareils",
  matieres_plastiques: "Matières plastiques",
  produits_controles: "Produits contrôlés",
  circulaires: "Circulaires",
  annexes_reglementaires: "Annexes réglementaires",
  autre: "Autre",
};

type BadgeVariant =
  | "default"
  | "secondary"
  | "outline"
  | "success"
  | "warning"
  | "destructive";

/** Libellé + variante de badge pour chaque statut de document. */
export const STATUS_META: Record<
  DocumentStatus,
  { label: string; variant: BadgeVariant }
> = {
  en_attente: { label: "En attente", variant: "secondary" },
  en_traitement: { label: "En traitement", variant: "warning" },
  termine: { label: "Terminé", variant: "success" },
  partiel: { label: "Partiel", variant: "warning" },
  erreur: { label: "Erreur", variant: "destructive" },
  doublon: { label: "Doublon", variant: "outline" },
};

export const CATEGORY_OPTIONS = Object.entries(CATEGORY_LABELS).map(
  ([value, label]) => ({ value: value as DocumentCategory, label })
);
