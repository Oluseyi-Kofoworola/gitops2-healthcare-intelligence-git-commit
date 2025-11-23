#!/bin/bash
# Quick Reference - Common Commands for Developers

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║           GitOps 2.0 Healthcare Intelligence                      ║
║                   Quick Reference Card                            ║
╚══════════════════════════════════════════════════════════════════╝

🚀 QUICK START
──────────────
  ./setup.sh                    # First-time setup
  ./scripts/demo.sh --quick     # 5-minute demo
  ./START_HERE.md               # 30-minute walkthrough

🔧 DEVELOPMENT
──────────────
  # Generate compliant commit
  python3 tools/healthcare_commit_generator.py --interactive
  
  # Validate compliance
  python3 tools/ai_compliance_framework.py check --commit HEAD
  
  # Calculate risk score
  python3 tools/git_intel/risk_scorer.py --commit HEAD
  
  # Build all services
  go build ./services/...

🧪 TESTING
──────────
  cd tests && make test              # Run all tests
  make test-unit                     # Unit tests only
  make test-integration              # Integration tests
  make test-e2e                      # End-to-end tests
  make test-security                 # Security scans
  make test-chaos                    # Chaos engineering

  # Individual service tests
  cd services/auth-service && go test -v ./...

🐳 DOCKER
──────────
  # Start all services
  cd tests/integration && docker-compose up -d
  
  # View logs
  docker-compose logs -f auth-service
  
  # Stop services
  docker-compose down

☸️  KUBERNETES
──────────────
  # Create cluster
  kind create cluster --name gitops2
  
  # Deploy services
  kubectl apply -f k8s/
  
  # Check status
  kubectl get pods -n healthcare
  
  # Port forward
  kubectl port-forward -n healthcare svc/auth-service 8081:8080

📝 COMPLIANCE
──────────────
  # Test OPA policies
  opa test policies/healthcare/ --verbose
  
  # Validate policy syntax
  opa check policies/
  
  # Run compliance checks
  python3 tools/ai_compliance_framework.py analyze-commit HEAD

🔍 DEBUGGING
──────────────
  # Service logs
  tail -f logs/auth-service.log
  
  # Check service health
  curl http://localhost:8081/health
  
  # Run intelligent bisect
  ./scripts/intelligent-bisect.sh

📚 DOCUMENTATION
──────────────
  README.md                          # Project overview
  START_HERE.md                      # Quick walkthrough
  docs/GETTING_STARTED.md            # Complete setup
  docs/SCENARIO_END_TO_END.md        # Full scenario
  docs/DEPLOYMENT_GUIDE.md           # Production deploy
  docs/COMPLIANCE_GUIDE.md           # HIPAA/FDA/SOX

🔐 ENVIRONMENT VARIABLES
──────────────
  export OPENAI_API_KEY="sk-..."    # Required for AI features
  export AZURE_OPENAI_ENDPOINT="..." # If using Azure OpenAI
  export LOG_LEVEL="debug"           # Verbose logging

🎯 COMMON WORKFLOWS
──────────────
  # Feature development
  git checkout -b feat/my-feature
  # ... make changes ...
  python3 tools/healthcare_commit_generator.py --interactive
  git commit -F .gitops/commit_message.txt
  git push origin feat/my-feature

  # Run validation before PR
  ./scripts/validation/final-validation.sh

  # Generate incident report
  python3 tools/intelligent_bisect.py analyze --commit COMMIT_SHA

EOF
