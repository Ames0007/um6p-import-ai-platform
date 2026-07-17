-- Extensions PostgreSQL requises.
-- Exécuté automatiquement au premier démarrage du conteneur postgres.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector (recherche sémantique)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- recherche floue / similarité texte
