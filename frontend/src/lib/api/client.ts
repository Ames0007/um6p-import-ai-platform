/**
 * Client HTTP minimal et typé pour l'API backend.
 * Aucune logique métier ici : uniquement le transport.
 *
 * Résilience (Phase 5) :
 *  - délai d'expiration via AbortController (évite les requêtes suspendues) ;
 *  - les échecs réseau (backend injoignable / CORS) sont convertis en
 *    `ApiError(0, "network")` — un statut 0 signale « hors ligne ».
 */

/** URL de base de l'API (exportée pour les sondes de connexion). */
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const API_URL = API_BASE;

/** Délai d'expiration par défaut d'une requête (ms). */
const DEFAULT_TIMEOUT_MS = 20_000;

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }

  /** Vrai si l'erreur est une panne réseau / backend injoignable. */
  get isNetwork(): boolean {
    return this.status === 0;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Jeton JWT (préparé pour l'authentification future). */
  token?: string;
  /** Délai d'expiration en ms (0 = aucun). */
  timeoutMs?: number;
}

async function request<T>(
  path: string,
  { body, token, headers, timeoutMs = DEFAULT_TIMEOUT_MS, signal, ...init }: RequestOptions = {}
): Promise<T> {
  const isFormData = body instanceof FormData;

  // Délai d'expiration : combine un signal appelant éventuel + un timer.
  const controller = new AbortController();
  const timer =
    timeoutMs > 0 ? setTimeout(() => controller.abort(), timeoutMs) : undefined;
  if (signal) {
    signal.addEventListener("abort", () => controller.abort(), { once: true });
  }

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: isFormData ? (body as FormData) : body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    // fetch rejette (TypeError) si le backend est injoignable, en cas de CORS
    // bloqué, ou d'abort/timeout : on normalise en ApiError réseau (status 0).
    const aborted = err instanceof DOMException && err.name === "AbortError";
    throw new ApiError(
      0,
      aborted ? "Délai dépassé — le serveur ne répond pas." : "Serveur injoignable.",
      err
    );
  } finally {
    if (timer) clearTimeout(timer);
  }

  if (!res.ok) {
    let details: unknown;
    try {
      details = await res.json();
    } catch {
      details = await res.text();
    }
    throw new ApiError(res.status, `Erreur API (${res.status})`, details);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const apiClient = {
  get: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: "GET" }),
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: "POST", body }),
  put: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: "PUT", body }),
  patch: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: "PATCH", body }),
  delete: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: "DELETE" }),
};
