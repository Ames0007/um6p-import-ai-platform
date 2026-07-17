"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Menu, X } from "lucide-react";
import { Sidebar } from "./sidebar";
import { BrandLogo } from "./brand-logo";
import { Button } from "@/components/ui/button";

/**
 * Coquille applicative responsive.
 * - Desktop : barre latérale repliable persistante.
 * - Mobile  : barre latérale en overlay pilotée par une barre supérieure.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-background">
      {/* Barre latérale — desktop */}
      <div className="hidden lg:block">
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed((v) => !v)}
        />
      </div>

      {/* Barre latérale — overlay mobile */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/40 lg:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 320, damping: 32 }}
              className="fixed inset-y-0 left-0 z-50 lg:hidden"
            >
              <Sidebar
                collapsed={false}
                onToggle={() => setMobileOpen(false)}
                onNavigate={() => setMobileOpen(false)}
              />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Zone principale */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Barre supérieure — mobile */}
        <header className="flex h-16 items-center justify-between border-b px-4 lg:hidden">
          <BrandLogo />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Ouvrir le menu"
          >
            {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </Button>
        </header>

        <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
