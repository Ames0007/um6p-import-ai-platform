# Politique de sécurité

## Versions prises en charge

| Version | Prise en charge |
|---|---|
| 1.0.x | ✅ |
| < 1.0 | ❌ |

## Signaler une vulnérabilité

**N'ouvrez PAS d'issue publique** pour une faille de sécurité.

Signalez la vulnérabilité de manière responsable et privée à l'équipe UM6P —
Département Achats, Supply Chain & Import (canal de sécurité interne UM6P).

> ⚠️ **À renseigner avant publication** : adresse e-mail de contact sécurité
> dédiée (p. ex. `security@um6p.ma`) ou lien vers l'*advisory* privé GitHub.

Merci d'inclure, dans la mesure du possible :

- une description de la vulnérabilité et de son impact ;
- les étapes de reproduction ou une preuve de concept ;
- les versions/composants affectés ;
- toute atténuation éventuelle.

Nous nous efforçons d'accuser réception sous **72 heures** et de fournir un plan
de correction après évaluation.

## Bonnes pratiques dans ce dépôt

- **Aucun secret versionné.** Les fichiers `.env` (dont `backend/.env`) sont
  ignorés par Git ; seul `.env.example` (placeholders) est fourni.
- **Aucune donnée versionnée.** Le cluster PostgreSQL récupéré
  (`database/recovered_pgdata/`) et les sauvegardes (`database/backups/`) sont
  ignorés par Git.
- **Durcissement production.** Le backend refuse de démarrer avec un `SECRET_KEY`
  ou un mot de passe par défaut, ou un CORS `*`.
- **Source de vérité.** L'IA n'invente jamais de données réglementaires ; toute
  réponse est ancrée sur PostgreSQL et les documents officiels.

## Après une exposition accidentelle de secret

1. Révoquer immédiatement le secret concerné (clé API, mot de passe, etc.).
2. Générer un nouveau secret et le déployer.
3. Purger le secret de l'historique Git si nécessaire
   (`git filter-repo` ou l'outil BFG) et forcer la rotation.
