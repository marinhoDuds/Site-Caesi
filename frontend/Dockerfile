# Multi-stage Dockerfile for Vue 3 Frontend

# Stage 1: Build Vue 3 static assets
FROM node:20-alpine AS builder

WORKDIR /app

# Install package dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy project files and build
COPY . .
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Production Nginx Server
FROM nginx:1.27-alpine AS runner

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy custom Nginx SPA configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build artifacts from builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
