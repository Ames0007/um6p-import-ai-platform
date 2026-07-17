"use client";

import * as React from "react";
import { Search, CornerDownLeft, Hash, Package, FileText, BookOpen, Percent, ShieldCheck, Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import { useKnowledgeSuggest } from "@/hooks/use-knowledge-suggest";
import type { KnowledgeType, Suggestion } from "@/types/knowledge";

const TYPE_ICON: Record<KnowledgeType, React.ComponentType<{ className?: string }>> = {
  HS_CODE: Hash,
  PRODUCT: Package,
  DOCUMENT: FileText,
  CHAPTER: BookOpen,
  SECTION: Layers,
  TAX: Percent,
  AUTHORIZATION: ShieldCheck,
  SUPPLIER: Package,
};

const DEFAULT_PLACEHOLDER =
  "Rechercher un produit, un code SH, une substance chimique, un fournisseur ou un document...";

interface SearchBarProps {
  initialValue?: string;
  placeholder?: string;
  autoFocus?: boolean;
  size?: "lg" | "md";
  onSubmit: (query: string) => void;
}

/** Barre de recherche avec suggestions instantanées (Index de connaissance, sans IA). */
export function SearchBar({
  initialValue = "",
  placeholder = DEFAULT_PLACEHOLDER,
  autoFocus = false,
  size = "lg",
  onSubmit,
}: SearchBarProps) {
  const [value, setValue] = React.useState(initialValue);
  const [open, setOpen] = React.useState(false);
  const [active, setActive] = React.useState(-1);
  const boxRef = React.useRef<HTMLDivElement>(null);

  const { data } = useKnowledgeSuggest(value, open);
  const suggestions = data?.suggestions ?? [];

  React.useEffect(() => {
    function onClick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const submit = (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) return;
    setOpen(false);
    setActive(-1);
    onSubmit(trimmed);
  };

  const queryFor = (s: Suggestion) =>
    s.type === "HS_CODE" && s.reference ? s.reference : s.label;

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!open || suggestions.length === 0) {
      if (e.key === "Enter") submit(value);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => (a + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => (a <= 0 ? suggestions.length - 1 : a - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (active >= 0 && active < suggestions.length) submit(queryFor(suggestions[active]));
      else submit(value);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={boxRef} className="relative w-full">
      <div
        className={cn(
          "flex items-center gap-3 rounded-2xl border bg-card shadow-sm transition-colors focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-ring",
          size === "lg" ? "px-5 py-4" : "px-4 py-2.5"
        )}
      >
        <Search className={cn("shrink-0 text-muted-foreground", size === "lg" ? "size-5" : "size-4")} />
        <input
          value={value}
          autoFocus={autoFocus}
          onChange={(e) => {
            setValue(e.target.value);
            setOpen(true);
            setActive(-1);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          className={cn(
            "w-full bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none",
            size === "lg" ? "text-base" : "text-sm"
          )}
        />
        <kbd className="hidden shrink-0 items-center gap-1 rounded border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground sm:inline-flex">
          <CornerDownLeft className="size-3" /> Entrée
        </kbd>
      </div>

      {open && value.trim().length >= 2 && suggestions.length > 0 && (
        <div className="absolute z-50 mt-2 w-full overflow-hidden rounded-xl border bg-popover shadow-lg">
          {suggestions.map((s, i) => {
            const Icon = TYPE_ICON[s.type] ?? Search;
            return (
              <button
                key={`${s.type}-${s.reference}-${i}`}
                type="button"
                onMouseEnter={() => setActive(i)}
                onClick={() => submit(queryFor(s))}
                className={cn(
                  "flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors",
                  active === i ? "bg-accent" : "hover:bg-accent/60"
                )}
              >
                <Icon className="size-4 shrink-0 text-muted-foreground" />
                <span className="min-w-0 flex-1 truncate text-sm text-foreground">
                  {s.label}
                </span>
                {s.sublabel && (
                  <span className="shrink-0 text-xs text-muted-foreground">{s.sublabel}</span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
