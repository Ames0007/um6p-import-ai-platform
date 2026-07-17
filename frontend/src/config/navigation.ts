import {
  Home,
  MessageSquare,
  Package,
  FileSearch,
  History,
  Library,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  /** Libellé affiché (français). */
  label: string;
  href: string;
  icon: LucideIcon;
  /** Réservé à une future gestion des rôles (ex. Administration). */
  adminOnly?: boolean;
  /** Fonctionnalité non finalisée : affiche un badge « Bientôt ». */
  comingSoon?: boolean;
}

/** Navigation principale de la barre latérale. */
export const NAV_ITEMS: NavItem[] = [
  { label: "Accueil", href: "/", icon: Home },
  { label: "Conversation", href: "/conversation", icon: MessageSquare },
  { label: "Produits", href: "/produits", icon: Package },
  { label: "Bibliothèque", href: "/bibliotheque", icon: Library },
  { label: "Analyse Importation", href: "/analyse-importation", icon: FileSearch },
  // « Factures » retiré du menu : l'analyse de factures est fournie par
  // « Analyse Importation ». La page /factures redirige vers ce module.
  { label: "Historique", href: "/historique", icon: History, comingSoon: true },
  { label: "Administration", href: "/administration", icon: Settings, adminOnly: true },
];
