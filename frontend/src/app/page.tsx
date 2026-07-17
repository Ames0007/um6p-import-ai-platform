"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, MessageSquareText, FileSearch, GitCompare, HelpCircle } from "lucide-react";
import { SearchBar } from "@/components/search/search-bar";
import { QuickActions } from "@/components/home/quick-actions";
import { routeForQuery } from "@/lib/search-mode";

const ASSISTANT_ACTIONS = [
  { label: "Poser une question complexe", icon: MessageSquareText, href: "/conversation" },
  { label: "Analyser un document", icon: FileSearch, href: "/analyse-importation" },
  { label: "Comparer", icon: GitCompare, href: "/conversation" },
  { label: "Expliquer", icon: HelpCircle, href: "/conversation" },
];

/**
 * Accueil — plateforme de recherche achats & douane (façon Google Enterprise
 * Search). La recherche est l'interaction principale : les requêtes simples
 * interrogent l'Index de connaissance ; seul le raisonnement passe par l'IA.
 */
export default function HomePage() {
  const router = useRouter();

  return (
    <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8 text-center"
      >
        <span className="mb-4 inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          <span className="size-1.5 rounded-full bg-primary" />
          UM6P · Achats &amp; Import
        </span>
        <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Recherche douanière &amp; achats
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-balance text-sm text-muted-foreground sm:text-base">
          Recherchez un produit, un code SH, une substance, un fournisseur ou un
          document. L&apos;assistant IA intervient pour comparer, expliquer ou analyser.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="w-full"
      >
        <SearchBar autoFocus size="lg" onSubmit={(q) => router.push(routeForQuery(q))} />
      </motion.div>

      <div className="mt-10 w-full">
        <QuickActions />
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="mt-10 w-full rounded-2xl border bg-card p-4 shadow-sm"
      >
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground">
          <Sparkles className="size-4 text-primary" /> Assistant IA
          <span className="font-normal text-muted-foreground">— pour le raisonnement et l&apos;analyse</span>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {ASSISTANT_ACTIONS.map((a) => (
            <button
              key={a.label}
              type="button"
              onClick={() => router.push(a.href)}
              className="flex items-center gap-2 rounded-xl border bg-background px-3 py-2 text-left text-xs font-medium text-foreground transition-colors hover:border-primary/40 hover:bg-accent/40"
            >
              <a.icon className="size-4 shrink-0 text-primary" />
              <span className="min-w-0 truncate">{a.label}</span>
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
