import { Card } from "@/components/ui/card";
import type { ChartPoint } from "@/types/admin";

interface BarChartProps {
  title: string;
  data: ChartPoint[];
}

/**
 * Diagramme à barres horizontales (SVG/CSS, sans dépendance).
 * Accent orange UM6P, fond blanc.
 */
export function BarChart({ title, data }: BarChartProps) {
  const max = Math.max(1, ...data.map((d) => d.value));

  return (
    <Card className="p-5">
      <h3 className="mb-4 text-sm font-medium text-foreground">{title}</h3>
      {data.length === 0 ? (
        <p className="py-6 text-center text-xs text-muted-foreground">
          Aucune donnée disponible.
        </p>
      ) : (
        <ul className="space-y-2.5">
          {data.map((point) => (
            <li key={point.label} className="flex items-center gap-3">
              <span
                className="w-28 shrink-0 truncate text-xs text-muted-foreground"
                title={point.label}
              >
                {point.label}
              </span>
              <div className="flex-1">
                <div className="h-5 overflow-hidden rounded-md bg-secondary">
                  <div
                    className="flex h-full items-center justify-end rounded-md bg-primary px-2 transition-all"
                    style={{ width: `${Math.max(6, (point.value / max) * 100)}%` }}
                  >
                    <span className="text-[11px] font-medium text-primary-foreground tabular-nums">
                      {point.value}
                    </span>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
