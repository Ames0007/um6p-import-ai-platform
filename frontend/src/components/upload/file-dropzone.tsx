"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { UploadCloud, FileText, X } from "lucide-react";
import { cn, formatFileSize } from "@/lib/utils";
import {
  ACCEPTED_UPLOAD_EXTENSIONS,
  ACCEPTED_UPLOAD_MIME_TYPES,
  MAX_UPLOAD_SIZE_MB,
} from "@shared/constants";

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  files?: File[];
  onRemove?: (index: number) => void;
  multiple?: boolean;
  className?: string;
  /** Extensions acceptées (défaut : facture). Ex. [".pdf", ".zip"]. */
  extensions?: readonly string[];
  /** Types MIME acceptés (défaut : facture). */
  mimeTypes?: readonly string[];
  /** Taille maximale en Mo. */
  maxSizeMb?: number;
  /** Ligne d'aide affichée sous le titre. */
  hint?: string;
}

const MAX_BYTES_DEFAULT = MAX_UPLOAD_SIZE_MB * 1024 * 1024;

/**
 * Zone de dépôt de fichiers (drag & drop + sélection).
 * Accepte par défaut PDF, Excel, Word et images ; les formats peuvent être
 * surchargés via les props `extensions` / `mimeTypes`.
 */
export function FileDropzone({
  onFilesSelected,
  files = [],
  onRemove,
  multiple = true,
  className,
  extensions = ACCEPTED_UPLOAD_EXTENSIONS,
  mimeTypes = ACCEPTED_UPLOAD_MIME_TYPES,
  maxSizeMb = MAX_UPLOAD_SIZE_MB,
  hint,
}: FileDropzoneProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const accept = extensions.join(",");
  const maxBytes = maxSizeMb * 1024 * 1024 || MAX_BYTES_DEFAULT;
  const defaultHint = `PDF, Excel, Word, images · max ${maxSizeMb} Mo`;

  const validate = React.useCallback(
    (incoming: File[]) => {
      setError(null);
      const valid: File[] = [];
      for (const file of incoming) {
        const okType =
          (mimeTypes as readonly string[]).includes(file.type) ||
          extensions.some((ext) => file.name.toLowerCase().endsWith(ext));
        if (!okType) {
          setError(`Format non pris en charge : ${file.name}`);
          continue;
        }
        if (file.size > maxBytes) {
          setError(`Fichier trop volumineux (max ${maxSizeMb} Mo).`);
          continue;
        }
        valid.push(file);
      }
      if (valid.length) onFilesSelected(valid);
    },
    [onFilesSelected, extensions, mimeTypes, maxBytes, maxSizeMb]
  );

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    validate(Array.from(e.dataTransfer.files));
  };

  return (
    <div className={cn("w-full", className)}>
      <motion.div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        whileHover={{ scale: 1.005 }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-colors",
          isDragging
            ? "border-primary bg-accent"
            : "border-border bg-secondary/40 hover:border-primary/50 hover:bg-accent/60"
        )}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
          <UploadCloud className="size-6" />
        </div>
        <p className="text-sm font-medium text-foreground">
          Glissez-déposez vos fichiers ici
        </p>
        <p className="text-xs text-muted-foreground">
          ou cliquez pour parcourir · {hint ?? defaultHint}
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          className="hidden"
          onChange={(e) => {
            if (e.target.files) validate(Array.from(e.target.files));
            e.target.value = "";
          }}
        />
      </motion.div>

      {error && (
        <p className="mt-2 text-xs text-destructive" role="alert">
          {error}
        </p>
      )}

      {files.length > 0 && (
        <ul className="mt-3 space-y-2">
          {files.map((file, i) => (
            <li
              key={`${file.name}-${i}`}
              className="flex items-center gap-3 rounded-xl border bg-card px-3 py-2"
            >
              <FileText className="size-4 shrink-0 text-primary" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(file.size)}
                </p>
              </div>
              {onRemove && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove(i);
                  }}
                  className="rounded-md p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
                  aria-label={`Retirer ${file.name}`}
                >
                  <X className="size-4" />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
