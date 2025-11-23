#!/bin/bash
# filepath: tests/load/run-load-tests.sh
# Load Testing Runner using Locust

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "GitOps 2.0 - Load Testing Runner"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
USERS="${USERS:-100}"
SPAWN_RATE="${SPAWN_RATE:-10}"
RUN_TIME="${RUN_TIME:-5m}"
HOST="${HOST:-http://localhost:8080}"

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    log_error "pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Install Locust if not installed
if ! python3 -c "import locust" &> /dev/null; then
    log_info "Installing Locust..."
    pip3 install locust
fi

log_info "✓ All prerequisites met"
echo ""

# Display configuration
log_info "Load Test Configuration:"
log_info "  Users:        $USERS"
log_info "  Spawn Rate:   $SPAWN_RATE users/sec"
log_info "  Run Time:     $RUN_TIME"
log_info "  Target Host:  $HOST"
echo ""

# Ask user to select test scenario
echo "Available test scenarios:"
echo "  1) Complete Healthcare Workflow (CompleteWorkflowUser)"
echo "  2) Auth Service Only (AuthServiceUser)"
echo "  3) Payment Gateway Only (PaymentGatewayUser)"
echo "  4) PHI Service Only (PHIServiceUser)"
echo "  5) Medical Device Only (MedicalDeviceUser)"
echo "  6) Synthetic PHI Only (SyntheticPHIUser)"
echo "  7) All Services Mixed (Run all user types)"
echo ""

read -p "Select scenario [1-7, default=1]: " scenario
scenario="${scenario:-1}"

# Map scenario to Locust user class
case $scenario in
    1)
        USER_CLASS="CompleteWorkflowUser"
        log_info "Running Complete Healthcare Workflow test..."
        ;;
    2)
        USER_CLASS="AuthServiceUser"
        log_info "Running Auth Service load test..."
        ;;
    3)
        USER_CLASS="PaymentGatewayUser"
        log_info "Running Payment Gateway load test..."
        ;;
    4)
        USER_CLASS="PHIServiceUser"
        log_info "Running PHI Service load test..."
        ;;
    5)
        USER_CLASS="MedicalDeviceUser"
        log_info "Running Medical Device Service load test..."
        ;;
    6)
        USER_CLASS="SyntheticPHIUser"
        log_info "Running Synthetic PHI Service load test..."
        ;;
    7)
        USER_CLASS=""
        log_info "Running mixed load test (all services)..."
        ;;
    *)
        log_error "Invalid scenario selection"
        exit 1
        ;;
esac

echo ""
log_info "Starting Locust load test..."
log_info "Press CTRL+C to stop the test"
echo ""

# Run Locust
cd "$SCRIPT_DIR"

if [ -z "$USER_CLASS" ]; then
    # Run all user classes
    locust -f locustfile.py \
        --host="$HOST" \
        --users="$USERS" \
        --spawn-rate="$SPAWN_RATE" \
        --run-time="$RUN_TIME" \
        --headless \
        --html=load-test-report.html \
        --csv=load-test-results
else
    # Run specific user class
    locust -f locustfile.py \
        --host="$HOST" \
        --users="$USERS" \
        --spawn-rate="$SPAWN_RATE" \
        --run-time="$RUN_TIME" \
        --headless \
        --html=load-test-report.html \
        --csv=load-test-results \
        "$USER_CLASS"
fi

log_info ""
log_info "========================================="
log_info "✓ LOAD TEST COMPLETE"
log_info "========================================="
log_info "Report: $SCRIPT_DIR/load-test-report.html"
log_info "CSV Results: $SCRIPT_DIR/load-test-results*.csv"
log_info "========================================="
