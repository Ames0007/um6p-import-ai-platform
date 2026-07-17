import { Loader2 } from "lucide-react";

/** Fallback de chargement au niveau route (Phase 5 — récupération de chargement). */
export default function Loading() {
  return (
    <div className="flex min-h-[50vh] w-full items-center justify-center gap-2 text-muted-foreground">
      <Loader2 className="size-5 animate-spin" />
      <span className="text-sm">Chargement…</span>
    </div>
  );
}
