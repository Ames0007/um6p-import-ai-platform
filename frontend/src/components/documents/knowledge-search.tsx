"use client";

import * as React from "react";
import { Search, FileText, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useKnowledgeSearch } from "@/hooks/use-knowledge-search";

/**
 * Recherche dans la base de connaissances officielle.
 * Chaque résultat affiche sa traçabilité (document — chapitre — page).
 */
export function KnowledgeSearch() {
  const [query, setQuery] = React.useState("");
  const [debounced, setDebounced] = React.useState("");

  React.useEffect(() => {
    const t = setTimeout(() => setDebounced(query), 350);
    return () => clearTimeout(t);
  }, [query]);

  const { data, isFetching } = useKnowledgeSearch(debounced);

  return (
    <div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Rechercher dans les documents officiels (ex. « centrifuge »)…"
          className="h-11 pl-9"
        />
        {isFetching && (
          <Loader2 className="absolute right-3 top-1/2 size-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {data && debounced.length >= 2 && (
        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {data.total} résultat{data.total > 1 ? "s" : ""}
            </span>
            <Badge variant="secondary">
              recherche {data.mode === "semantique" ? "sémantique" : "texte"}
            </Badge>
          </div>

          {data.hits.length === 0 ? (
            <p className="rounded-xl border border-dashed bg-secondary/30 px-4 py-8 text-center text-sm text-muted-foreground">
              Aucun passage trouvé dans les documents officiels.
            </p>
          ) : (
            data.hits.map((hit) => (
              <article
                key={hit.chunk_id}
                className="rounded-xl border bg-card p-4"
              >
                <p className="text-sm leading-relaxed text-foreground">
                  {hit.excerpt}
                </p>

                {hit.hs_codes.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {hit.hs_codes.map((code) => (
                      <Badge key={code} variant="default">
                        {code}
                      </Badge>
                    ))}
                  </div>
                )}

                <div className="mt-3 flex items-center gap-1.5 border-t pt-2 text-xs text-muted-foreground">
                  <FileText className="size-3.5 text-primary" />
                  <span className="font-medium text-foreground">Source :</span>
                  <span>{hit.citation.document_title}</span>
                  {hit.citation.chapter && <span>· {hit.citation.chapter}</span>}
                  {hit.citation.page != null && (
                    <span>· Page {hit.citation.page}</span>
                  )}
                </div>
              </article>
            ))
          )}
        </div>
      )}
    </div>
  );
}
