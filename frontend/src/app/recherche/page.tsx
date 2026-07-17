"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Sparkles, Loader2, SearchX, BookOpen, ArrowRight } from "lucide-react";
import { SearchBar } from "@/components/search/search-bar";
import { ResultCard } from "@/components/search/result-card";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useKnowledgeLookup } from "@/hooks/use-knowledge-lookup";
import { isReasoningQuery } from "@/lib/search-mode";

function AssistantBanner({ query }: { query: string }) {
  const router = useRouter();
  return (
    <Card className="flex flex-col items-start justify-between gap-3 border-primary/30 bg-primary/5 p-4 sm:flex-row sm:items-center">
      <div className="flex items-center gap-2 text-sm text-foreground">
        <Sparkles className="size-4 shrink-0 text-primary" />
        <span>Besoin d&apos;une comparaison, d&apos;une explication ou d&apos;une analyse&nbsp;?</span>
      </div>
      <Button
        size="sm"
        onClick={() => router.push(`/conversation?q=${encodeURIComponent(query)}`)}
      >
        Demander à l&apos;Assistant IA <ArrowRight />
      </Button>
    </Card>
  );
}

function SearchResults() {
  const router = useRouter();
  const params = useSearchParams();
  const query = params.get("q") ?? "";
  const { data, isLoading, isError } = useKnowledgeLookup(query);

  const reasoning = isReasoningQuery(query);
  const results = data?.results ?? [];
  const chapterCodes = data?.chapter_codes ?? [];

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-6">
      <SearchBar
        key={query}
        initialValue={query}
        size="md"
        onSubmit={(q) => router.push(`/recherche?q=${encodeURIComponent(q)}`)}
      />

      <div className="mt-6 space-y-4">
        {/* Escalade IA quand la requête relève du raisonnement. */}
        {reasoning && <AssistantBanner query={query} />}

        {isLoading && (
          <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
            <Loader2 className="size-5 animate-spin" /> Recherche dans l&apos;Index de connaissance…
          </div>
        )}

        {isError && (
          <Card className="p-6 text-sm text-destructive">
            Une erreur est survenue lors de la recherche. Vérifiez que l&apos;API est démarrée.
          </Card>
        )}

        {!isLoading && !isError && data && (
          <>
            {/* Aperçu chapitre */}
            {data.mode === "chapter" && results[0] && (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <span className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <BookOpen className="size-5" />
                  </span>
                  <div>
                    <div className="text-lg font-semibold text-foreground">
                      {results[0].title || results[0].chapter}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {chapterCodes.length} code(s) SH dans ce chapitre
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {chapterCodes.map((c) => (
                    <ResultCard key={c.id} result={c} compact />
                  ))}
                </div>
              </div>
            )}

            {/* Résultat(s) classés / exact */}
            {data.mode !== "chapter" && results.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>
                    {results.length} résultat{results.length > 1 ? "s" : ""} pour «&nbsp;{query}&nbsp;»
                  </span>
                  {data.mode === "exact_hs" && <Badge variant="success">Correspondance exacte</Badge>}
                </div>
                {/* Pas de correspondance exacte : cadrer les résultats comme des
                    suggestions à vérifier (jamais une classification inventée). */}
                {data.mode !== "exact_hs" && (
                  <Card className="border-amber-300/60 bg-amber-50/60 p-3 text-xs text-amber-900 dark:border-amber-500/30 dark:bg-amber-950/30 dark:text-amber-100">
                    Aucune correspondance exacte : voici les entrées les plus proches
                    de la base documentaire, classées par pertinence. Vérifiez la
                    correspondance avant toute déclaration douanière ; en cas de doute,
                    demandez à l&apos;Assistant&nbsp;IA.
                  </Card>
                )}
                {results.map((r) => (
                  <ResultCard key={r.id} result={r} />
                ))}
              </div>
            )}

            {/* Aucun résultat */}
            {data.mode === "empty" && (
              <Card className="flex flex-col items-center gap-3 p-10 text-center">
                <span className="flex size-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
                  <SearchX className="size-6" />
                </span>
                <div>
                  <div className="font-medium text-foreground">Aucun concept trouvé pour «&nbsp;{query}&nbsp;»</div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Reformulez votre recherche ou demandez à l&apos;Assistant IA.
                  </p>
                </div>
                <Button onClick={() => router.push(`/conversation?q=${encodeURIComponent(query)}`)}>
                  <Sparkles /> Demander à l&apos;Assistant IA
                </Button>
              </Card>
            )}

            {/* Escalade IA disponible en bas (hors cas déjà affiché). */}
            {!reasoning && data.mode !== "empty" && <AssistantBanner query={query} />}
          </>
        )}
      </div>
    </div>
  );
}

export default function RecherchePage() {
  return (
    <React.Suspense fallback={null}>
      <SearchResults />
    </React.Suspense>
  );
}
