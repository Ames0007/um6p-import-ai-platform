"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Package, Search, Loader2, Hash, ArrowRight, PackageSearch } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useProductsSearch } from "@/hooks/use-products";
import type { Product } from "@/types/product";

function ProductCard({ product }: { product: Product }) {
  const router = useRouter();
  const target = product.reference || product.name;
  return (
    <Card className="flex flex-col gap-3 p-5">
      <div className="flex items-start gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Package className="size-5" />
        </span>
        <div className="min-w-0">
          <div className="font-medium text-foreground">{product.name}</div>
          {product.reference && (
            <Badge variant="secondary" className="mt-1 font-mono">{product.reference}</Badge>
          )}
        </div>
      </div>
      {product.description_fr && (
        <p className="text-sm text-muted-foreground">{product.description_fr}</p>
      )}
      <div className="flex flex-wrap gap-2 pt-1">
        <Button
          variant="outline"
          size="sm"
          onClick={() => router.push(`/recherche?q=${encodeURIComponent(target)}`)}
        >
          <Hash /> Code SH &amp; taxes <ArrowRight />
        </Button>
      </div>
    </Card>
  );
}

export default function ProduitsPage() {
  const router = useRouter();
  const [query, setQuery] = React.useState("");
  const [submitted, setSubmitted] = React.useState("");

  const { data, isLoading, isError } = useProductsSearch(submitted, submitted.length > 0);
  const products = data ?? [];

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8">
      <PageHeader
        title="Produits"
        description="Recherchez un produit dans le référentiel interne et consultez son code SH."
      />

      <form
        className="mt-6 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          setSubmitted(query.trim());
        }}
        role="search"
      >
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Nom, référence ou description du produit..."
            className="pl-9"
          />
        </div>
        <Button type="submit">Rechercher</Button>
      </form>

      <div className="mt-8">
        {/* État initial */}
        {!submitted && (
          <EmptyState
            icon={Package}
            title="Recherche de produits"
            description="Saisissez un nom, une référence ou une description pour interroger le référentiel produits interne."
          />
        )}

        {/* Chargement */}
        {submitted && isLoading && (
          <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
            <Loader2 className="size-5 animate-spin" /> Recherche dans le référentiel produits…
          </div>
        )}

        {/* Erreur */}
        {submitted && isError && (
          <Card className="p-6 text-sm text-destructive">
            Une erreur est survenue lors de la recherche. Vérifiez que l&apos;API est démarrée.
          </Card>
        )}

        {/* Résultats */}
        {submitted && !isLoading && !isError && products.length > 0 && (
          <div className="space-y-3">
            <div className="text-sm text-muted-foreground">
              {products.length} produit{products.length > 1 ? "s" : ""} pour «&nbsp;{submitted}&nbsp;»
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {products.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          </div>
        )}

        {/* Aucun produit interne -> proposer la base douanière */}
        {submitted && !isLoading && !isError && products.length === 0 && (
          <Card className="flex flex-col items-center gap-3 p-10 text-center">
            <span className="flex size-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
              <PackageSearch className="size-6" />
            </span>
            <div>
              <div className="font-medium text-foreground">
                Aucun produit interne pour «&nbsp;{submitted}&nbsp;»
              </div>
              <p className="mt-1 max-w-md text-sm text-muted-foreground">
                Le référentiel produits interne est distinct de la base douanière
                (codes SH, taxes, documents). Recherchez ce terme dans la base de
                connaissances douanière&nbsp;:
              </p>
            </div>
            <Button onClick={() => router.push(`/recherche?q=${encodeURIComponent(submitted)}`)}>
              <Search /> Rechercher «&nbsp;{submitted}&nbsp;» dans la base douanière <ArrowRight />
            </Button>
          </Card>
        )}
      </div>
    </div>
  );
}
