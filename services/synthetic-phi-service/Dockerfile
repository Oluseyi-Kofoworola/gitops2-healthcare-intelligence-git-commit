# Multi-stage build for synthetic-phi-service
# WHY: Optimized container size and security - ~20MB final image vs ~800MB with full Go
# PRODUCTION-READY: Distroless base for minimal attack surface

# Stage 1: Build the Go binary
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates

WORKDIR /build

# Copy go mod files first for better caching
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY *.go ./

# Build static binary with all optimizations
# CGO_ENABLED=0 for static linking
# -ldflags for smaller binary size
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o synthetic-phi-service .

# Stage 2: Create minimal production image
FROM gcr.io/distroless/static-debian11:nonroot

# Copy CA certificates for HTTPS
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy compiled binary
COPY --from=builder /build/synthetic-phi-service /app/synthetic-phi-service

# Use non-root user (provided by distroless/nonroot)
USER nonroot:nonroot

# Service listens on 8081
EXPOSE 8081

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/app/synthetic-phi-service", "health"] || exit 1

# Metadata labels following OCI standards
LABEL org.opencontainers.image.title="Synthetic PHI Service" \
      org.opencontainers.image.description="Production-grade synthetic patient data generator for HIPAA compliance testing" \
      org.opencontainers.image.vendor="GitOps 2.0 Enterprise" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.source="https://github.com/your-org/gitops2-enterprise" \
      compliance="HIPAA,SOX" \
      security.scan="required" \
      deployment.strategy="blue-green,canary"

# Run the service
ENTRYPOINT ["/app/synthetic-phi-service"]
