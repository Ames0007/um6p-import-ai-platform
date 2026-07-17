import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Fusionne des classes Tailwind de façon sûre (déduplication + conflits). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Formate une taille de fichier en unités lisibles (FR). */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 o";
  const units = ["o", "Ko", "Mo", "Go"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

/** Formate une date ISO en français (jj/mm/aaaa). */
export function formatDateFr(iso: string): string {
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(iso));
}
