/**
 * Configuration déclarative des ressources d'administration.
 * Pilote à la fois les tableaux (colonnes) et les formulaires (champs).
 */

export type FieldType =
  | "text"
  | "textarea"
  | "number"
  | "select"
  | "keywords"
  | "date"
  | "datetime"
  | "relation";

export interface FieldConfig {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  options?: { value: string; label: string }[];
  /** Pour type "relation" : ressource liée + champ à afficher. */
  relation?: { resource: string; labelKey: string };
}

export interface ColumnConfig {
  key: string;
  label: string;
  kind?: "text" | "number" | "date" | "badge";
}

export interface AdminResource {
  name: string; // segment d'URL (= endpoint /admin/{name})
  label: string; // pluriel (nav / titre)
  singular: string;
  columns: ColumnConfig[];
  fields: FieldConfig[];
}

const PRODUCT_STATUS = [
  { value: "actif", label: "Actif" },
  { value: "inactif", label: "Inactif" },
  { value: "archive", label: "Archivé" },
];

const AUTH_STATUS = [
  { value: "requise", label: "Requise" },
  { value: "non_requise", label: "Non requise" },
  { value: "conditionnelle", label: "Conditionnelle" },
];

export const ADMIN_RESOURCES: Record<string, AdminResource> = {
  products: {
    name: "products",
    label: "Produits",
    singular: "produit",
    columns: [
      { key: "reference", label: "Référence" },
      { key: "name", label: "Nom" },
      { key: "category", label: "Catégorie" },
      { key: "brand", label: "Marque" },
      { key: "status", label: "Statut", kind: "badge" },
    ],
    fields: [
      { name: "reference", label: "Référence interne", type: "text" },
      { name: "name", label: "Nom du produit", type: "text", required: true },
      { name: "manufacturer", label: "Fabricant", type: "text" },
      { name: "brand", label: "Marque", type: "text" },
      { name: "category", label: "Catégorie", type: "text" },
      { name: "description_fr", label: "Description", type: "textarea" },
      { name: "keywords", label: "Mots-clés", type: "keywords" },
      {
        name: "hs_code_id",
        label: "Code SH",
        type: "relation",
        relation: { resource: "hs-codes", labelKey: "code" },
      },
      {
        name: "country_of_origin_id",
        label: "Pays d'origine",
        type: "relation",
        relation: { resource: "countries", labelKey: "name_fr" },
      },
      {
        name: "preferred_supplier_id",
        label: "Fournisseur privilégié",
        type: "relation",
        relation: { resource: "suppliers", labelKey: "name" },
      },
      { name: "status", label: "Statut", type: "select", options: PRODUCT_STATUS },
      { name: "notes", label: "Notes", type: "textarea" },
    ],
  },
  "product-aliases": {
    name: "product-aliases",
    label: "Alias Produits",
    singular: "alias",
    columns: [{ key: "alias", label: "Alias" }],
    fields: [
      {
        name: "product_id",
        label: "Produit",
        type: "relation",
        required: true,
        relation: { resource: "products", labelKey: "name" },
      },
      { name: "alias", label: "Alias", type: "text", required: true },
    ],
  },
  "hs-codes": {
    name: "hs-codes",
    label: "Codes SH",
    singular: "code SH",
    columns: [
      { key: "code", label: "Code SH" },
      { key: "chapter", label: "Chapitre" },
      { key: "description_fr", label: "Description" },
    ],
    fields: [
      { name: "code", label: "Code SH", type: "text", required: true },
      {
        name: "description_fr",
        label: "Description officielle",
        type: "textarea",
        required: true,
      },
      { name: "chapter", label: "Chapitre", type: "text" },
    ],
  },
  taxes: {
    name: "taxes",
    label: "Taxes",
    singular: "taxe",
    columns: [
      { key: "import_duty", label: "Droit d'import. %", kind: "number" },
      { key: "vat", label: "TVA %", kind: "number" },
      { key: "parafiscal_tax", label: "Parafiscale %", kind: "number" },
      { key: "effective_date", label: "Date d'effet", kind: "date" },
    ],
    fields: [
      {
        name: "hs_code_id",
        label: "Code SH",
        type: "relation",
        required: true,
        relation: { resource: "hs-codes", labelKey: "code" },
      },
      { name: "import_duty", label: "Droit d'importation (%)", type: "number" },
      { name: "vat", label: "TVA (%)", type: "number" },
      { name: "parafiscal_tax", label: "Taxe parafiscale (%)", type: "number" },
      { name: "effective_date", label: "Date d'effet", type: "date" },
      {
        name: "country_id",
        label: "Pays",
        type: "relation",
        relation: { resource: "countries", labelKey: "name_fr" },
      },
      { name: "notes_fr", label: "Notes", type: "textarea" },
    ],
  },
  authorizations: {
    name: "authorizations",
    label: "Autorisations",
    singular: "autorisation",
    columns: [
      { key: "status", label: "Statut", kind: "badge" },
      { key: "organization", label: "Organisme" },
      { key: "ministry", label: "Ministère" },
      { key: "legal_reference", label: "Réf. légale" },
    ],
    fields: [
      {
        name: "hs_code_id",
        label: "Code SH",
        type: "relation",
        required: true,
        relation: { resource: "hs-codes", labelKey: "code" },
      },
      { name: "status", label: "Statut", type: "select", options: AUTH_STATUS },
      { name: "organization", label: "Organisme", type: "text" },
      { name: "ministry", label: "Ministère", type: "text" },
      { name: "legal_reference", label: "Référence légale", type: "text" },
      {
        name: "processing_time_days",
        label: "Délai estimé (jours)",
        type: "number",
      },
      { name: "comments", label: "Commentaires", type: "textarea" },
      { name: "description_fr", label: "Description", type: "textarea" },
    ],
  },
  suppliers: {
    name: "suppliers",
    label: "Fournisseurs",
    singular: "fournisseur",
    columns: [
      { key: "name", label: "Société" },
      { key: "contact_name", label: "Contact" },
      { key: "email", label: "Email" },
      { key: "phone", label: "Téléphone" },
      { key: "lead_time_days", label: "Délai (j)", kind: "number" },
    ],
    fields: [
      { name: "name", label: "Société", type: "text", required: true },
      {
        name: "country_id",
        label: "Pays",
        type: "relation",
        relation: { resource: "countries", labelKey: "name_fr" },
      },
      { name: "website", label: "Site web", type: "text" },
      { name: "contact_name", label: "Contact", type: "text" },
      { name: "email", label: "Email", type: "text" },
      { name: "phone", label: "Téléphone", type: "text" },
      { name: "lead_time_days", label: "Délai d'appro. (jours)", type: "number" },
    ],
  },
  "purchase-history": {
    name: "purchase-history",
    label: "Historique des achats",
    singular: "achat",
    columns: [
      { key: "invoice_number", label: "Facture" },
      { key: "unit_price", label: "Prix unitaire", kind: "number" },
      { key: "currency", label: "Devise" },
      { key: "quantity", label: "Qté", kind: "number" },
      { key: "incoterm", label: "Incoterm" },
      { key: "purchased_at", label: "Date d'achat", kind: "date" },
    ],
    fields: [
      {
        name: "product_id",
        label: "Produit",
        type: "relation",
        required: true,
        relation: { resource: "products", labelKey: "name" },
      },
      {
        name: "supplier_id",
        label: "Fournisseur",
        type: "relation",
        relation: { resource: "suppliers", labelKey: "name" },
      },
      {
        name: "country_id",
        label: "Pays",
        type: "relation",
        relation: { resource: "countries", labelKey: "name_fr" },
      },
      { name: "invoice_number", label: "N° de facture", type: "text" },
      { name: "unit_price", label: "Prix unitaire", type: "number", required: true },
      { name: "currency", label: "Devise", type: "text" },
      { name: "quantity", label: "Quantité", type: "number" },
      { name: "incoterm", label: "Incoterm", type: "text" },
      { name: "purchased_at", label: "Date d'achat", type: "date", required: true },
    ],
  },
  countries: {
    name: "countries",
    label: "Pays",
    singular: "pays",
    columns: [
      { key: "code", label: "Code ISO" },
      { key: "name_fr", label: "Nom" },
    ],
    fields: [
      { name: "code", label: "Code ISO (2 lettres)", type: "text", required: true },
      { name: "name_fr", label: "Nom (français)", type: "text", required: true },
    ],
  },
};

/** Ordre d'affichage dans la navigation de l'administration. */
export const ADMIN_SECTIONS = [
  "products",
  "hs-codes",
  "taxes",
  "authorizations",
  "suppliers",
  "purchase-history",
  "countries",
  "product-aliases",
] as const;
