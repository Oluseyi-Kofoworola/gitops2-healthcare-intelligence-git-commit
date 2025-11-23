#!/bin/bash

################################################################################
# GitOps 2.0 Healthcare Intelligence - Setup Script
# Quick setup for developers and engineers
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  GitOps 2.0 Healthcare Intelligence - Setup               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { print_error "Python 3.9+ required"; exit 1; }
command -v go >/dev/null 2>&1 || { print_error "Go 1.21+ required"; exit 1; }
command -v git >/dev/null 2>&1 || { print_error "Git 2.30+ required"; exit 1; }
command -v docker >/dev/null 2>&1 || print_info "Docker not found (optional for demos)"

print_success "Prerequisites check passed"

# Install Python dependencies
print_info "Installing Python dependencies..."
pip3 install -r requirements.txt >/dev/null 2>&1 || pip3 install openai pyyaml requests

print_success "Python dependencies installed"

# Install Go dependencies
print_info "Installing Go dependencies..."
go mod download

print_success "Go dependencies installed"

# Install Node dependencies (for commit linting)
if command -v npm >/dev/null 2>&1; then
    print_info "Installing Node dependencies..."
    npm install --silent
    print_success "Node dependencies installed"
fi

# Create config from example
if [ ! -f "config/gitops-health.yml" ]; then
    print_info "Creating config file..."
    cp config/gitops-health.example.yml config/gitops-health.yml
    print_success "Config file created: config/gitops-health.yml"
    print_info "⚠️  Remember to set OPENAI_API_KEY in your environment"
fi

# Build services
print_info "Building Go services..."
for service in services/*/; do
    if [ -f "$service/go.mod" ]; then
        service_name=$(basename "$service")
        (cd "$service" && go build -o "../../bin/$service_name" . 2>/dev/null) && \
            print_success "Built $service_name" || \
            print_info "Skipped $service_name (no main package)"
    fi
done

# Create necessary directories
mkdir -p bin reports .gitops

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Setup Complete! ✨                                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
print_info "Next steps:"
echo "  1. Set your OpenAI API key: export OPENAI_API_KEY='your-key'"
echo "  2. Run quick demo: ./scripts/demo.sh --quick"
echo "  3. Read: START_HERE.md for 30-minute walkthrough"
echo ""
print_info "Documentation:"
echo "  - README.md - Main overview"
echo "  - START_HERE.md - Quick walkthrough"
echo "  - docs/ - Detailed guides"
echo ""
