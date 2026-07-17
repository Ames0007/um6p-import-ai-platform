import {
  Package,
  Hash,
  FileText,
  Percent,
  ShieldCheck,
  FileSearch,
  type LucideIcon,
} from "lucide-react";

export interface QuickAction {
  label: string;
  description: string;
  icon: LucideIcon;
  /** Destination (page existante ou recherche pré-remplie). */
  href: string;
}

/**
 * Actions rapides (catégories) affichées sous la barre de recherche.
 * Chaque action ouvre soit une page existante, soit une recherche pré-remplie
 * dans l'Index de connaissance — jamais l'IA.
 */
export const QUICK_ACTIONS: QuickAction[] = [
  {
    label: "Produits",
    description: "Référentiel produits interne",
    icon: Package,
    href: "/produits",
  },
  {
    label: "Codes SH",
    description: "Nomenclature du Système Harmonisé",
    icon: Hash,
    href: "/recherche?q=Chapitre%2031",
  },
  {
    label: "Documents",
    description: "Bibliothèque documentaire officielle",
    icon: FileText,
    href: "/bibliotheque",
  },
  {
    label: "Taxes",
    description: "Droits de douane et TVA",
    icon: Percent,
    href: "/recherche?q=3104.20",
  },
  {
    label: "Autorisations",
    description: "Exigences réglementaires d'importation",
    icon: ShieldCheck,
    href: "/recherche?q=autorisation",
  },
  {
    label: "Analyse Importation",
    description: "Analyser une facture ou un dossier",
    icon: FileSearch,
    href: "/analyse-importation",
  },
];
