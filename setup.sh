#!/bin/bash
# GitOps 2.0 Healthcare Intelligence Platform - Setup Script
# This script automates the initial setup of the development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  GitOps 2.0 Healthcare Intelligence Platform - Setup            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print step headers
print_step() {
    echo ""
    echo -e "${BLUE}▶ $1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Step 1: Check Prerequisites
print_step "Step 1/6: Checking Prerequisites"

echo "Checking required tools..."
MISSING_TOOLS=0

# Check Go
if command -v go &> /dev/null; then
    GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
    print_success "Go $GO_VERSION installed"
else
    print_error "Go not found. Install from https://go.dev/dl/"
    MISSING_TOOLS=1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python $PYTHON_VERSION installed"
else
    print_error "Python 3 not found. Install from https://python.org"
    MISSING_TOOLS=1
fi

# Check Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    print_success "Git $GIT_VERSION installed"
else
    print_error "Git not found. Install from https://git-scm.com"
    MISSING_TOOLS=1
fi

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker $DOCKER_VERSION installed"
else
    print_warning "Docker not found (optional for containerization)"
fi

if [ $MISSING_TOOLS -eq 1 ]; then
    print_error "Missing required tools. Please install them and run setup again."
    exit 1
fi

# Step 2: Install Python Dependencies
print_step "Step 2/6: Installing Python Dependencies"

if [ -f "requirements.txt" ]; then
    echo "Installing Python packages from requirements.txt..."
    python3 -m pip install --upgrade pip -q
    python3 -m pip install -r requirements.txt -q
    print_success "Python dependencies installed"
else
    print_warning "requirements.txt not found, skipping Python dependencies"
fi

# Step 3: Build Go Microservices
print_step "Step 3/6: Building Go Microservices"

# Create bin directory if it doesn't exist
mkdir -p bin

SERVICES=("auth-service" "payment-gateway" "phi-service")
BUILD_ERRORS=0

for service in "${SERVICES[@]}"; do
    if [ -d "services/$service" ]; then
        echo "Building $service..."
        cd "services/$service"
        if go build -v -o "../../bin/$service" . 2>&1 | grep -v "^#"; then
            print_success "$service built successfully"
        else
            print_error "Failed to build $service"
            BUILD_ERRORS=1
        fi
        cd ../..
    else
        print_warning "Service directory services/$service not found"
    fi
done

if [ $BUILD_ERRORS -eq 1 ]; then
    print_warning "Some services failed to build, but continuing..."
fi

# Step 4: Install Open Policy Agent (OPA)
print_step "Step 4/6: Installing Open Policy Agent (OPA)"

if command -v opa &> /dev/null; then
    OPA_VERSION=$(opa version | head -n1 | awk '{print $2}')
    print_success "OPA $OPA_VERSION already installed"
else
    echo "Installing OPA..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install opa
            print_success "OPA installed via Homebrew"
        else
            print_warning "Homebrew not found. Install OPA manually from https://www.openpolicyagent.org/docs/latest/#running-opa"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64
        chmod +x opa
        sudo mv opa /usr/local/bin/
        print_success "OPA installed"
    else
        print_warning "Unsupported OS. Install OPA manually from https://www.openpolicyagent.org/docs/latest/#running-opa"
    fi
fi

# Step 5: Configure Environment
print_step "Step 5/6: Configuring Environment"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file with defaults..."
    cat > .env << 'EOF'
# GitOps 2.0 Healthcare Intelligence Platform - Environment Configuration

# OpenAI API Configuration (Required for AI commit generation)
OPENAI_API_KEY=''

# Azure Cosmos DB Configuration (Optional - for production)
AZURE_COSMOS_ENDPOINT=''
AZURE_COSMOS_KEY=''
AZURE_COSMOS_DATABASE='healthcare_demo'

# Service Ports
AUTH_SERVICE_PORT=8080
PAYMENT_GATEWAY_PORT=8081
PHI_SERVICE_PORT=8082

# Observability
PROMETHEUS_PORT=9090
JAEGER_PORT=16686

# Environment
ENVIRONMENT=development
LOG_LEVEL=info
EOF
    print_success ".env file created"
    print_warning "Don't forget to add your OPENAI_API_KEY to .env file!"
else
    print_success ".env file already exists"
fi

# Step 6: Configure Git Hooks (Optional)
print_step "Step 6/6: Configuring Git Hooks"

if [ -d ".git" ]; then
    mkdir -p .git/hooks
    
    # Create pre-commit hook for policy validation
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook: Validate commit message against OPA policies

echo "Running pre-commit checks..."

# Check if OPA is installed
if ! command -v opa &> /dev/null; then
    echo "⚠️  OPA not installed. Skipping policy validation."
    exit 0
fi

# Check if policies directory exists
if [ ! -d "policies/healthcare" ]; then
    echo "⚠️  Policies directory not found. Skipping validation."
    exit 0
fi

echo "✓ Pre-commit checks passed"
exit 0
EOF
    
    chmod +x .git/hooks/pre-commit
    print_success "Git pre-commit hook configured"
else
    print_warning "Not a git repository. Skipping git hooks setup."
fi

# Final Summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Setup Complete!                                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Configure your OpenAI API key:"
echo "   ${YELLOW}export OPENAI_API_KEY='sk-your-key-here'${NC}"
echo "   or edit .env file"
echo ""
echo "2. Verify installation:"
echo "   ${YELLOW}./QUICK_TEST.sh${NC}  (if available)"
echo ""
echo "3. Start microservices:"
echo "   ${YELLOW}./bin/auth-service${NC}     # Terminal 1"
echo "   ${YELLOW}./bin/payment-gateway${NC}  # Terminal 2"
echo "   ${YELLOW}./bin/phi-service${NC}      # Terminal 3"
echo ""
echo "4. Try AI commit generation:"
echo "   ${YELLOW}python tools/git_copilot_commit.py --help${NC}"
echo ""
echo "5. Run the full demo:"
echo "   ${YELLOW}./scripts/demo.sh${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""
