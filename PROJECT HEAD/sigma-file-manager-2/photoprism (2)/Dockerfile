# syntax=docker/dockerfile:1

# ----------- Build Stage -----------
ARG GO_VERSION=1.24.0
FROM golang:${GO_VERSION}-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git

# Set working directory
WORKDIR /app

# Copy go.mod and go.sum first for dependency caching
COPY --link go.mod go.sum ./

# Download dependencies (use cache mounts for speed)
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download

# Copy the rest of the source code
COPY --link . .

# Build the Go binary (replace 'photoprism' with your main package if different)
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o photoprism ./cmd/photoprism

# ----------- Final Stage -----------
FROM alpine:latest AS final

# Install runtime dependencies
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache ca-certificates

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Copy the built binary from builder
COPY --from=builder /app/photoprism /app/photoprism

# Copy static assets, templates, etc. (adjust as needed)
COPY --from=builder /app/assets /app/assets
COPY --from=builder /app/static /app/static
COPY --from=builder /app/templates /app/templates

# Expose the default port (adjust if your app uses a different port)
EXPOSE 2342

# Use non-root user
USER appuser

# Set entrypoint
ENTRYPOINT ["/app/photoprism"]
