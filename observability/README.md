# Observability Configuration
## Grafana Dashboards, Prometheus Metrics, and Alerting

**Version**: 1.0  
**Last Updated**: December 8, 2025  
**Owner**: SRE Team

---

## Overview

This directory contains observability configurations including:
- Grafana dashboard definitions (JSON)
- Prometheus alerting rules (YAML)
- SLI/SLO definitions for each service
- PagerDuty/Opsgenie integration configs

---

## Quick Start

### 1. Deploy Monitoring Stack

```bash
# Deploy Prometheus + Grafana + Alertmanager
kubectl create namespace monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Get Grafana admin password
kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d

# Port-forward to access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Access: http://localhost:3000 (admin/password)
```

### 2. Import Dashboards

```bash
# Import all dashboards
for dashboard in observability/dashboards/*.json; do
  curl -X POST http://admin:password@localhost:3000/api/dashboards/db \
    -H "Content-Type: application/json" \
    -d @$dashboard
done
```

### 3. Configure Alerting

```bash
# Apply Prometheus alert rules
kubectl apply -f observability/alerts/prometheus-rules.yaml

# Configure Alertmanager
kubectl apply -f observability/alerts/alertmanager-config.yaml
```

---

## Directory Structure

```
observability/
├── dashboards/
│   ├── platform-overview.json       # High-level service health
│   ├── go-services-metrics.json     # Go service detailed metrics
│   ├── database-performance.json    # PostgreSQL metrics
│   ├── api-cost-tracking.json       # OpenAI API cost monitoring
│   └── compliance-audit.json        # Compliance event tracking
├── alerts/
│   ├── prometheus-rules.yaml        # Prometheus alerting rules
│   ├── alertmanager-config.yaml     # Alertmanager routing config
│   └── pagerduty-integration.yaml   # PagerDuty integration
├── sli-slo/
│   ├── service-level-objectives.yaml # SLO definitions
│   └── error-budget-policy.md       # Error budget policy
└── README.md                         # This file
```

---

## SLI/SLO Definitions

### Service Level Objectives (SLOs)

#### Platform-Wide SLOs
| Service | SLI | Target | Measurement Window |
|---------|-----|--------|-------------------|
| **Availability** | % of successful requests | 99.9% | 30 days |
| **Latency (P95)** | 95th percentile response time < 500ms | 95% | 30 days |
| **Latency (P99)** | 99th percentile response time < 2s | 99% | 30 days |
| **Error Rate** | % of requests with 5xx errors < 0.1% | 99.9% | 30 days |

#### Service-Specific SLOs

**auth-service**
- Availability: 99.95% (higher due to critical auth)
- P95 Latency: < 200ms
- P99 Latency: < 500ms
- Error Rate: < 0.05%

**payment-gateway**
- Availability: 99.9%
- P95 Latency: < 1s (payment processing)
- P99 Latency: < 3s
- Error Rate: < 0.1%

**phi-service**
- Availability: 99.9%
- P95 Latency: < 300ms
- P99 Latency: < 1s
- Error Rate: < 0.1%
- Data Loss: 0% (critical for PHI)

**medical-device**
- Availability: 99.95% (medical critical)
- P95 Latency: < 500ms
- P99 Latency: < 2s
- Error Rate: < 0.05%

**synthetic-phi-service**
- Availability: 99.5% (lower priority)
- P95 Latency: < 2s
- P99 Latency: < 5s
- Error Rate: < 1%

### Error Budget Policy

**Monthly Error Budget**: (1 - SLO) × Total Requests

Example: 99.9% SLO = 0.1% error budget
- 1M requests/month → 1,000 errors allowed
- If budget exhausted: Freeze feature releases, focus on reliability

**Error Budget Alerts**:
- 50% consumed: Warning (review incident trends)
- 75% consumed: Page on-call (investigate root causes)
- 90% consumed: Feature freeze (emergency reliability work)
- 100% consumed: Post-mortem required, leadership notification

