# Chaos Engineering Guide

## Overview

This guide provides comprehensive instructions for running chaos engineering experiments to validate system resilience and fault tolerance in the GitOps 2.0 Enterprise platform.

## Architecture

```
Chaos Engineering Stack
├── Chaos Mesh (Kubernetes-native)
├── Experiment Types
│   ├── Pod Failure
│   ├── Network Chaos
│   ├── Stress Testing
│   └── I/O Chaos
└── Monitoring & Recovery
    ├── Prometheus Metrics
    ├── OpenTelemetry Traces
    └── Automated Rollback
```

## Prerequisites

### 1. Kubernetes Cluster
```bash
# Minikube (recommended for local)
minikube start --cpus 4 --memory 8192 --kubernetes-version v1.28.0

# Or KIND
kind create cluster --config tests/chaos/kind-config.yaml
```

### 2. Chaos Mesh Installation
```bash
# Install Chaos Mesh via Helm
curl -sSL https://mirrors.chaos-mesh.org/v2.6.3/install.sh | bash

# Verify installation
kubectl get pods -n chaos-mesh

# Install Chaos Mesh Dashboard (optional)
kubectl port-forward -n chaos-mesh svc/chaos-dashboard 2333:2333
# Access at http://localhost:2333
```

### 3. Deploy Services
```bash
# Deploy all microservices
kubectl apply -f services/auth-service/k8s-deployment.yaml
kubectl apply -f services/payment-gateway/k8s-deployment.yaml
kubectl apply -f services/phi-service/k8s-deployment.yaml

# Verify deployments
kubectl get pods -n default
```

## Chaos Experiments

### Experiment 1: Pod Failure Injection

**Scenario**: Simulate random pod crashes to test pod restart and self-healing.

```yaml
# experiments/pod-failure.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: auth-service-pod-kill
  namespace: default
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      'app': 'auth-service'
  duration: '30s'
  scheduler:
    cron: '@every 2m'
```

**Expected Behavior**:
- Pod terminates gracefully
- Kubernetes restarts pod within 5 seconds
- Service mesh routes traffic to healthy pods
- No 500 errors (max 503 during restart)

**Validation**:
```bash
# Monitor pod restarts
kubectl get pods -l app=auth-service -w

# Check service availability
while true; do
  curl -s http://auth-service:8080/health || echo "FAIL"
  sleep 1
done
```

---

### Experiment 2: Network Partition

**Scenario**: Simulate network splits between services to test graceful degradation.

```yaml
# experiments/network-partition.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: payment-to-auth-partition
  namespace: default
spec:
  action: partition
  mode: all
  selector:
    namespaces:
      - default
    labelSelectors:
      'app': 'payment-gateway'
  direction: to
  target:
    selector:
      namespaces:
        - default
      labelSelectors:
        'app': 'auth-service'
    mode: all
  duration: '60s'
```

**Expected Behavior**:
- Payment Gateway cannot reach Auth Service
- Circuit breaker activates after 3 failed requests
- Payment requests return 503 Service Unavailable
- Graceful error messages returned to clients

**Validation**:
```bash
# Test payment with auth dependency
curl -X POST http://payment-gateway:8081/process \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "currency": "USD"}'

# Expected: {"error": "auth service unavailable", "retry_after": 60}
```

---

### Experiment 3: Network Delay

**Scenario**: Inject latency to test timeout handling and user experience.

```yaml
# experiments/network-delay.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: phi-service-delay
  namespace: default
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - default
    labelSelectors:
      'app': 'phi-service'
  delay:
    latency: '2s'
    correlation: '100'
    jitter: '500ms'
  duration: '5m'
```

**Expected Behavior**:
- PHI encryption requests delayed by 2s ± 500ms
- Client timeouts respected (default 5s)
- Request queuing handled gracefully
- No resource exhaustion

**Validation**:
```bash
# Measure response times
for i in {1..10}; do
  time curl -X POST http://phi-service:8083/encrypt \
    -H "Content-Type: application/json" \
    -d '{"plaintext": "test data"}'
done
```

---

### Experiment 4: Network Packet Loss

**Scenario**: Simulate lossy network conditions.

```yaml
# experiments/packet-loss.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: auth-packet-loss
  namespace: default
spec:
  action: loss
  mode: all
  selector:
    namespaces:
      - default
    labelSelectors:
      'app': 'auth-service'
  loss:
    loss: '25'
    correlation: '50'
  duration: '3m'
```

**Expected Behavior**:
- 25% of packets dropped
- HTTP retries handle transient failures
- Eventually consistent behavior
- No data corruption

---

### Experiment 5: CPU Stress

**Scenario**: Test behavior under CPU pressure.

```yaml
# experiments/cpu-stress.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: payment-cpu-stress
  namespace: default
spec:
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      'app': 'payment-gateway'
  stressors:
    cpu:
      workers: 2
      load: 80
  duration: '5m'
```

**Expected Behavior**:
- CPU usage reaches 80%
- Response times degrade gracefully
- Horizontal Pod Autoscaler (HPA) scales out
- No OOMKills

**Validation**:
```bash
# Monitor CPU and scaling
kubectl top pods -l app=payment-gateway
kubectl get hpa payment-gateway -w
```

---

### Experiment 6: Memory Pressure

**Scenario**: Test memory limits and OOM handling.

```yaml
# experiments/memory-stress.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: phi-memory-stress
  namespace: default
spec:
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      'app': 'phi-service'
  stressors:
    memory:
      workers: 1
      size: '256MB'
  duration: '3m'
```

**Expected Behavior**:
- Memory usage increases
- Kubernetes limits enforced
- Pod evicted if exceeding limits
- New pod starts automatically

