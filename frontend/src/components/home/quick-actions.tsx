"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { QUICK_ACTIONS } from "@/config/quick-actions";

/** Grille d'actions rapides (catégories) sous la barre de recherche. */
export function QuickActions() {
  const router = useRouter();

  return (
    <div className="grid w-full grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {QUICK_ACTIONS.map((action, i) => (
        <motion.button
          key={action.label}
          type="button"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 * i, duration: 0.25 }}
          whileHover={{ y: -2 }}
          onClick={() => router.push(action.href)}
          className="group flex flex-col items-center gap-2 rounded-2xl border bg-card p-4 text-center shadow-sm transition-colors hover:border-primary/40 hover:bg-accent/40"
        >
          <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
            <action.icon className="size-5" />
          </span>
          <span className="min-w-0">
            <span className="block text-sm font-medium text-foreground">{action.label}</span>
            <span className="mt-0.5 hidden text-xs text-muted-foreground sm:block">
              {action.description}
            </span>
          </span>
        </motion.button>
      ))}
    </div>
  );
}
