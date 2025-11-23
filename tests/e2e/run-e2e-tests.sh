#!/bin/bash
# filepath: tests/e2e/run-e2e-tests.sh
# End-to-End Test Runner for Kubernetes
# Deploys services to Kubernetes and runs E2E tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================="
echo "GitOps 2.0 - E2E Test Runner (Kubernetes)"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${TEST_NAMESPACE:-gitops2-e2e-test}"
KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"
CLEANUP="${CLEANUP:-true}"
TEST_TIMEOUT="${TEST_TIMEOUT:-600s}"

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

cleanup() {
    if [ "$CLEANUP" = "true" ]; then
        log_info "Cleaning up Kubernetes resources..."
        kubectl delete namespace "$NAMESPACE" --ignore-not-found=true --wait=true
        log_info "Cleanup complete"
    else
        log_warn "Skipping cleanup (CLEANUP=false)"
        log_warn "To manually cleanup: kubectl delete namespace $NAMESPACE"
    fi
}

# Trap cleanup on exit
trap cleanup EXIT INT TERM

# Step 1: Check prerequisites
log_step "Step 1: Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

if ! command -v go &> /dev/null; then
    log_error "Go is not installed. Please install Go 1.21+ first."
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

log_info "✓ All prerequisites met"
log_info "  Kubernetes cluster: $(kubectl config current-context)"
echo ""

# Step 2: Create test namespace
log_step "Step 2: Creating test namespace..."

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace "$NAMESPACE" environment=e2e-test --overwrite

log_info "✓ Namespace created: $NAMESPACE"
echo ""

# Step 3: Deploy services to Kubernetes
log_step "Step 3: Deploying services to Kubernetes..."

services=(
    "auth-service"
    "payment-gateway"
    "phi-service"
    "medical-device"
    "synthetic-phi-service"
)

for service in "${services[@]}"; do
    log_info "Deploying $service..."
    
    if [ -f "$PROJECT_ROOT/services/$service/k8s/deployment.yaml" ]; then
        # Apply Kubernetes manifests
        kubectl apply -f "$PROJECT_ROOT/services/$service/k8s/" -n "$NAMESPACE"
    else
        log_warn "Kubernetes manifests not found for $service, skipping..."
    fi
done

log_info "✓ All services deployed"
echo ""

# Step 4: Wait for services to be ready
log_step "Step 4: Waiting for services to be ready..."

for service in "${services[@]}"; do
    log_info "Waiting for $service to be ready..."
    
    if kubectl get deployment "$service" -n "$NAMESPACE" &> /dev/null; then
        kubectl wait --for=condition=available \
            --timeout=300s \
            deployment/"$service" \
            -n "$NAMESPACE"
        log_info "✓ $service is ready"
    else
        log_warn "$service deployment not found, skipping..."
    fi
done

echo ""

# Step 5: Port-forward services
log_step "Step 5: Setting up port forwarding..."

# Kill any existing port-forwards
pkill -f "kubectl port-forward" || true
sleep 2

# Start port-forwarding in background
declare -A SERVICE_PORTS=(
    ["auth-service"]=8080
    ["payment-gateway"]=8081
    ["phi-service"]=8083
    ["medical-device"]=8084
    ["synthetic-phi-service"]=8085
)

for service in "${services[@]}"; do
    port="${SERVICE_PORTS[$service]}"
    log_info "Port-forwarding $service to localhost:$port..."
    
    if kubectl get service "$service" -n "$NAMESPACE" &> /dev/null; then
        kubectl port-forward -n "$NAMESPACE" "service/$service" "$port:$port" &
        sleep 1
    else
        log_warn "$service service not found, skipping port-forward..."
    fi
done

log_info "✓ Port forwarding established"
log_info "Waiting 10 seconds for port-forwards to stabilize..."
sleep 10
echo ""

# Step 6: Run E2E tests
log_step "Step 6: Running E2E tests..."

cd "$SCRIPT_DIR"

# Download dependencies
go mod download

# Set environment variables for tests
export BASE_URL="http://localhost"
export AUTH_PORT="8080"
export PAYMENT_PORT="8081"
export PHI_PORT="8083"
export DEVICE_PORT="8084"
export SYNTHETIC_PORT="8085"

log_info "Executing E2E test suite (timeout: $TEST_TIMEOUT)..."
echo ""

if go test -v -timeout "$TEST_TIMEOUT" ./...; then
    log_info ""
    log_info "========================================="
    log_info "✓ ALL E2E TESTS PASSED"
    log_info "========================================="
    exit 0
else
    log_error ""
    log_error "========================================="
    log_error "✗ E2E TESTS FAILED"
    log_error "========================================="
    log_error ""
    log_error "View pod logs with:"
    log_error "  kubectl logs -n $NAMESPACE <pod-name>"
    log_error ""
    log_error "View all pods:"
    log_error "  kubectl get pods -n $NAMESPACE"
    exit 1
fi
