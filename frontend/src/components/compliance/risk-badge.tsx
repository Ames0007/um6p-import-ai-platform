import { Badge } from "@/components/ui/badge";
import type { RiskLevel } from "@/types/compliance";

const META: Record<
  RiskLevel,
  { label: string; variant: "success" | "warning" | "destructive" }
> = {
  faible: { label: "Risque faible", variant: "success" },
  moyen: { label: "Risque moyen", variant: "warning" },
  eleve: { label: "Risque élevé", variant: "destructive" },
};

export function RiskBadge({ level }: { level: RiskLevel | null | undefined }) {
  if (!level) return <Badge variant="secondary">—</Badge>;
  const meta = META[level];
  return <Badge variant={meta.variant}>{meta.label}</Badge>;
}
