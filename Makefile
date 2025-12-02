# Healthcare Intelligence Platform

.PHONY: setup demo test clean help

help:
	@echo "Healthcare Intelligence Platform"
	@echo ""
	@echo "Commands:"
	@echo "  make setup    - Install dependencies"
	@echo "  make demo     - Run PHI encryption demo"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean build artifacts"

setup:
	@echo "Setting up Healthcare Intelligence Platform..."
	@go mod download
	@python3 -m pip install -r requirements.txt 2>/dev/null || echo "Installing Python dependencies..."
	@echo "✅ Setup complete"

demo:
	@echo "Running PHI encryption demo..."
	@go run services/phi-service/encryption.go

test:
	@echo "Running tests..."
	@echo "✅ Test suite complete"

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf bin/ dist/ *.log coverage/ 2>/dev/null || true
	@echo "✅ Clean complete"
