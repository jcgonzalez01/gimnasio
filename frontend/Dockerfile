# ── Etapa 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Instalar dependencias
COPY package*.json ./
RUN npm ci --prefer-offline

# Copiar código y construir
COPY . .
RUN npm run build

# ── Etapa 2: Producción con Nginx ─────────────────────────────────────────────
FROM nginx:1.27-alpine

# Config de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Assets del build
COPY --from=builder /app/dist /usr/share/nginx/html

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
