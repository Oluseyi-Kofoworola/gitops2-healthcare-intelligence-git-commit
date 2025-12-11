# Deployment Guide

Quick reference for deploying the Healthcare GitOps Intelligence demo.

---

## Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.9+** and **Go 1.22+**
- **OPA 0.50+** (optional, for policy enforcement)
- **Git**

---

## Local Development

```bash
# Clone repository
git clone https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit.git
cd gitops2-healthcare-intelligence-git-commit

# Run setup
./setup.sh

# Start services with Docker Compose
cd tests/integration
docker-compose up -d

# Verify services
curl http://localhost:8081/health  # auth-service
curl http://localhost:8082/health  # phi-service
curl http://localhost:8083/health  # payment-gateway

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Kubernetes Deployment (Optional)

### Local Cluster (Kind)

```bash
# Create cluster
kind create cluster --name gitops2-healthcare
kubectl cluster-info

# Deploy services
kubectl apply -f k8s/

# Verify deployments
kubectl get pods
kubectl get services

# Port-forward to access services
kubectl port-forward svc/auth-service 8081:8080
kubectl port-forward svc/phi-service 8082:8080
kubectl port-forward svc/payment-gateway 8083:8080
```

### Cloud Deployment

For cloud platforms (AWS/Azure/GCP), you'll need to:

1. **Provision a Kubernetes cluster**
   - AWS: Use EKS
   - Azure: Use AKS
   - GCP: Use GKE

2. **Configure kubectl** to connect to your cluster

3. **Apply manifests**:
   ```bash
   kubectl apply -f k8s/
   ```

4. **Set up Ingress/Load Balancer** for external access

---

## Environment Variables

Key environment variables for services:

### Auth Service
```bash
PORT=8080                    # Server port
JWT_SECRET=your-secret-key   # JWT signing key
TOKEN_EXPIRY=15m            # Access token TTL
```

### PHI Service
```bash
PORT=8080
ENCRYPTION_KEY=your-32-byte-key  # AES-256 key
PBKDF2_ITERATIONS=100000        # Key derivation iterations
```

### Payment Gateway
```bash
PORT=8080
AUTH_SERVICE_URL=http://auth-service:8080
SOX_VALIDATION_ENABLED=true
```

---

## Running the Demo

```bash
# Full demo (all 3 flows)
./demo.sh

# Individual flows
./scripts/flow-1-ai-commit.sh      # AI commit generation
./scripts/flow-2-policy-gate-real.sh  # Policy validation
./scripts/flow-3-bisect-real.sh    # Intelligent bisect
```

See `START_HERE.md` for detailed walkthrough.

---

## Monitoring (Optional)

### Prometheus + Grafana

```bash
# Deploy monitoring stack
cd tests/integration
docker-compose --profile monitoring up -d

# Access Grafana
open http://localhost:3000  # admin/admin

# Access Prometheus
open http://localhost:9090
```

### View Metrics

Services expose metrics at `/metrics`:
- http://localhost:8081/metrics (auth-service)
- http://localhost:8082/metrics (phi-service)
- http://localhost:8083/metrics (payment-gateway)

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker ps

# Check logs
cd tests/integration
docker-compose logs

# Rebuild services
docker-compose up -d --build
```

### Port Conflicts

If ports 8081-8083 are in use:

```bash
# Edit docker-compose.yml to use different ports
# Or kill processes using those ports
lsof -ti:8081 | xargs kill -9
```

### OPA Policies Fail

```bash
# Test policies
opa test policies/healthcare/ -v

# Check policy syntax
opa check policies/healthcare/
```

---

## Production Considerations

This is a **demo repository**. For production deployment:

- [ ] Use proper secrets management (HashiCorp Vault, AWS Secrets Manager)
- [ ] Implement real database backends (not in-memory)
- [ ] Set up TLS/HTTPS with valid certificates
- [ ] Configure proper logging and monitoring
- [ ] Implement backup and disaster recovery
- [ ] Add rate limiting and DDoS protection
- [ ] Conduct security audit and penetration testing

---

## Cleanup

```bash
# Stop all services
cd tests/integration
docker-compose down

# Remove volumes
docker-compose down -v

# Delete Kubernetes cluster (if using Kind)
kind delete cluster --name gitops2-healthcare
```
