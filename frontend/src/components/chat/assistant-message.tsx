"use client";

import * as React from "react";
import { FileText, Loader2, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfidenceBadge } from "./confidence-badge";
import type { CopilotMessage } from "@/types/chat";

/** Rend un texte avec **gras** et puces « - » (markdown minimal, sans dépendance). */
function FormattedText({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="space-y-1 text-sm leading-relaxed">
      {lines.map((line, i) => {
        if (line.trim() === "") return <div key={i} className="h-1" />;
        const bullet = line.trimStart().startsWith("- ");
        const content = bullet ? line.trimStart().slice(2) : line;
        return (
          <p key={i} className={bullet ? "flex gap-2 pl-1" : undefined}>
            {bullet && <span className="text-primary">•</span>}
            <span>{renderInline(content)}</span>
          </p>
        );
      })}
    </div>
  );
}

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i} className="font-semibold text-foreground">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    )
  );
}

interface AssistantMessageProps {
  message: CopilotMessage;
  onSelectCandidate: (label: string) => void;
}

export function AssistantMessage({
  message,
  onSelectCandidate,
}: AssistantMessageProps) {
  const meta = message.meta;

  return (
    <div className="flex gap-3">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
        <Sparkles className="size-4" />
      </div>
      <div className="min-w-0 flex-1 space-y-3">
        <div className="rounded-2xl bg-secondary px-4 py-3">
          {message.content ? (
            <FormattedText text={message.content} />
          ) : message.streaming ? (
            <span className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" /> Recherche dans la base
              de connaissances…
            </span>
          ) : null}
        </div>

        {/* Liste de sélection (désambiguïsation) */}
        {meta?.candidates && meta.candidates.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {meta.candidates.map((c) => (
              <Button
                key={c.id}
                variant="outline"
                size="sm"
                onClick={() => onSelectCandidate(c.label)}
              >
                {c.label}
                {c.sublabel && (
                  <span className="text-muted-foreground">· {c.sublabel}</span>
                )}
              </Button>
            ))}
          </div>
        )}

        {/* Citations documentaires */}
        {meta?.citations && meta.citations.length > 0 && (
          <div className="space-y-1">
            {meta.citations.map((cit, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 text-xs text-muted-foreground"
              >
                <FileText className="size-3.5 text-primary" />
                <span className="font-medium text-foreground">Source :</span>
                <span>{cit.document_title}</span>
                {cit.chapter && <span>· {cit.chapter}</span>}
                {cit.page != null && <span>· Page {cit.page}</span>}
              </div>
            ))}
          </div>
        )}

        {/* Sources structurées + confiance */}
        {meta && !message.streaming && (
          <div className="flex flex-wrap items-center gap-1.5">
            <ConfidenceBadge level={meta.confidence} />
            {meta.sources
              .filter((s) => s.type !== "document")
              .map((s, i) => (
                <Badge key={i} variant="secondary">
                  {s.label}
                </Badge>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
