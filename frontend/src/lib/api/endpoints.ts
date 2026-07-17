/**
 * Cartographie centralisée des routes de l'API (v1).
 * Les hooks React Query s'appuient sur ces constantes.
 */
export const API_ENDPOINTS = {
  health: "/health",
  chat: {
    ask: "/chat/ask",
    conversations: "/chat/conversations",
  },
  products: {
    list: "/products",
    search: "/products/search",
    byId: (id: string) => `/products/${id}`,
  },
  hsCodes: {
    list: "/hs-codes",
    search: "/hs-codes/search",
  },
  taxes: {
    byHsCode: (hsCodeId: string) => `/taxes/hs-code/${hsCodeId}`,
  },
  authorizations: {
    byHsCode: (hsCodeId: string) => `/authorizations/hs-code/${hsCodeId}`,
  },
  suppliers: {
    list: "/suppliers",
  },
  purchaseHistory: {
    list: "/purchase-history",
    byProduct: (productId: string) => `/purchase-history/product/${productId}`,
  },
  invoices: {
    list: "/invoices",
    upload: "/invoices/upload",
    byId: (id: string) => `/invoices/${id}`,
  },
  documents: {
    list: "/documents",
    import: "/documents/import",
    byId: (id: string) => `/documents/${id}`,
    progress: (id: string) => `/documents/${id}/progress`,
    reimport: (id: string) => `/documents/${id}/reimport`,
    file: (id: string, inline = false) =>
      `/documents/${id}/file?inline=${inline}`,
  },
  knowledge: {
    search: "/knowledge/search",
    lookup: "/knowledge/lookup",
    suggest: "/knowledge/suggest",
  },
  analysis: {
    list: "/import-analysis",
    upload: "/import-analysis/upload",
    byId: (id: string) => `/import-analysis/${id}`,
    progress: (id: string) => `/import-analysis/${id}/progress`,
    reanalyze: (id: string) => `/import-analysis/${id}/reanalyze`,
    export: (id: string, format: string) =>
      `/import-analysis/${id}/export?format=${format}`,
  },
  admin: {
    dashboard: "/admin/dashboard",
    search: "/admin/search",
    audit: "/admin/audit",
    importResources: "/admin/import/resources",
    importPreview: "/admin/import/preview",
    importCommit: "/admin/import/commit",
    resource: (name: string) => `/admin/${name}`,
    resourceItem: (name: string, id: string) => `/admin/${name}/${id}`,
    resourceExport: (name: string) => `/admin/${name}/export`,
    productDetail: (id: string) => `/admin/products/${id}/detail`,
    hsCodeDetail: (id: string) => `/admin/hs-codes/${id}/detail`,
  },
} as const;
