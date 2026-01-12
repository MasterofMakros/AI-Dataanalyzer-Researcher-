# =============================================================================
# Mission Control v2 - Neural Search UI
# Multi-stage build for production React app
# =============================================================================

# Stage 1: Build
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY mission_control_v2/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY mission_control_v2/ ./

# Build for production
RUN npm run build

# Stage 2: Production with nginx
FROM nginx:alpine AS production

# Copy custom nginx config
COPY docker/mission-control/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
