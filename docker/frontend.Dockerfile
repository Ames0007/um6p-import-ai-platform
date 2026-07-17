# Frontend Next.js 15 — multi-stage.
#   target `dev`    : serveur de développement (hot reload) — utilisé par docker-compose.yml
#   target `runner` : build de production (`next build` + `next start`) — docker-compose.prod.yml
#
# Le monorepo partage `../shared` (alias @shared) : il est copié en /shared.

# --- dépendances ---
FROM node:22-alpine AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# --- développement (hot reload) ---
FROM node:22-alpine AS dev
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
COPY shared/ /shared/
EXPOSE 3005
CMD ["npm", "run", "dev"]

# --- build de production ---
FROM node:22-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ARG NEXT_PUBLIC_APP_NAME="Assistant IA Import UM6P"
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
COPY shared/ /shared/
RUN npm run build

# --- runtime de production ---
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1
# Copie l'application construite (inclut .next, node_modules, config, sources).
COPY --from=build /app ./
COPY --from=build /shared /shared
EXPOSE 3005
CMD ["npm", "run", "start"]
