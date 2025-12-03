# Multi-stage build for medical-device-service
# Produces a minimal Alpine-based image < 30MB

# Stage 1: Build
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download && go mod verify

# Copy source code
COPY . .

# Build binary with optimizations
# -ldflags: Strip debug info, reduce binary size
# CGO_ENABLED=0: Static binary for Alpine
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o medical-device-service .

# Stage 2: Runtime
FROM alpine:3.19

# Install runtime dependencies
RUN apk --no-cache add ca-certificates tzdata && \
    adduser -D -u 65532 appuser

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/medical-device-service .

# Copy timezone data
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Use non-root user
USER appuser

# Expose service port
EXPOSE 8084

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8084/health || exit 1

# Run the service
ENTRYPOINT ["/app/medical-device-service"]
