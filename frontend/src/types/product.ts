/** Produit du référentiel interne (schéma ProductRead du backend). */
export interface Product {
  id: string;
  name: string;
  description_fr: string | null;
  reference: string | null;
  hs_code_id: string | null;
  created_at: string;
  updated_at: string;
}
