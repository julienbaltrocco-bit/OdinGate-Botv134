# One image for web app, worker and migrations (same code, different command).
FROM node:22-bookworm-slim AS base
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH NEXT_TELEMETRY_DISABLED=1
RUN corepack enable && apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app

FROM base AS build
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
# Build-time placeholders only; real values come from the runtime environment.
RUN DATABASE_URL=postgres://build/none APP_ENCRYPTION_KEY=build-placeholder-build-placeholder-00 pnpm build

FROM base AS runtime
ENV NODE_ENV=production
COPY --from=build /app /app
RUN useradd --system --uid 1001 app && mkdir -p /app/data && chown -R app /app/data /app/.next
USER app
EXPOSE 3000
CMD ["pnpm", "start"]
