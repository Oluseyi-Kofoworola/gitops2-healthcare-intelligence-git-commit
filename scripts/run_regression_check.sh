#!/usr/bin/env bash
set -euo pipefail

PORT=9090
MAX_LATENCY_MS=250

echo "[regression] starting payment-gateway on :$PORT"
pushd services/payment-gateway > /dev/null
go build -o /tmp/payment-gateway-test main.go server.go handlers.go config.go payment.go
PORT=$PORT MAX_PROCESSING_MILLIS=200 /tmp/payment-gateway-test &
SERVICE_PID=$!
popd > /dev/null

cleanup() {
  echo "[regression] stopping service (pid: $SERVICE_PID)"
  kill "$SERVICE_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 2

echo "[regression] health check..."
if ! curl -s -o /dev/null "http://localhost:$PORT/health"; then
  echo "[regression] service did not start properly"
  exit 1
fi

REQUEST_PAYLOAD='{"amount_cents":1000,"currency":"USD","customer_id":"cust-123","method":"card"}'
ITERATIONS=10
total_ms=0

echo "[regression] running $ITERATIONS charge requests..."
for i in $(seq 1 $ITERATIONS); do
  start=$(date +%s%3N)
  http_code=$(curl -s -o /tmp/charge_resp.json -w "%{http_code}"     -X POST     -H "Content-Type: application/json"     -d "$REQUEST_PAYLOAD"     "http://localhost:$PORT/charge")
  end=$(date +%s%3N)

  if [ "$http_code" -ne 200 ]; then
    echo "[regression] request $i failed with status $http_code"
    exit 1
  fi

  elapsed=$((end - start))
  total_ms=$((total_ms + elapsed))
  echo "[regression] request $i took ${elapsed}ms"
done

avg_ms=$((total_ms / ITERATIONS))
echo "[regression] average latency: ${avg_ms}ms"

if [ "$avg_ms" -gt "$MAX_LATENCY_MS" ]; then
  echo "[regression] latency regression detected: avg ${avg_ms}ms > max ${MAX_LATENCY_MS}ms"
  exit 1
fi

echo "[regression] performance OK"
