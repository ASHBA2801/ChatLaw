FROM node:22-bookworm-slim AS base
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

FROM base AS deps
COPY package.json package-lock.json ./
COPY web/package.json ./web/package.json
COPY database/package.json ./database/package.json
RUN npm ci --fetch-retries=5 --fetch-timeout=600000

# Development target for docker-compose.dev.yml: the source is bind-mounted over
# /app/web and `next dev` hot reloads it. Dependencies stay in the image.
FROM deps AS dev
ENV NODE_ENV=development
# .next and the case-document store are volumes; make them writable for whichever
# UID Compose runs as.
RUN mkdir -p /app/web/.next /data/case-documents \
    && chmod 777 /app/web/.next /data/case-documents
WORKDIR /app/web
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY web ./web
COPY database ./database
ENV NODE_ENV=production \
    DOCKER_BUILD=1
# Satisfies the production auth check while Next compiles routes.
# The running container uses the real AUTH_SECRET from Compose.
ENV AUTH_SECRET=docker-build-auth-secret-not-for-runtime-use
ENV AUTH_TRUST_HOST=true
RUN npm run build --workspace @chatlaw/web -- --webpack

FROM base AS runner
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0 \
    CASE_STORAGE_ROOT=/data/case-documents
RUN groupadd --system --gid 1001 nodejs \
    && useradd --system --uid 1001 --gid nodejs nextjs \
    && mkdir -p /data/case-documents \
    && chown -R nextjs:nodejs /data/case-documents
COPY --from=builder /app/web/public ./web/public
COPY --from=builder --chown=nextjs:nodejs /app/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/web/.next/static ./web/.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "web/server.js"]
