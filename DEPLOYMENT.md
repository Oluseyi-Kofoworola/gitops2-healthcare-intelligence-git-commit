# Production Deployment Guide

Quick reference for deploying the Healthcare GitOps Intelligence Platform to production environments.

---

## Prerequisites

- **Kubernetes 1.25+** or Docker Compose
- **Python 3.9+** and **Go 1.22+**
- **OPA 0.50+** (optional, for policy enforcement)
- **OpenTelemetry Collector** (optional, for observability)

---

## Local Development

```bash
# Clone repository
git clone https://github.com/YOUR_ORG/gitops2-healthcare-intelligence-git-commit.git
cd gitops2-healthcare-intelligence-git-commit

# Run setup
./setup.sh

# Start services with Docker Compose
cd tests/integration
docker-compose up -d

# Verify services
curl http://localhost:8081/health  # auth-service
curl http://localhost:8083/health  # payment-gateway
curl http://localhost:8082/health  # phi-service
```

---

## Kubernetes Deployment

### 1. Create Cluster

```bash
# Using Kind (local)
kind create cluster --name gitops2-healthcare
kubectl cluster-info

# Using Cloud (AWS EKS example)
eksctl create cluster \
  --name gitops2-healthcare \
  --region us-east-1 \
  --nodes 3 \
  --node-type t3.medium
```

### 2. Deploy Services

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/services/
kubectl apply -f k8s/deployments/

# Verify deployments
kubectl get pods -n healthcare-platform
kubectl get services -n healthcare-platform
```

### 3. Configure Ingress

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# Apply ingress rules
kubectl apply -f k8s/ingress.yaml

# Get external IP
kubectl get ingress -n healthcare-platform
```

---

## Cloud Platform Deployment

### AWS (EKS)

```bash
# 1. Configure AWS CLI
aws configure

# 2. Create EKS cluster
eksctl create cluster -f k8s/aws/cluster-config.yaml

# 3. Deploy services
kubectl apply -f k8s/

# 4. Setup Load Balancer
kubectl apply -f k8s/aws/alb-ingress.yaml
```

### Azure (AKS)

```bash
# 1. Login to Azure
az login

# 2. Create AKS cluster
az aks create \
  --resource-group healthcare-rg \
  --name gitops2-healthcare \
  --node-count 3 \
  --enable-addons monitoring

# 3. Get credentials
az aks get-credentials --resource-group healthcare-rg --name gitops2-healthcare

# 4. Deploy
kubectl apply -f k8s/
```

### GCP (GKE)

```bash
# 1. Authenticate
gcloud auth login

# 2. Create GKE cluster
gcloud container clusters create gitops2-healthcare \
  --zone us-central1-a \
  --num-nodes 3

# 3. Get credentials
gcloud container clusters get-credentials gitops2-healthcare --zone us-central1-a

# 4. Deploy
kubectl apply -f k8s/
```

---

## Environment Configuration

### Required Environment Variables

```bash
# AI Tools
export AI_MODEL_DEFAULT="gpt-4"
export OPENAI_API_KEY="your-key"

# Microservices
export JWT_SECRET="your-secret-key"
export ENCRYPTION_KEY="your-32-byte-key"
export DATABASE_URL="postgres://user:pass@host:5432/db"

# Observability
export OTEL_EXPORTER_OTLP_ENDPOINT="http://collector:4318"
export PROMETHEUS_ENDPOINT="http://prometheus:9090"

# Compliance
export HIPAA_AUDIT_RETENTION_DAYS="2555"  # 7 years
export FDA_VALIDATION_REQUIRED="true"
export SOX_AUDIT_ENABLED="true"
```

### Configuration Files

Place in `config/production.yaml`:

```yaml
compliance:
  hipaa:
    enabled: true
    audit_retention_days: 2555
  fda:
    enabled: true
    validation_mode: strict
  sox:
    enabled: true
    financial_controls: true

security:
  encryption:
    algorithm: AES-256-GCM
    key_rotation_days: 90
  authentication:
    jwt_expiry_hours: 24
    mfa_required: true

monitoring:
  metrics_enabled: true
  tracing_enabled: true
  log_level: info
```

---

## Production Checklist

### Pre-Deployment

- [ ] Review security configuration
- [ ] Update encryption keys
- [ ] Configure backup strategy
- [ ] Setup monitoring/alerting
- [ ] Test disaster recovery
- [ ] Review compliance settings

### Post-Deployment

- [ ] Verify all services healthy
- [ ] Test authentication flow
- [ ] Validate encryption working
- [ ] Check audit trail logging
- [ ] Monitor performance metrics
- [ ] Review security scan results

---

## Monitoring & Observability

### Metrics

```bash
# View Prometheus metrics
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
open http://localhost:9090

# View Grafana dashboards
kubectl port-forward svc/grafana 3000:3000 -n monitoring
open http://localhost:3000
```

### Logs

```bash
# View service logs
kubectl logs -f deployment/auth-service -n healthcare-platform
kubectl logs -f deployment/phi-service -n healthcare-platform

# Aggregate logs with Loki
kubectl port-forward svc/loki 3100:3100 -n monitoring
```

### Tracing

```bash
# View Jaeger traces
kubectl port-forward svc/jaeger-query 16686:16686 -n monitoring
open http://localhost:16686
```

---

## Scaling

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: phi-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: phi-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Apply: `kubectl apply -f k8s/hpa/`

---

## Backup & Recovery

### Database Backups

```bash
# Automated daily backups (CronJob)
kubectl apply -f k8s/cronjobs/backup-db.yaml

# Manual backup
kubectl exec -it postgres-0 -n healthcare-platform -- \
  pg_dump -U postgres healthcare_db > backup-$(date +%Y%m%d).sql
```

### Configuration Backups

```bash
# Backup all ConfigMaps and Secrets
kubectl get configmaps -n healthcare-platform -o yaml > backup-configs.yaml
kubectl get secrets -n healthcare-platform -o yaml > backup-secrets.yaml
```

---

## Security Hardening

### Network Policies

```bash
# Apply network policies
kubectl apply -f k8s/network-policies/

# Verify isolation
kubectl exec -it test-pod -- curl http://phi-service.healthcare-platform.svc.cluster.local
```

### Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: healthcare-platform
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

---

## Troubleshooting

### Service Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n healthcare-platform

# View logs
kubectl logs <pod-name> -n healthcare-platform --previous

# Check resource limits
kubectl top pods -n healthcare-platform
```

### Performance Issues

```bash
# Check resource usage
kubectl top nodes
kubectl top pods -n healthcare-platform

# Scale up replicas
kubectl scale deployment phi-service --replicas=5 -n healthcare-platform
```

### Network Issues

```bash
# Test service connectivity
kubectl exec -it debug-pod -- curl http://service-name.namespace.svc.cluster.local

# Check DNS
kubectl exec -it debug-pod -- nslookup phi-service.healthcare-platform.svc.cluster.local
```

---

## Compliance Audit

### Generate Audit Report

```bash
# Export audit logs (7-year retention)
kubectl logs -l app=phi-service --since=7d -n healthcare-platform > audit-logs.txt

# Generate compliance report
python tools/ai_compliance_framework.py audit-report \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --output compliance-report-2024.json
```

---

## Support

- **Issues**: https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit/issues
- **Documentation**: See [README.md](README.md)
- **Security**: security@your-org.com
