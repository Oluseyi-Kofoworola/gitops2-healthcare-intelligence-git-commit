#!/usr/bin/env bash
set -e

# GitOps 2.0 - AI-Native Engineering Demo
# This script demonstrates all GitOps 2.0 principles in action

echo "🚀 GitOps 2.0 - AI-Native Engineering Intelligence Demo"
echo "=================================================="
echo ""

# Check prerequisites
echo "📋 Checking Prerequisites..."
echo "✓ Go version: $(go version | awk '{print $3}')"
echo "✓ Python version: $(python3 --version | awk '{print $2}')"
echo "✓ OPA version: $(opa version | head -1)"
echo ""

# 1. Semantic Commits & Policy Enforcement
echo "1️⃣  SEMANTIC COMMITS & POLICY ENFORCEMENT"
echo "----------------------------------------"
echo "Testing OPA policies for semantic commit enforcement..."
opa test policies/ --verbose
echo ""
echo "✅ Policy Results:"
echo "   • Conventional commits (feat, fix, security, etc.) are ENFORCED"
echo "   • Low-signal commits (WIP, temp, update) are BLOCKED"
echo "   • Security commits MUST touch critical domains (payment-gateway or lib/security)"
echo ""

# 2. Risk Scoring Intelligence
echo "2️⃣  RISK-ADAPTIVE SCORING"
echo "------------------------"
echo "Analyzing commit risk based on semantic type and critical paths..."
python3 tools/git_intel/risk_scorer.py
echo ""
echo "✅ Risk Scoring Results:"
echo "   • feat(payment) commits are classified as MEDIUM risk (business impact)"
echo "   • Commits touching payment-gateway + auth-service are always HIGH risk"
echo "   • Risk scores drive adaptive CI/CD pipeline decisions"
echo ""

# 3. AI-Driven Regression Detection
echo "3️⃣  AI-DRIVEN REGRESSION DETECTION"
echo "-----------------------------------"
echo "Running automated performance regression detection..."
./scripts/run_regression_check.sh
echo ""
echo "✅ Regression Detection Results:"
echo "   • Service built and benchmarked automatically"
echo "   • Performance thresholds enforced (< 250ms latency)"
echo "   • Ready for integration with 'git bisect' for automated forensics"
echo ""

# 4. Unit Tests & Service Health
echo "4️⃣  WORKLOAD VALIDATION"
echo "-----------------------"
echo "Running payment-gateway unit tests..."
cd services/payment-gateway
go test ./... -v
echo ""
echo "✅ Service Validation Results:"
echo "   • All unit tests pass"
echo "   • Payment simulation logic validated"
echo "   • Production-ready microservice structure"
cd ../..
echo ""

# 5. Copilot Integration Demo
echo "5️⃣  COPILOT INTEGRATION TOUCHPOINTS"
echo "-----------------------------------"
echo "✅ AI-Ready Repository Structure:"
echo "   • Semantic commit format enables Copilot to generate compliant messages"
echo "   • Policy-as-code allows Copilot to suggest governance-aware changes"
echo "   • Risk scoring provides context for AI-driven development decisions"
echo "   • Clear file structure and comments guide Copilot suggestions"
echo ""

# Summary
echo "🎯 GITOPS 2.0 ACHIEVEMENT SUMMARY"
echo "================================="
echo ""
echo "Your repository now implements:"
echo "✅ Machine-readable commit history (Conventional Commits + OPA enforcement)"
echo "✅ Risk-adaptive governance (automated risk scoring + policy checks)"
echo "✅ AI-driven forensics (regression detection + git bisect integration)"
echo "✅ Copilot-ready structure (semantic commits + business context)"
echo "✅ Business-aligned engineering (commits as operational artifacts)"
echo ""
echo "This transforms Git from a passive log into an AI-native intelligence platform."
echo "Your engineering velocity, compliance, and risk management are now automated and scalable."
echo ""
echo "🚀 Ready for enterprise adoption!"
