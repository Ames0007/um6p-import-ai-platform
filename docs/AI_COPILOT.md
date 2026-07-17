# Copilote IA achats & import (Phase 4)

Couche de **récupération + raisonnement** au-dessus de PostgreSQL et du dépôt
documentaire officiel. Ce n'est pas un chatbot généraliste.

## Règle absolue

Claude ne répond **jamais** avec ses connaissances propres. Chaque réponse est
ancrée dans :

1. les données structurées PostgreSQL (base UM6P) ;
2. les extraits de documents douaniers officiels.

Sans contexte vérifié → réponse figée :
> « Aucune information vérifiée n'a été trouvée dans la base de connaissances UM6P. »

Aucun code SH, droit, TVA, autorisation, ministère ou règlement n'est inventé.

## Pipeline (`backend/app/ai/`)

```
Message
  ↓  intents.py      détection d'intention (heuristique FR, sensible au suivi)
  ↓  retriever.py    PostgreSQL d'abord : produit/alias → code SH → taxes,
  ↓                  autorisations, achats, fournisseur ; puis documents
  ↓  context.py      paquet de contexte + sources + citations + confiance
  ↓  prompt.py       prompt système + messages (contexte UNIQUEMENT)
  ↓  claude_client   génération / streaming (retry, jetons) — repli déterministe
  ↓  pipeline.py     orchestration + journalisation
Réponse (Résumé · Informations trouvées · Sources · Confiance)
```

- **Intentions** : produit, code SH, taxe, autorisation, historique, fournisseur,
  recherche documentaire, achats (général), analyse de facture, indéterminé.
- **Ne jamais envoyer toute la base** : seul le contexte pertinent est transmis.
- **Sélection** : si plusieurs produits correspondent, une liste de choix est
  renvoyée (l'IA ne tranche pas).
- **Clarification** : question ambiguë → demande de précision.
- **Mémoire** : historique conservé + « focus » (dernier produit / code SH) pour
  résoudre les suivis (« Et les taxes ? »). Stocké dans `Message.sources`.
- **Repli déterministe** : sans clé API ou en cas d'échec Claude, la réponse est
  composée directement à partir du contexte (toujours ancrée, jamais inventée).

## Réponse

Format imposé (français) : **Résumé**, **Informations trouvées**, **Sources**,
**Confiance** (élevée / moyenne / faible / aucune). Les citations affichent
`Document — Chapitre — Page`.

## API

- `POST /api/v1/chat/ask` → réponse complète (`AskResponse`).
- `POST /api/v1/chat/stream` → Server-Sent Events (`meta`, `delta`, `done`).

Champs de réponse : `answer`, `conversation_id`, `intent`, `confidence`,
`sources`, `citations`, `candidates`, `needs_clarification`.

## Observabilité (`ai_request_logs`)

Chaque requête est journalisée **côté serveur** : question, intention,
enregistrements et documents récupérés (récapitulatifs), prompt, réponse, temps
d'exécution, jetons (entrée/sortie), modèle, erreur éventuelle.

## Sécurité

- Le **prompt**, le **SQL** et les **clés API** ne sont jamais renvoyés au client
  (le journal reste interne).
- Les réponses n'exposent que : texte, sources, citations, confiance.

## Configuration

`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (défaut `claude-opus-4-8`),
`AI_MAX_TOKENS`, `AI_TEMPERATURE` (0 = factuel), `AI_MAX_RETRIES`,
`AI_HISTORY_TURNS`. Sans clé, le copilote fonctionne en mode déterministe.

> L'analyse OCR de factures reste hors périmètre (phase suivante).
