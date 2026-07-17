/**
 * Sélection de mode côté client : décide si une requête relève de la RECHERCHE
 * directe (Index de connaissance, sans IA) ou du RAISONNEMENT (Assistant IA).
 *
 * Règle : seule une intention explicite de comparaison / explication / analyse
 * appelle l'IA. Tout le reste (code SH, produit, chapitre, document, terme
 * simple, même formulé en question « Quel est le code SH de… ») est une
 * recherche instantanée dans l'Index de connaissance.
 */

const REASONING_RE =
  /\b(compar\w*|pourquoi|explique\w*|expliqu\w*|r[ée]sum\w*|diff[ée]renc\w*|analys\w*|similaire\w*|semblable\w*|versus|vs|avantage\w*|inconv[ée]nient\w*|recommand\w*|conseill\w*|équivalent\w*|equivalent\w*|difference between|what is the difference|why does|explain|compare|summar\w*)\b/i;

/** True si la requête nécessite un raisonnement (⇒ Assistant IA). */
export function isReasoningQuery(query: string): boolean {
  const q = (query || "").trim();
  if (!q) return false;
  // Un code SH explicite n'est jamais du raisonnement.
  if (/^\d{2,4}\.\d{2}(?:\.\d{2}){0,2}$/.test(q)) return false;
  return REASONING_RE.test(q);
}

/** Destination de navigation pour une requête donnée. */
export function routeForQuery(query: string): string {
  const q = encodeURIComponent(query.trim());
  return isReasoningQuery(query) ? `/conversation?q=${q}` : `/recherche?q=${q}`;
}
