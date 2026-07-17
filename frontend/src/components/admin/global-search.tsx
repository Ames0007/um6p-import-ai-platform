"use client";

import * as React from "react";
import { Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useGlobalSearch } from "@/hooks/use-admin";
import type { GlobalSearchResponse, SearchEntity } from "@/types/admin";

const GROUPS: { key: keyof GlobalSearchResponse; label: string }[] = [
  { key: "products", label: "Produits" },
  { key: "aliases", label: "Alias" },
  { key: "hs_codes", label: "Codes SH" },
  { key: "suppliers", label: "Fournisseurs" },
  { key: "purchases", label: "Achats" },
  { key: "authorizations", label: "Autorisations" },
];

export function GlobalSearch() {
  const [query, setQuery] = React.useState("");
  const [debounced, setDebounced] = React.useState("");

  React.useEffect(() => {
    const t = setTimeout(() => setDebounced(query), 300);
    return () => clearTimeout(t);
  }, [query]);

  const { data, isFetching } = useGlobalSearch(debounced);

  const total = data
    ? GROUPS.reduce((n, g) => n + (data[g.key] as SearchEntity[]).length, 0)
    : 0;

  return (
    <div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Recherche globale (produits, alias, codes SH, fournisseurs…)"
          className="h-11 pl-9"
        />
        {isFetching && (
          <Loader2 className="absolute right-3 top-1/2 size-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {data && debounced.length >= 2 && (
        <div className="mt-4">
          {total === 0 ? (
            <p className="rounded-xl border border-dashed bg-secondary/30 px-4 py-6 text-center text-sm text-muted-foreground">
              Aucun résultat pour « {debounced} ».
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {GROUPS.map((group) => {
                const items = data[group.key] as SearchEntity[];
                if (items.length === 0) return null;
                return (
                  <div key={group.key} className="rounded-xl border bg-card p-3">
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {group.label} ({items.length})
                    </h4>
                    <ul className="space-y-1.5">
                      {items.map((item) => (
                        <li key={item.id} className="text-sm">
                          <span className="font-medium text-foreground">
                            {item.label}
                          </span>
                          {item.sublabel && (
                            <span className="block truncate text-xs text-muted-foreground">
                              {item.sublabel}
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
