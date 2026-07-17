import { type LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
}

export function StatCard({ label, value, icon: Icon }: StatCardProps) {
  return (
    <Card className="flex items-center gap-4 p-4">
      <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
        <Icon className="size-5" />
      </span>
      <div className="min-w-0">
        <div className="text-2xl font-semibold tabular-nums text-foreground">
          {value}
        </div>
        <div className="truncate text-xs text-muted-foreground">{label}</div>
      </div>
    </Card>
  );
}