---

## Prometheus Metrics

### Standard Metrics (Exported by All Services)

```promql
# Request rate (requests per second)
rate(http_requests_total[5m])

# Error rate (5xx errors)
rate(http_requests_total{status=~"5.."}[5m])

# Request duration (P95, P99)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Service availability
up{job="healthcare-gitops"}

# CPU usage
rate(process_cpu_seconds_total[5m])

# Memory usage
process_resident_memory_bytes

# Goroutines
go_goroutines

# Database connections
go_sql_connections_open
go_sql_connections_in_use
```

### Custom Business Metrics

```promql
# Commit generation success rate
rate(commit_generation_success_total[5m]) / rate(commit_generation_attempts_total[5m])

# Compliance validation pass rate
rate(compliance_validation_passed_total[5m]) / rate(compliance_validation_total[5m])

# OpenAI API cost (dollars per hour)
rate(openai_api_cost_dollars_total[1h])

# PHI encryption operations
rate(phi_encryption_operations_total[5m])

# Audit log writes
rate(audit_log_writes_total[5m])
```

---

## Alert Rules

### Critical Alerts (Page Immediately)

```yaml
# High Error Rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  severity: critical
  annotations:
    summary: "High error rate detected"
    description: "{{ $labels.service }} error rate: {{ $value }}"

# Service Down
- alert: ServiceDown
  expr: up{job="healthcare-gitops"} == 0
  for: 2m
  severity: critical
  annotations:
    summary: "Service is down"
    description: "{{ $labels.instance }} is unreachable"

# Database Connection Failure
- alert: DatabaseConnectionFailure
  expr: go_sql_connections_open == 0
  for: 1m
  severity: critical
  annotations:
    summary: "Database connection lost"
    description: "{{ $labels.service }} cannot connect to database"

# High P99 Latency
- alert: HighP99Latency
  expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 10m
  severity: critical
  annotations:
    summary: "High P99 latency"
    description: "{{ $labels.service }} P99 latency: {{ $value }}s"
```

### Warning Alerts (Review, No Page)

```yaml
# Error Budget 75% Consumed
- alert: ErrorBudget75Percent
  expr: (error_budget_consumed / error_budget_total) > 0.75
  for: 5m
  severity: warning
  annotations:
    summary: "Error budget 75% consumed"
    description: "{{ $labels.service }} approaching error budget limit"

# High Memory Usage
- alert: HighMemoryUsage
  expr: process_resident_memory_bytes / 1e9 > 2
  for: 15m
  severity: warning
  annotations:
    summary: "High memory usage"
    description: "{{ $labels.service }} using {{ $value }}GB memory"

# OpenAI API Cost Spike
- alert: OpenAICostSpike
  expr: rate(openai_api_cost_dollars_total[1h]) > 10
  for: 30m
  severity: warning
  annotations:
    summary: "OpenAI API cost spike"
    description: "Current rate: ${{ $value }}/hour"
```

---

## Grafana Dashboards

### 1. Platform Overview Dashboard

**Purpose**: High-level health monitoring for on-call engineers

**Panels**:
- Service availability (uptime %)
- Request rate (RPS) per service
- Error rate (% of 5xx)
- P95/P99 latency per service
- Active incidents count
- Error budget consumption

**Refresh**: 30 seconds

---

### 2. Go Services Metrics Dashboard

**Purpose**: Detailed Go service performance

**Panels**:
- HTTP request rate by endpoint
- HTTP error rate by status code
- Request duration histogram
- Go runtime metrics:
  - Goroutines count
  - Heap memory usage
  - GC pause duration
- Database connection pool stats
- External API call latencies

**Refresh**: 10 seconds

---

### 3. Database Performance Dashboard

**Purpose**: PostgreSQL monitoring

