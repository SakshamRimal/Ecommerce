# Stage 1: Build React + TypeScript + Tailwind v4 SPA
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies with layer caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source
COPY index.html tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts ./
COPY src/ ./src/

# Default to same-origin (/api/v1 proxied by Nginx) unless overridden at build time
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Stage 2: Production Nginx server with reverse proxy + SPA routing
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

