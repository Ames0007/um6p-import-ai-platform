"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ADMIN_RESOURCES, ADMIN_SECTIONS } from "@/config/admin-resources";
import { cn } from "@/lib/utils";

interface Tab {
  href: string;
  label: string;
}

const TABS: Tab[] = [
  { href: "/administration", label: "Tableau de bord" },
  ...ADMIN_SECTIONS.map((name) => ({
    href: `/administration/${name}`,
    label: ADMIN_RESOURCES[name].label,
  })),
  { href: "/administration/import", label: "Import" },
];

export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-10 -mx-4 mb-6 border-b bg-background/80 px-4 backdrop-blur">
      <div className="flex gap-1 overflow-x-auto py-2">
        {TABS.map((tab) => {
          const active =
            tab.href === "/administration"
              ? pathname === "/administration"
              : pathname.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              )}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
