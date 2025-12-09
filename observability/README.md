# Observability Configuration

Grafana dashboards and Prometheus configurations for monitoring the healthcare platform.

---

## Quick Start

### Deploy Monitoring Stack (Local)

```bash
# Using Docker Compose
cd tests/integration
docker-compose up -d prometheus grafana

# Access Grafana
open http://localhost:3000  # admin/admin
```

### Deploy to Kubernetes

```bash
# Install Prometheus + Grafana
kubectl create namespace monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Get Grafana password
kubectl get secret -n monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d

# Port-forward
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

---

## Dashboards

Pre-configured dashboards in `observability/dashboards/`:

- `platform-overview.json` - System health, request rates, error rates

### Import Dashboards

```bash
# Manual import
# 1. Open Grafana (http://localhost:3000)
# 2. Dashboards → Import
# 3. Upload JSON file from observability/dashboards/

# Or use API
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @observability/dashboards/platform-overview.json
```

---

## Alerting

Alert rules in `observability/alerts/`:

- `prometheus-rules.yaml` - Error rate, latency, availability alerts
- `alertmanager-config.yaml` - Alert routing configuration

### Apply Alert Rules

```bash
# Kubernetes
kubectl apply -f observability/alerts/prometheus-rules.yaml

# Local Prometheus
# Add to prometheus.yml:
rule_files:
  - "observability/alerts/prometheus-rules.yaml"
```

---

## Metrics

Services expose metrics at `/metrics` endpoint:

- **auth-service**: `http://localhost:8081/metrics`
- **phi-service**: `http://localhost:8082/metrics`
- **payment-gateway**: `http://localhost:8083/metrics`

### Key Metrics

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `http_requests_errors_total` - Error count
- `phi_encryption_operations_total` - Encryption operations
- `payment_transactions_total` - Payment transactions

---

## Tracing (Optional)

For distributed tracing with Jaeger:

```bash
# Start Jaeger
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest

# Access UI
open http://localhost:16686
```

---

## Notes

This is a **demo configuration**. For production:
- Configure proper alert receivers (PagerDuty, Slack, etc.)
- Set up long-term metrics storage
- Implement SLI/SLO monitoring
- Add custom business metrics
