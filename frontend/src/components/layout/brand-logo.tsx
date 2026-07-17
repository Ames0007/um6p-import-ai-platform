import { cn } from "@/lib/utils";

interface BrandLogoProps {
  /** Masque le texte (mode barre latérale repliée). */
  collapsed?: boolean;
  className?: string;
}

/**
 * Marque de l'application. Carré orange UM6P + wordmark charbon.
 * L'orange reste réservé à l'accent visuel de la marque.
 */
export function BrandLogo({ collapsed = false, className }: BrandLogoProps) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
        <span className="text-sm font-bold tracking-tight">IA</span>
      </div>
      {!collapsed && (
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold text-foreground">
            Assistant IA
          </span>
          <span className="text-xs text-muted-foreground">Import UM6P</span>
        </div>
      )}
    </div>
  );
}
