"use client";

import * as React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { WifiOff, Loader2, RefreshCw } from "lucide-react";
import { API_BASE } from "@/lib/api/client";

/** Sonde légère de disponibilité du backend (liveness). */
async function ping(): Promise<boolean> {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 5000);
    const res = await fetch(`${API_BASE}/live`, {
      signal: ctrl.signal,
      cache: "no-store",
    });
    clearTimeout(timer);
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * Bannière de connexion (Phase 5).
 *
 * Sonde périodiquement le backend. Quand la connexion revient après une coupure
 * (redémarrage backend, port DB, etc.), invalide toutes les requêtes React Query
 * pour une RÉCUPÉRATION AUTOMATIQUE, sans rechargement manuel de la page.
 */
export function ConnectionStatus() {
  const queryClient = useQueryClient();
  const [online, setOnline] = React.useState(true);
  const [checking, setChecking] = React.useState(false);
  const wasOnline = React.useRef(true);

  const check = React.useCallback(async () => {
    setChecking(true);
    const ok = await ping();
    setChecking(false);
    setOnline(ok);
    // Transition hors-ligne → en-ligne : on relance toutes les requêtes.
    if (ok && !wasOnline.current) {
      queryClient.invalidateQueries();
    }
    wasOnline.current = ok;
    return ok;
  }, [queryClient]);

  React.useEffect(() => {
    let active = true;
    check();
    const interval = setInterval(() => {
      if (active) check();
    }, 15_000);
    const onWake = () => check();
    window.addEventListener("online", onWake);
    window.addEventListener("focus", onWake);
    return () => {
      active = false;
      clearInterval(interval);
      window.removeEventListener("online", onWake);
      window.removeEventListener("focus", onWake);
    };
  }, [check]);

  if (online) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 top-0 z-[100] flex justify-center px-4 pt-3"
    >
      <div className="pointer-events-auto flex items-center gap-3 rounded-xl border border-amber-300/70 bg-amber-50 px-4 py-2.5 text-sm text-amber-900 shadow-lg dark:border-amber-500/40 dark:bg-amber-950/90 dark:text-amber-100">
        {checking ? (
          <Loader2 className="size-4 shrink-0 animate-spin" />
        ) : (
          <WifiOff className="size-4 shrink-0" />
        )}
        <span>Connexion au serveur perdue. Nouvelle tentative automatique…</span>
        <button
          type="button"
          onClick={() => check()}
          disabled={checking}
          className="ml-1 inline-flex items-center gap-1 rounded-lg border border-amber-400/70 px-2 py-1 text-xs font-medium transition-colors hover:bg-amber-100 disabled:opacity-50 dark:hover:bg-amber-900"
        >
          <RefreshCw className="size-3" /> Réessayer
        </button>
      </div>
    </div>
  );
}
