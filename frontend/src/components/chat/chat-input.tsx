"use client";

import * as React from "react";
import { ArrowUp, Paperclip, FileText, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn, formatFileSize } from "@/lib/utils";
import {
  ACCEPTED_UPLOAD_EXTENSIONS,
  ACCEPTED_UPLOAD_MIME_TYPES,
  MAX_UPLOAD_SIZE_MB,
} from "@shared/constants";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string, files: File[]) => void;
  placeholder?: string;
  disabled?: boolean;
  /** Zone de dépôt intégrée (glisser une facture directement dans le champ). */
  className?: string;
}

const ACCEPT = ACCEPTED_UPLOAD_EXTENSIONS.join(",");
const MAX_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024;

/**
 * Zone de saisie principale, façon Claude/ChatGPT.
 * Textarea auto-extensible + pièce jointe (facture) + drag & drop.
 */
export function ChatInput({
  value,
  onChange,
  onSubmit,
  placeholder = "Posez votre question...",
  disabled,
  className,
}: ChatInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [files, setFiles] = React.useState<File[]>([]);
  const [isDragging, setIsDragging] = React.useState(false);

  // Auto-resize du textarea.
  React.useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const addFiles = (incoming: File[]) => {
    const valid = incoming.filter(
      (f) =>
        f.size <= MAX_BYTES &&
        ((ACCEPTED_UPLOAD_MIME_TYPES as readonly string[]).includes(f.type) ||
          ACCEPTED_UPLOAD_EXTENSIONS.some((ext) =>
            f.name.toLowerCase().endsWith(ext)
          ))
    );
    if (valid.length) setFiles((prev) => [...prev, ...valid]);
  };

  const submit = () => {
    if (disabled) return;
    if (!value.trim() && files.length === 0) return;
    onSubmit(value.trim(), files);
    setFiles([]);
  };

  return (
    <div className={cn("w-full", className)}>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          addFiles(Array.from(e.dataTransfer.files));
        }}
        className={cn(
          "rounded-2xl border bg-card shadow-sm transition-all focus-within:ring-2 focus-within:ring-ring",
          isDragging && "border-primary ring-2 ring-primary"
        )}
      >
        {/* Pièces jointes */}
        {files.length > 0 && (
          <div className="flex flex-wrap gap-2 border-b p-3">
            {files.map((file, i) => (
              <div
                key={`${file.name}-${i}`}
                className="flex items-center gap-2 rounded-lg bg-secondary px-2.5 py-1.5 text-xs"
              >
                <FileText className="size-3.5 text-primary" />
                <span className="max-w-[160px] truncate font-medium">
                  {file.name}
                </span>
                <span className="text-muted-foreground">
                  {formatFileSize(file.size)}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    setFiles((prev) => prev.filter((_, idx) => idx !== i))
                  }
                  className="text-muted-foreground hover:text-foreground"
                  aria-label={`Retirer ${file.name}`}
                >
                  <X className="size-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-end gap-2 p-2.5">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="shrink-0 text-muted-foreground"
            onClick={() => fileInputRef.current?.click()}
            aria-label="Joindre une facture"
          >
            <Paperclip className="size-5" />
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPT}
            multiple
            className="hidden"
            onChange={(e) => {
              if (e.target.files) addFiles(Array.from(e.target.files));
              e.target.value = "";
            }}
          />

          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            rows={1}
            placeholder={placeholder}
            disabled={disabled}
            className="max-h-[200px] flex-1 resize-none bg-transparent py-2 text-sm outline-none placeholder:text-muted-foreground disabled:opacity-60"
          />

          <Button
            type="button"
            size="icon"
            className="shrink-0"
            onClick={submit}
            disabled={disabled || (!value.trim() && files.length === 0)}
            aria-label="Envoyer"
          >
            <ArrowUp className="size-5" />
          </Button>
        </div>
      </div>

      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        className="mt-2 inline-flex items-center gap-1.5 px-1 text-xs text-muted-foreground transition-colors hover:text-primary"
      >
        <Paperclip className="size-3.5" />
        Joindre une facture
      </button>
    </div>
  );
}