**Panels**:
- Active connections
- Connection pool utilization
- Query execution time (P95, P99)
- Transaction rate (commits/rollbacks)
- Deadlocks count
- Index hit ratio
- Table/index size growth
- Replication lag (if applicable)

**Refresh**: 1 minute

---

### 4. API Cost Tracking Dashboard

**Purpose**: OpenAI API cost monitoring

**Panels**:
- Hourly cost ($)
- Daily cost trend
- Monthly cost projection
- Cost by user
- Cost by team
- Cost by model (GPT-4, GPT-3.5, etc.)
- Token usage (input/output)
- Rate limit violations

**Refresh**: 5 minutes

---

### 5. Compliance Audit Dashboard

**Purpose**: Healthcare compliance monitoring

**Panels**:
- Audit log write rate
- Compliance validation success rate
- PHI access events (read/write)
- Encryption operations count
- Failed compliance checks
- Policy violations by type
- Commit metadata completeness

**Refresh**: 1 minute

---

## PagerDuty Integration

### Setup

```yaml
# alertmanager-config.yaml
global:
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

route:
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'pagerduty'
  
  routes:
    # Critical alerts -> page immediately
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    
    # Warning alerts -> Slack only
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'
  
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: '{{ .CommonAnnotations.summary }}'
        text: '{{ .CommonAnnotations.description }}'
```

### On-Call Schedule

```
Primary: SRE Team (rotating weekly)
  - Week 1: Engineer A
  - Week 2: Engineer B
  - Week 3: Engineer C
  
Secondary: Engineering Lead (always)

Escalation: CTO (after 15 minutes)
```

---

## Opsgenie Integration (Alternative)

```yaml
# opsgenie-config.yaml
receivers:
  - name: 'opsgenie'
    opsgenie_configs:
      - api_key: 'YOUR_OPSGENIE_API_KEY'
        priority: 'P1'
        responders:
          - type: 'team'
            id: 'SRE_TEAM_ID'
        tags: ['healthcare-gitops', '{{ .CommonLabels.service }}']
```

---

## Runbook Links

All alerts include runbook links for quick resolution:

```yaml
annotations:
  runbook_url: "https://wiki.company.com/runbooks/{{ $labels.alertname }}"
```

**Runbook Topics**:
- High error rate investigation
- Service restart procedure
- Database connection troubleshooting
- Cost spike mitigation
- Scaling services up/down
- Log analysis procedures

---

## Maintenance Windows

To silence alerts during maintenance:

```bash
# Create silence (2 hours)
amtool silence add \
  alertname=".*" \
  service="auth-service" \
  --duration=2h \
  --author="SRE Team" \
  --comment="Planned database migration"
```

---

## Metrics Retention

| Data Type | Retention | Aggregation |
|-----------|-----------|-------------|
| Raw metrics | 7 days | None |
| 5-minute aggregates | 30 days | Average |
| 1-hour aggregates | 1 year | Average |
| Daily aggregates | 5 years | Average |

---

## Dashboard Access

- **Grafana URL**: https://grafana.healthcare-gitops.com
- **Prometheus URL**: https://prometheus.healthcare-gitops.com
- **Alertmanager URL**: https://alertmanager.healthcare-gitops.com

**Access Control**:
- SRE Team: Full admin access
- Engineering Team: Read-only access
- Management: Executive dashboards only

---

## Next Steps

1. ✅ Deploy monitoring stack (Prometheus + Grafana)
2. ✅ Import dashboard definitions
3. ✅ Configure PagerDuty integration
4. ⬜ Set up Slack notifications
5. ⬜ Create runbooks for common alerts
6. ⬜ Schedule quarterly SLO review meetings
7. ⬜ Train team on observability tools

---

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [SLO Best Practices](https://sre.google/workbook/implementing-slos/)
- [The Four Golden Signals](https://sre.google/sre-book/monitoring-distributed-systems/)

---

**Document Owner**: SRE Lead  
**Last Review**: December 8, 2025  
**Next Review**: March 8, 2026
