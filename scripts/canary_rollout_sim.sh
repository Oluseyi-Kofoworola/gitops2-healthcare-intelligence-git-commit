#!/usr/bin/env bash
set -euo pipefail
# Canary rollout simulation for payment-gateway.
# WHY: Demonstrates risk-adaptive staged deployment for GitOps 2.0.

SERVICE=payment-gateway
PORT=${PORT:-8080}
IMAGE=${IMAGE:-gitops2-demo/$SERVICE:local}

stages=(5 25 100)

simulate_health() {
  # Placeholder: would query real metrics & error rate.
  curl -sf "http://localhost:$PORT/health" >/dev/null || return 1
  return 0
}

for pct in "${stages[@]}"; do
  echo "[canary] Deploying stage: ${pct}% traffic"
  sleep 2
  if ! simulate_health; then
    echo "[canary] Health check failed at ${pct}% - initiating rollback"
    exit 1
  fi
  echo "[canary] Stage ${pct}% healthy"
 done

 echo "[canary] Rollout complete"
