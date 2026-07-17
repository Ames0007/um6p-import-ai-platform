"use client";

import * as React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

/**
 * Frontière d'erreur au niveau route (Phase 5).
 * Remplace l'écran blanc par un message clair + bouton « Réessayer » (reset()).
 */
export default function RouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    // Trace côté client (repris par l'observabilité navigateur).
    console.error("Erreur de route:", error);
  }, [error]);

  return (
    <div className="mx-auto flex min-h-[60vh] w-full max-w-lg flex-col items-center justify-center gap-4 px-4 text-center">
      <span className="flex size-14 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
        <AlertTriangle className="size-7" />
      </span>
      <div>
        <h2 className="text-lg font-semibold text-foreground">
          Une erreur est survenue
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Cette section n&apos;a pas pu se charger. Le service est peut-être en
          cours de redémarrage — réessayez dans un instant.
        </p>
      </div>
      <button
        type="button"
        onClick={() => reset()}
        className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:opacity-90"
      >
        <RefreshCw className="size-4" /> Réessayer
      </button>
    </div>
  );
}
