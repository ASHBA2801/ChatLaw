FROM node:22-bookworm-slim
RUN apt-get update -y && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
COPY database/package.json ./database/package.json
COPY web/package.json ./web/package.json
RUN npm ci --workspace @chatlaw/database --include-workspace-root --fetch-retries=5 --fetch-timeout=600000
COPY database ./database
WORKDIR /app/database
CMD ["npx", "prisma", "migrate", "deploy"]
