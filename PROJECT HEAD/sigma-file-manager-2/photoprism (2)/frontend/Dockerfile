# syntax=docker/dockerfile:1

ARG NODE_VERSION=22.13.1

# Build stage
FROM node:${NODE_VERSION}-slim AS builder
WORKDIR /app

# Install dependencies (npm ci is deterministic)
COPY --link package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy application source
COPY --link . .

# Build the frontend assets
RUN --mount=type=cache,target=/root/.npm \
    npm run build

# Remove dev dependencies and keep only production deps
RUN --mount=type=cache,target=/root/.npm \
    rm -rf node_modules && npm ci --production

# Production image
FROM node:${NODE_VERSION}-slim AS final
WORKDIR /app

# Create non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy built assets and production dependencies
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=4096"
USER appuser

# Expose port (adjust if your app uses a different port)
EXPOSE 3000

# Start the app (adjust if your app uses a different entrypoint)
CMD ["npx", "server", "dist", "-p", "3000"]
