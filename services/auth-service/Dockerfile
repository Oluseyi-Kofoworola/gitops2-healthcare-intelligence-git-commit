# =============================================================================
# Multi-stage Dockerfile for auth-service
# Production-optimized build with minimal attack surface
# Final image size: < 25MB (Alpine-based)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build Stage
# Purpose: Compile Go binary with all dependencies
# -----------------------------------------------------------------------------
FROM golang:1.21-alpine AS builder

# Install build dependencies (git for go modules, ca-certificates for HTTPS)
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /build

# Copy go.mod and go.sum first for better layer caching
# Dependencies are downloaded only when these files change
COPY go.mod go.sum ./
RUN go mod download
RUN go mod verify

# Copy application source code
COPY *.go ./

# Build the binary with optimizations:
# - CGO_ENABLED=0: Pure Go binary (no C dependencies)
# - GOOS=linux: Target Linux OS
# - GOARCH=amd64: Target x86-64 architecture
# - -ldflags="-w -s": Strip debug info and symbol table
# - -a: Force rebuild of packages
# - -installsuffix cgo: Use separate package install suffix
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" \
    -a -installsuffix cgo \
    -o auth-service .

# Verify binary was created
RUN ls -lh /build/auth-service

# -----------------------------------------------------------------------------
# Stage 2: Runtime Stage
# Purpose: Minimal production image with only runtime essentials
# -----------------------------------------------------------------------------
FROM alpine:3.19

# Install runtime dependencies:
# - ca-certificates: HTTPS/TLS support
# - tzdata: Timezone database for accurate timestamps
RUN apk --no-cache add ca-certificates tzdata

# Create non-root user for security
# - uid=10001: Fixed UID for consistency across environments
# - /dev/null: No home directory needed
RUN adduser -D -u 10001 -s /bin/sh appuser

# Set working directory
WORKDIR /app

# Copy binary from builder stage
COPY --from=builder /build/auth-service .

# Copy timezone data for accurate logging
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Copy CA certificates for HTTPS
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose service port
# - 8083: HTTP API and health endpoints
EXPOSE 8083

# Health check configuration
# - Interval: 30s (check every 30 seconds)
# - Timeout: 10s (fail if check takes > 10 seconds)
# - Start period: 5s (grace period for startup)
# - Retries: 3 (mark unhealthy after 3 failures)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8083/health || exit 1

# Set environment variables
ENV PORT=8083
ENV LOG_LEVEL=info
ENV JWT_EXPIRY=3600

# Run the binary
ENTRYPOINT ["/app/auth-service"]

# =============================================================================
# Build Instructions:
# =============================================================================
# docker build -t auth-service:2.0.0 .
# docker build -t auth-service:latest .
#
# Run Instructions:
# =============================================================================
# docker run -d \
#   --name auth-service \
#   -p 8083:8083 \
#   -e JWT_SECRET="your-secret-key" \
#   -e OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317" \
#   auth-service:2.0.0
#
# Development Run (with logs):
# =============================================================================
# docker run --rm \
#   --name auth-service \
#   -p 8083:8083 \
#   -e JWT_SECRET="dev-secret" \
#   -e LOG_LEVEL=debug \
#   auth-service:2.0.0
#
# Security Scan:
# =============================================================================
# docker scan auth-service:2.0.0
# trivy image auth-service:2.0.0
#
# Image Size:
# =============================================================================
# docker images auth-service:2.0.0
# Expected: < 25MB (Alpine base + Go binary)
#
# =============================================================================