---

### Experiment 7: I/O Delay

**Scenario**: Simulate slow disk I/O.

```yaml
# experiments/io-delay.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: IOChaos
metadata:
  name: phi-io-delay
  namespace: default
spec:
  action: latency
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      'app': 'phi-service'
  volumePath: /data
  path: '/data/**/*'
  delay: '100ms'
  percent: 50
  duration: '5m'
```

**Expected Behavior**:
- 50% of I/O operations delayed by 100ms
- Database queries slower
- Application remains responsive
- No timeouts or crashes

---

### Experiment 8: DNS Failure

**Scenario**: Simulate DNS resolution failures.

```yaml
# experiments/dns-failure.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: DNSChaos
metadata:
  name: auth-dns-failure
  namespace: default
spec:
  action: error
  mode: all
  selector:
    namespaces:
      - default
    labelSelectors:
      'app': 'payment-gateway'
  patterns:
    - auth-service
    - auth-service.default.svc.cluster.local
  duration: '2m'
```

**Expected Behavior**:
- DNS lookups fail for auth-service
- Cached DNS entries used initially
- Graceful fallback to IP addresses
- Circuit breaker prevents cascading failures

---

## Running Experiments

### Manual Execution

```bash
# 1. Apply chaos experiment
kubectl apply -f tests/chaos/experiments/pod-failure.yaml

# 2. Monitor experiment
kubectl get podchaos
kubectl describe podchaos auth-service-pod-kill

# 3. Observe system behavior
kubectl logs -f -l app=auth-service
curl http://auth-service:8080/health

# 4. Cleanup
kubectl delete podchaos auth-service-pod-kill
```

### Automated Test Suite

```bash
# Run all chaos experiments
cd tests/chaos
./run-chaos-tests.sh

# Run specific experiment
./run-chaos-tests.sh pod-failure

# Run with custom duration
./run-chaos-tests.sh --duration 10m --experiment network-partition
```

---

## Monitoring & Metrics

### Key Metrics to Track

1. **Availability Metrics**
   - Service uptime (target: 99.9%)
   - Request success rate (target: 99.5%)
   - Pod restart count

2. **Performance Metrics**
   - P50/P95/P99 response times
   - Request throughput (RPS)
   - Error rate

3. **Resilience Metrics**
   - Circuit breaker activations
   - Retry attempts
   - Failover time (target: <5s)

### Grafana Dashboards

```bash
# Import pre-built dashboards
kubectl apply -f tests/chaos/grafana-dashboards/

# Access Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000
# http://localhost:3000 (admin/admin)
```

---

## Recovery Validation

### Automated Recovery Tests

```go
// tests/chaos/recovery_test.go
func TestPodFailureRecovery(t *testing.T) {
    // 1. Inject pod failure
    applyChaosPodKill(t, "auth-service")
    
    // 2. Wait for pod restart
    waitForPodReady(t, "auth-service", 30*time.Second)
    
    // 3. Validate service health
    resp := callHealthEndpoint(t, "http://auth-service:8080/health")
    assert.Equal(t, 200, resp.StatusCode)
    
    // 4. Validate functional correctness
    token := loginUser(t, "testuser", "password")
    assert.NotEmpty(t, token)
}
```

---

## Best Practices

### 1. Start Small
- Begin with single pod failures
- Gradually increase blast radius
- Test in non-production first

### 2. Define Success Criteria
- Maximum downtime allowed
- Acceptable error rates
- Recovery time objectives (RTO)

### 3. Monitor Continuously
- Use Prometheus + Grafana
- Set up alerts for anomalies
- Log all chaos events

### 4. Document Learnings
- Record all experiment results
- Track system improvements
- Update runbooks

### 5. Automate Game Days
- Schedule regular chaos tests
- Include in CI/CD pipeline
- Simulate peak load scenarios

---

## Troubleshooting

### Chaos Mesh Not Working

```bash
# Check Chaos Mesh components
kubectl get pods -n chaos-mesh
kubectl logs -n chaos-mesh -l app.kubernetes.io/component=controller-manager

# Verify CRDs installed
kubectl get crds | grep chaos-mesh

# Reinstall if needed
helm uninstall chaos-mesh -n chaos-mesh
curl -sSL https://mirrors.chaos-mesh.org/v2.6.3/install.sh | bash
```

### Experiment Not Applying

```bash
# Validate YAML syntax
kubectl apply --dry-run=client -f experiments/pod-failure.yaml

# Check permissions
kubectl auth can-i create podchaos

# View experiment status
kubectl describe podchaos <name>
```

---

## Compliance & Safety

### HIPAA Considerations
- Never inject chaos in production PHI environments
- Use synthetic data only
- Maintain audit logs of all experiments

### Safety Guards
```yaml
# Add safety annotations
metadata:
  annotations:
    chaos-mesh.org/environment: "staging"
    chaos-mesh.org/approved-by: "platform-team"
```

---

## References

- [Chaos Mesh Documentation](https://chaos-mesh.org/docs/)
- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [Netflix Chaos Monkey](https://netflix.github.io/chaosmonkey/)
- [SRE Book - Practicing Chaos](https://sre.google/books/)

---

## Next Steps

1. ✅ Run basic pod failure tests
2. ✅ Validate network partition handling
3. ✅ Test resource exhaustion scenarios
4. 🚧 Integrate with CI/CD pipelines
5. 🚧 Schedule automated game days
6. 📋 Expand to multi-region chaos

---

**Status**: Ready for Chaos Testing 🎯
**Estimated Time**: 2-3 hours to complete all experiments
**Prerequisites**: Kubernetes cluster + Chaos Mesh installed
