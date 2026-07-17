"use client";

import * as React from "react";
import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/api/client";
import { ConnectionStatus } from "@/components/system/connection-status";

/**
 * Fournisseurs globaux (client).
 *
 * Résilience (Phase 5) :
 *  - nouvelles tentatives automatiques avec backoff exponentiel (sauf erreurs 4xx) ;
 *  - refetch au retour de focus et à la reconnexion réseau ;
 *  - bannière de reconnexion + récupération automatique après redémarrage backend
 *    (voir <ConnectionStatus/>).
 */
export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            gcTime: 5 * 60 * 1000,
            // Ne pas réessayer les erreurs client (4xx) ; réessayer le reste.
            retry: (failureCount, error) => {
              if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
                return false;
              }
              return failureCount < 3;
            },
            // Backoff exponentiel plafonné à 15 s.
            retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 15_000),
            refetchOnWindowFocus: true,
            refetchOnReconnect: true,
          },
          mutations: {
            retry: (failureCount, error) => {
              if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
                return false;
              }
              return failureCount < 1;
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider delayDuration={200}>
        <ConnectionStatus />
        {children}
      </TooltipProvider>
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}
