# filepath: tests/Makefile
# Test Suite Makefile
# Orchestrates all testing activities for GitOps 2.0 Healthcare Platform

.PHONY: help test-all test-integration test-e2e test-load test-unit clean install-deps

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[1;33m
RED    := \033[0;31m
BLUE   := \033[0;34m
NC     := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)GitOps 2.0 - Test Suite Commands$(NC)"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

install-deps: ## Install test dependencies
	@echo "$(GREEN)Installing test dependencies...$(NC)"
	@echo "Installing Go dependencies..."
	@cd integration && go mod download
	@cd e2e && go mod download
	@cd contract && go mod download
	@echo "Installing Python dependencies..."
	@if [ ! -d "../.venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv ../.venv; \
	fi
	@echo "Installing Python packages in virtual environment..."
	@../.venv/bin/pip install --quiet locust pytest 2>/dev/null || echo "$(YELLOW)Note: Python packages can be installed with: source .venv/bin/activate && pip install locust pytest$(NC)"
	@echo "Installing Pact CLI..."
	@command -v pact-broker >/dev/null 2>&1 || npm install -g @pact-foundation/pact 2>/dev/null || brew install pact-foundation/pact-ruby/pact 2>/dev/null || echo "$(YELLOW)Note: Install Pact manually if needed$(NC)"
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

test-unit: ## Run unit tests for all services
	@echo "$(GREEN)Running unit tests...$(NC)"
	@cd ../services/auth-service && go test -v -race -cover ./...
	@cd ../services/payment-gateway && go test -v -race -cover ./...
	@cd ../services/phi-service && go test -v -race -cover ./...
	@cd ../services/medical-device && go test -v -race -cover ./...
	@cd ../services/synthetic-phi-service && go test -v -race -cover ./...
	@echo "$(GREEN)✓ Unit tests complete$(NC)"

# Aliases for compatibility with main Makefile
unit: test-unit ## Alias for test-unit
integration: test-integration ## Alias for test-integration
e2e: test-e2e ## Alias for test-e2e
all: test-all ## Alias for test-all

test-integration: ## Run integration tests (Docker Compose)
	@echo "$(GREEN)Running integration tests...$(NC)"
	@cd integration && chmod +x run-integration-tests.sh && ./run-integration-tests.sh
	@echo "$(GREEN)✓ Integration tests complete$(NC)"

test-e2e: ## Run end-to-end tests (Kubernetes)
	@echo "$(GREEN)Running E2E tests...$(NC)"
	@cd e2e && chmod +x run-e2e-tests.sh && ./run-e2e-tests.sh
	@echo "$(GREEN)✓ E2E tests complete$(NC)"

test-contract: ## Run contract tests (Pact)
	@echo "$(GREEN)Running contract tests...$(NC)"
	@cd contract && go test -v ./...
	@echo "$(GREEN)✓ Contract tests complete$(NC)"

test-load: ## Run load tests (Locust)
	@echo "$(GREEN)Running load tests...$(NC)"
	@echo "$(YELLOW)Note: Ensure services are running before load testing$(NC)"
	@cd load && chmod +x run-load-tests.sh && ./run-load-tests.sh
	@echo "$(GREEN)✓ Load tests complete$(NC)"

test-load-headless: ## Run load tests in headless mode
	@echo "$(GREEN)Running load tests (headless)...$(NC)"
	@cd load && locust -f locustfile.py \
		--host=http://localhost:8080 \
		--users=100 \
		--spawn-rate=10 \
		--run-time=5m \
		--headless \
		--html=load-test-report.html \
		--csv=load-test-results
	@echo "$(GREEN)✓ Load tests complete$(NC)"
	@echo "Report: tests/load/load-test-report.html"

test-all: install-deps test-unit test-integration test-contract ## Run all tests (unit + integration + contract)
	@echo "$(GREEN)=========================================$(NC)"
	@echo "$(GREEN)✓ ALL TESTS PASSED$(NC)"
	@echo "$(GREEN)=========================================$(NC)"

test-quick: test-unit ## Quick test (unit tests only)
	@echo "$(GREEN)✓ Quick tests complete$(NC)"

test-ci: install-deps test-unit test-integration test-contract ## CI/CD test suite
	@echo "$(GREEN)✓ CI test suite complete$(NC)"

clean: ## Clean up test artifacts
	@echo "$(YELLOW)Cleaning up test artifacts...$(NC)"
	@rm -f integration/load-test-*.html integration/load-test-*.csv
	@rm -f e2e/load-test-*.html e2e/load-test-*.csv
	@rm -f load/load-test-*.html load/load-test-*.csv
	@docker-compose -f integration/docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
	@kubectl delete namespace gitops2-e2e-test --ignore-not-found=true 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

start-services: ## Start all services via Docker Compose
	@echo "$(GREEN)Starting all services...$(NC)"
	@cd integration && docker-compose -f docker-compose.test.yml up -d
	@echo "$(YELLOW)Waiting for services to be healthy (60s)...$(NC)"
	@sleep 60
	@echo "$(GREEN)✓ Services started$(NC)"

stop-services: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	@cd integration && docker-compose -f docker-compose.test.yml down
	@echo "$(GREEN)✓ Services stopped$(NC)"

logs: ## View service logs
	@cd integration && docker-compose -f docker-compose.test.yml logs -f

status: ## Check service status
	@echo "$(GREEN)Service Status:$(NC)"
	@cd integration && docker-compose -f docker-compose.test.yml ps

health-check: ## Check health of all services
	@echo "$(GREEN)Checking service health...$(NC)"
	@echo "Auth Service:      $$(curl -s http://localhost:8080/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "Payment Gateway:   $$(curl -s http://localhost:8081/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "PHI Service:       $$(curl -s http://localhost:8083/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "Medical Device:    $$(curl -s http://localhost:8084/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "Synthetic PHI:     $$(curl -s http://localhost:8085/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"

coverage: ## Generate test coverage report
	@echo "$(GREEN)Generating coverage report...$(NC)"
	@mkdir -p coverage
	@cd ../services/auth-service && go test -coverprofile=../../tests/coverage/auth.out ./...
	@cd ../services/payment-gateway && go test -coverprofile=../../tests/coverage/payment.out ./...
	@cd ../services/phi-service && go test -coverprofile=../../tests/coverage/phi.out ./...
	@cd ../services/medical-device && go test -coverprofile=../../tests/coverage/medical-device.out ./...
	@cd ../services/synthetic-phi-service && go test -coverprofile=../../tests/coverage/synthetic-phi.out ./...
	@echo "$(GREEN)✓ Coverage reports generated in tests/coverage/$(NC)"
	@go tool cover -html=coverage/auth.out -o coverage/auth.html
	@go tool cover -html=coverage/payment.out -o coverage/payment.html
	@go tool cover -html=coverage/phi.out -o coverage/phi.html
	@go tool cover -html=coverage/medical-device.out -o coverage/medical-device.html
	@go tool cover -html=coverage/synthetic-phi.out -o coverage/synthetic-phi.html
	@echo "$(GREEN)HTML reports: tests/coverage/*.html$(NC)"

benchmark: ## Run benchmark tests
	@echo "$(GREEN)Running benchmark tests...$(NC)"
	@cd ../services/auth-service && go test -bench=. -benchmem ./...
	@cd ../services/payment-gateway && go test -bench=. -benchmem ./...
	@cd ../services/phi-service && go test -bench=. -benchmem ./...
	@cd ../services/medical-device && go test -bench=. -benchmem ./...
	@cd ../services/synthetic-phi-service && go test -bench=. -benchmem ./...
	@echo "$(GREEN)✓ Benchmarks complete$(NC)"

##############################################################################
# Security Tests
##############################################################################

test-security: ## Run all security tests
	@echo "$(BLUE)Running security test suite...$(NC)"
	@cd security && chmod +x run-security-tests.sh && ./run-security-tests.sh --all

test-owasp: ## Run OWASP ZAP security scan
	@echo "$(BLUE)Running OWASP ZAP scan...$(NC)"
	@cd security && chmod +x run-security-tests.sh && ./run-security-tests.sh --owasp

test-ssl: ## Run SSL/TLS validation tests
	@echo "$(BLUE)Running SSL/TLS tests...$(NC)"
	@cd security && chmod +x run-security-tests.sh && ./run-security-tests.sh --ssl

test-jwt: ## Run JWT security tests
	@echo "$(BLUE)Running JWT security tests...$(NC)"
	@cd security && chmod +x run-security-tests.sh && ./run-security-tests.sh --jwt

test-phi-security: ## Run PHI encryption validation
	@echo "$(BLUE)Running PHI encryption validation...$(NC)"
	@cd security && chmod +x run-security-tests.sh && ./run-security-tests.sh --phi

test-api-security: ## Run API security tests
	@echo "$(BLUE)Running API security tests...$(NC)"
	@cd security && chmod +x run-security-tests.sh && ./run-security-tests.sh --api

test-deps: ## Run dependency vulnerability scan
	@echo "$(BLUE)Running dependency vulnerability scan...$(NC)"
	@cd security && chmod +x run-security-tests.sh && ./run-security-tests.sh --deps

##############################################################################
# Chaos Engineering Tests
##############################################################################

test-chaos: ## Run chaos engineering tests
	@echo "$(BLUE)Running chaos engineering tests...$(NC)"
	@cd chaos && chmod +x run-chaos-tests.sh && ./run-chaos-tests.sh --all

chaos-pod-failure: ## Run pod failure chaos experiments
	@echo "$(BLUE)Running pod failure experiments...$(NC)"
	@cd chaos && chmod +x run-chaos-tests.sh && ./run-chaos-tests.sh --pod-failure

chaos-network: ## Run network chaos experiments
	@echo "$(BLUE)Running network chaos experiments...$(NC)"
	@cd chaos && chmod +x run-chaos-tests.sh && ./run-chaos-tests.sh --network

chaos-resource-stress: ## Run resource stress experiments
	@echo "$(BLUE)Running resource stress experiments...$(NC)"
	@cd chaos && chmod +x run-chaos-tests.sh && ./run-chaos-tests.sh --stress

.DEFAULT_GOAL := help
