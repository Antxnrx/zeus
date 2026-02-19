# ── Stage 1: Build ──────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@9 --activate

# Copy workspace root files for dependency resolution
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY packages/contracts/package.json packages/contracts/
COPY frontend/package.json frontend/

# Install all deps (workspace-aware)
RUN pnpm install --frozen-lockfile || pnpm install

# Copy source
COPY packages/contracts/ packages/contracts/
COPY frontend/ frontend/

# Build contracts first (if needed)
RUN cd packages/contracts && pnpm run build 2>/dev/null || true

# Build frontend
RUN cd frontend && pnpm run build

# ── Stage 2: Serve with nginx ──────────────────────────
FROM nginx:alpine AS production

# Copy built assets
COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# Copy nginx config (SPA routing + API/WS proxy)
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
