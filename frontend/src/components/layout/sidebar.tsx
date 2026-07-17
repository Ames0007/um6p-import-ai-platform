"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { NAV_ITEMS } from "@/config/navigation";
import { BrandLogo } from "./brand-logo";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  /** Ferme la barre en overlay mobile après navigation. */
  onNavigate?: () => void;
}

export function Sidebar({ collapsed, onToggle, onNavigate }: SidebarProps) {
  const pathname = usePathname();

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "flex h-full flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-300 ease-in-out",
          collapsed ? "w-[76px]" : "w-64"
        )}
      >
        {/* En-tête / marque */}
        <div className="flex h-16 items-center justify-between px-4">
          <BrandLogo collapsed={collapsed} />
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="hidden shrink-0 text-muted-foreground lg:inline-flex"
            aria-label={collapsed ? "Déployer le menu" : "Replier le menu"}
          >
            {collapsed ? (
              <PanelLeftOpen className="size-4" />
            ) : (
              <PanelLeftClose className="size-4" />
            )}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.href);
            const link = (
              <Link
                key={item.href}
                href={item.href}
                onClick={onNavigate}
                className={cn(
                  "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-sidebar-accent hover:text-foreground",
                  collapsed && "justify-center px-0"
                )}
              >
                {active && (
                  <motion.span
                    layoutId="sidebar-active"
                    className="absolute left-0 h-6 w-1 rounded-r-full bg-primary"
                  />
                )}
                <item.icon className="size-5 shrink-0" />
                {!collapsed && <span className="truncate">{item.label}</span>}
                {!collapsed && item.comingSoon && (
                  <span className="ml-auto shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                    Bientôt
                  </span>
                )}
              </Link>
            );

            return collapsed ? (
              <Tooltip key={item.href}>
                <TooltipTrigger asChild>{link}</TooltipTrigger>
                <TooltipContent side="right">{item.label}</TooltipContent>
              </Tooltip>
            ) : (
              link
            );
          })}
        </nav>

        {/* Pied de page */}
        <div className="border-t border-sidebar-border p-4">
          {!collapsed ? (
            <p className="text-xs text-muted-foreground">
              UM6P · Achats & Import
              <br />
              <span className="text-muted-foreground/70">Version 1.0</span>
            </p>
          ) : (
            <div className="flex justify-center">
              <div className="h-2 w-2 rounded-full bg-primary" />
            </div>
          )}
        </div>
      </aside>
    </TooltipProvider>
  );
}
