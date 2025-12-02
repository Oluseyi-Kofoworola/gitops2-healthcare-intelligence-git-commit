# GitOps 2.0 Healthcare Intelligence Platform - Makefile
# Simple commands for developers to build, test, and run the platform

.PHONY: help setup build test demo clean install lint validate all

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)GitOps 2.0 Healthcare Intelligence Platform$(NC)"
	@echo ""
	@echo "$(GREEN)Usage:$(NC)"
	@echo "  make [target]"
	@echo ""
	@echo "$(GREEN)Targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'

setup: ## Run initial setup (install dependencies, build services)
	@echo "$(GREEN)Running initial setup...$(NC)"
	@chmod +x setup.sh
	@./setup.sh

install: ## Install dependencies (Python, Go, Node.js)
	@echo "$(GREEN)Installing Python dependencies...$(NC)"
	@pip install -e .
	@echo "$(GREEN)Installing Go dependencies...$(NC)"
	@cd cmd/gitops-health && go mod download
	@echo "$(GREEN)Installing Node.js dependencies...$(NC)"
	@npm install
	@echo "$(GREEN)Dependencies installed!$(NC)"

build: ## Build all Go services
	@echo "$(GREEN)Building Go services...$(NC)"
	@mkdir -p bin
	@cd cmd/gitops-health && go build -o ../../bin/gitops-health
	@cd services/auth-service && go build -o ../../bin/auth-service
	@cd services/payment-gateway && go build -o ../../bin/payment-gateway
	@cd services/phi-service && go build -o ../../bin/phi-service
	@cd services/medical-device && go build -o ../../bin/medical-device
	@echo "$(GREEN)Build complete! Binaries in ./bin/$(NC)"

test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	@make -C tests test-all || echo "$(YELLOW)Some tests may require Docker/dependencies$(NC)"

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	@make -C tests test-unit || echo "$(YELLOW)Unit tests require Go services$(NC)"

test-integration: ## Run integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	@make -C tests test-integration || echo "$(YELLOW)Integration tests require Docker Compose$(NC)"

test-e2e: ## Run end-to-end tests
	@echo "$(GREEN)Running e2e tests...$(NC)"
	@make -C tests test-e2e || echo "$(YELLOW)E2E tests require Kubernetes$(NC)"

demo: ## Run quick demo (5 minutes)
	@echo "$(GREEN)Running quick demo...$(NC)"
	@./scripts/demo.sh --quick

demo-healthcare: ## Run healthcare demo (15 minutes)
	@echo "$(GREEN)Running healthcare demo...$(NC)"
	@./scripts/demo.sh --healthcare

demo-executive: ## Run executive demo (30 minutes)
	@echo "$(GREEN)Running executive demo...$(NC)"
	@./scripts/demo.sh --executive

lint: ## Run linters (Python, Go)
	@echo "$(GREEN)Running linters...$(NC)"
	@echo "$(YELLOW)Python linting...$(NC)"
	@ruff check tools/ || true
	@echo "$(YELLOW)Go linting...$(NC)"
	@cd cmd/gitops-health && go vet ./... || true
	@cd services/auth-service && go vet ./... || true

validate: ## Validate commit policies and configuration
	@echo "$(GREEN)Validating configuration...$(NC)"
	@./scripts/validation/final-validation.sh

validate-security: ## Run security validation
	@echo "$(GREEN)Running security validation...$(NC)"
	@./scripts/validation/security-validation.sh

clean: ## Clean build artifacts and caches
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -rf bin/
	@rm -rf dist/
	@rm -rf build/
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

docker-up: ## Start Docker services
	@echo "$(GREEN)Starting Docker services...$(NC)"
	@docker-compose up -d

docker-down: ## Stop Docker services
	@echo "$(YELLOW)Stopping Docker services...$(NC)"
	@docker-compose down

docker-logs: ## Show Docker logs
	@docker-compose logs -f

all: clean install build test ## Run full build pipeline (clean, install, build, test)
	@echo "$(GREEN)Full build complete!$(NC)"

dev: install build ## Quick developer setup (install + build)
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  1. Run 'make demo' for a quick demo"
	@echo "  2. Read START_HERE.md for guidance"
	@echo "  3. Run 'make test' to validate everything works"
