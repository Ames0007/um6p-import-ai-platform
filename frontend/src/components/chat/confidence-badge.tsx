import { Badge } from "@/components/ui/badge";
import type { ConfidenceLevel } from "@/types/chat";

const META: Record<
  ConfidenceLevel,
  { label: string; variant: "success" | "default" | "warning" | "secondary" }
> = {
  elevee: { label: "Confiance élevée", variant: "success" },
  moyenne: { label: "Confiance moyenne", variant: "default" },
  faible: { label: "Confiance faible", variant: "warning" },
  aucune: { label: "Aucune donnée vérifiée", variant: "secondary" },
};

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const meta = META[level];
  return <Badge variant={meta.variant}>{meta.label}</Badge>;
}
