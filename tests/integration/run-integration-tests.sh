#!/bin/bash
# filepath: tests/integration/run-integration-tests.sh
# Integration Test Runner
# Starts all services via Docker Compose and runs Go integration tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================="
echo "GitOps 2.0 - Integration Test Runner"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.test.yml"
TEST_TIMEOUT="${TEST_TIMEOUT:-300s}"
CLEANUP="${CLEANUP:-true}"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

cleanup() {
    if [ "$CLEANUP" = "true" ]; then
        log_info "Cleaning up Docker Compose services..."
        cd "$PROJECT_ROOT"
        docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
        log_info "Cleanup complete"
    else
        log_warn "Skipping cleanup (CLEANUP=false)"
    fi
}

# Trap cleanup on exit
trap cleanup EXIT INT TERM

# Step 1: Check prerequisites
log_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v go &> /dev/null; then
    log_error "Go is not installed. Please install Go 1.21+ first."
    exit 1
fi

log_info "✓ All prerequisites met"
echo ""

# Step 2: Build Docker images
log_info "Building Docker images for all services..."
cd "$PROJECT_ROOT"

services=(
    "services/auth-service"
    "services/payment-gateway"
    "services/phi-service"
    "services/medical-device"
    "services/synthetic-phi-service"
)

for service in "${services[@]}"; do
    service_name=$(basename "$service")
    log_info "Building $service_name..."
    
    if [ -f "$PROJECT_ROOT/$service/Dockerfile" ]; then
        docker build -t "gitops2-$service_name:test" "$PROJECT_ROOT/$service"
    else
        log_warn "Dockerfile not found for $service_name, skipping..."
    fi
done

log_info "✓ All Docker images built"
echo ""

# Step 3: Start Docker Compose services
log_info "Starting Docker Compose services..."
cd "$PROJECT_ROOT"

docker-compose -f "$COMPOSE_FILE" up -d

log_info "Waiting for services to be healthy (60 seconds)..."
sleep 60

# Check service health
log_info "Checking service health..."
services_healthy=true

check_health() {
    local service=$1
    local port=$2
    local url="http://localhost:$port/health"
    
    if curl -sf "$url" > /dev/null 2>&1; then
        log_info "✓ $service is healthy"
        return 0
    else
        log_error "✗ $service is not healthy"
        return 1
    fi
}

check_health "Auth Service" 8080 || services_healthy=false
check_health "Payment Gateway" 8081 || services_healthy=false
check_health "PHI Service" 8083 || services_healthy=false
check_health "Medical Device" 8084 || services_healthy=false
check_health "Synthetic PHI" 8085 || services_healthy=false

if [ "$services_healthy" = false ]; then
    log_error "Some services are not healthy. Check logs with:"
    log_error "  docker-compose -f $COMPOSE_FILE logs"
    exit 1
fi

log_info "✓ All services are healthy"
echo ""

# Step 4: Run Go integration tests
log_info "Running Go integration tests..."
cd "$SCRIPT_DIR"

# Download dependencies
go mod download

# Run tests with verbose output
log_info "Executing test suite (timeout: $TEST_TIMEOUT)..."
echo ""

if go test -v -timeout "$TEST_TIMEOUT" ./...; then
    log_info ""
    log_info "========================================="
    log_info "✓ ALL INTEGRATION TESTS PASSED"
    log_info "========================================="
    exit 0
else
    log_error ""
    log_error "========================================="
    log_error "✗ INTEGRATION TESTS FAILED"
    log_error "========================================="
    log_error ""
    log_error "View service logs with:"
    log_error "  docker-compose -f $COMPOSE_FILE logs <service-name>"
    exit 1
fi
