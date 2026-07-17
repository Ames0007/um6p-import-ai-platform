"use client";

import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useResourceOptions } from "@/hooks/use-admin";
import type { FieldConfig } from "@/config/admin-resources";
import type { ResourceRecord } from "@/types/admin";

interface ResourceFormProps {
  title: string;
  fields: FieldConfig[];
  initial?: ResourceRecord | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onSubmit: (body: Record<string, unknown>) => Promise<void> | void;
  pending?: boolean;
}

const selectClass =
  "h-10 w-full rounded-lg border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

function toInitialValue(field: FieldConfig, initial?: ResourceRecord | null): string {
  const raw = initial?.[field.name];
  if (raw == null) return "";
  if (field.type === "keywords" && Array.isArray(raw)) return raw.join(", ");
  if (field.type === "date" || field.type === "datetime") {
    return String(raw).slice(0, 10);
  }
  return String(raw);
}

function RelationField({
  field,
  value,
  onChange,
}: {
  field: FieldConfig;
  value: string;
  onChange: (v: string) => void;
}) {
  const { data: options, isLoading } = useResourceOptions(
    field.relation?.resource,
    field.relation?.labelKey ?? "id"
  );
  return (
    <select
      className={selectClass}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">
        {isLoading ? "Chargement…" : "— Aucun —"}
      </option>
      {(options ?? []).map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

export function ResourceForm({
  title,
  fields,
  initial,
  open,
  onOpenChange,
  onSubmit,
  pending,
}: ResourceFormProps) {
  const [values, setValues] = React.useState<Record<string, string>>({});
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (open) {
      const init: Record<string, string> = {};
      for (const f of fields) init[f.name] = toInitialValue(f, initial);
      setValues(init);
      setError(null);
    }
  }, [open, fields, initial]);

  const set = (name: string, v: string) =>
    setValues((prev) => ({ ...prev, [name]: v }));

  const handleSubmit = async () => {
    setError(null);
    for (const f of fields) {
      if (f.required && !values[f.name]?.trim()) {
        setError(`Le champ « ${f.label} » est obligatoire.`);
        return;
      }
    }
    const body: Record<string, unknown> = {};
    for (const f of fields) {
      const raw = values[f.name]?.trim() ?? "";
      if (raw === "") {
        if (f.type === "keywords") body[f.name] = [];
        continue;
      }
      if (f.type === "number") body[f.name] = Number(raw);
      else if (f.type === "keywords")
        body[f.name] = raw.split(",").map((s) => s.trim()).filter(Boolean);
      else body[f.name] = raw;
    }
    await onSubmit(body);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {fields.map((field) => {
            const full =
              field.type === "textarea" || field.type === "keywords";
            return (
              <div
                key={field.name}
                className={full ? "sm:col-span-2" : undefined}
              >
                <label className="mb-1.5 block text-sm font-medium">
                  {field.label}
                  {field.required && <span className="text-primary"> *</span>}
                </label>

                {field.type === "textarea" ? (
                  <Textarea
                    rows={3}
                    value={values[field.name] ?? ""}
                    onChange={(e) => set(field.name, e.target.value)}
                  />
                ) : field.type === "select" ? (
                  <select
                    className={selectClass}
                    value={values[field.name] ?? ""}
                    onChange={(e) => set(field.name, e.target.value)}
                  >
                    <option value="">— Choisir —</option>
                    {field.options?.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                ) : field.type === "relation" ? (
                  <RelationField
                    field={field}
                    value={values[field.name] ?? ""}
                    onChange={(v) => set(field.name, v)}
                  />
                ) : (
                  <Input
                    type={
                      field.type === "number"
                        ? "number"
                        : field.type === "date"
                          ? "date"
                          : "text"
                    }
                    value={values[field.name] ?? ""}
                    onChange={(e) => set(field.name, e.target.value)}
                    placeholder={
                      field.type === "keywords" ? "séparés par des virgules" : ""
                    }
                  />
                )}
              </div>
            );
          })}
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button onClick={handleSubmit} disabled={pending}>
            {pending ? "Enregistrement…" : "Enregistrer"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
