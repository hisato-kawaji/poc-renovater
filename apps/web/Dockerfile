FROM node:20-alpine AS builder
WORKDIR /app

# Install pnpm 9 which is compatible with Node 20
RUN npm install -g pnpm@9

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

ARG API_URL
ENV API_URL=${API_URL}

# Set Next.js to standalone output mode in next.config.ts first (or build works differently)
# We will just build normally for now, assuming next build handles it or we override
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
