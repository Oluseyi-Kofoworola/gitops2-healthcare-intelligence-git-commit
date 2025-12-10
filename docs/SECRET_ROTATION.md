# Secret Rotation Procedures

**Author**: Platform Security Team  
**Version**: 1.0.0  
**Last Updated**: December 10, 2025

---

## Overview

This document provides step-by-step procedures for rotating secrets in the GitOps Healthcare Intelligence Platform. Regular secret rotation is a critical security control required by:

- **HIPAA** 45 CFR § 164.308(a)(4)(ii)(B) - Access control mechanisms
- **SOX** Section 404 - IT general controls
- **PCI-DSS** Requirement 8.2.4 - Change passwords every 90 days
- **NIST 800-53** IA-5 - Authenticator management

---

## Rotation Schedule

| Secret Type | Rotation Frequency | Criticality |
|-------------|-------------------|-------------|
| JWT Signing Secret | 90 days | Critical |
| PHI Encryption Key | 180 days | Critical |
| API Keys (OpenAI) | 90 days | High |
| TLS Certificates | 365 days (or 90 days) | Critical |
| Database Passwords | 90 days | High |
| Service Account Tokens | 90 days | Medium |

**Emergency Rotation**: Immediately upon suspected compromise

---

## 1. JWT Signing Secret Rotation

### Overview
The JWT signing secret is used by `auth-service` to sign and verify authentication tokens.

### Prerequisites
- Access to production Kubernetes cluster
- Kubectl configured with admin permissions
- Rollback plan in case of failure

### Procedure

#### Step 1: Generate New Secret
```bash
# Generate a cryptographically secure secret (64 bytes = 512 bits)
NEW_JWT_SECRET=$(openssl rand -base64 64)

# Verify length (should be 88 characters due to base64 encoding)
echo ${#NEW_JWT_SECRET}  # Should output: 88
```

#### Step 2: Create Kubernetes Secret
```bash
# Create new secret version
kubectl create secret generic auth-service-secret-v2 \
  --from-literal=jwt-secret="${NEW_JWT_SECRET}" \
  --namespace=production

# Verify creation
kubectl get secret auth-service-secret-v2 -n production
```

#### Step 3: Deploy with Blue-Green Strategy
```bash
# Deploy new version with new secret
kubectl set env deployment/auth-service \
  JWT_SECRET_VERSION=v2 \
  --namespace=production

# Wait for rollout
kubectl rollout status deployment/auth-service -n production

# Verify health
kubectl exec -it deployment/auth-service -n production -- \
  curl -s localhost:8080/health | jq .
```

#### Step 4: Monitor and Validate
```bash
# Check logs for errors
kubectl logs -f deployment/auth-service -n production --tail=100

# Test token generation
curl -X POST https://auth.example.com/token \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "scopes": ["phi:read"],
    "role": "operator"
  }' | jq .

# Verify token validation works
TOKEN=$(curl -s -X POST https://auth.example.com/token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","scopes":["phi:read"],"role":"operator"}' | jq -r '.token')

curl -s https://auth.example.com/introspect \
  -H "Authorization: Bearer $TOKEN" | jq .
```

#### Step 5: Cleanup Old Secret (After 24 Hours)
```bash
# Delete old secret
kubectl delete secret auth-service-secret-v1 -n production

# Verify deletion
kubectl get secrets -n production | grep auth-service
```

### Rollback Procedure
```bash
# If issues occur, rollback immediately
kubectl set env deployment/auth-service \
  JWT_SECRET_VERSION=v1 \
  --namespace=production

kubectl rollout undo deployment/auth-service -n production
```

---

## 2. PHI Encryption Key Rotation

### Overview
The PHI encryption key is used by `phi-service` for AES-256-GCM encryption of protected health information.

### Prerequisites
- Database access for re-encryption (if using persistent storage)
- Estimated downtime: 2-4 hours for re-encryption
- Backup of all PHI data

### Procedure

#### Step 1: Generate New Encryption Key
```bash
# Generate 32-byte (256-bit) key
NEW_ENCRYPTION_KEY=$(openssl rand -base64 32)

# Verify length
echo ${#NEW_ENCRYPTION_KEY}  # Should be 44 (32 bytes base64-encoded)
```

#### Step 2: Deploy Key to Vault/Secrets Manager
```bash
# Using Kubernetes secrets
kubectl create secret generic phi-encryption-key-v2 \
  --from-literal=key="${NEW_ENCRYPTION_KEY}" \
  --namespace=production

# Using HashiCorp Vault
vault kv put secret/phi-service/encryption-key-v2 \
  key="${NEW_ENCRYPTION_KEY}" \
  created_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

#### Step 3: Enable Dual-Key Mode (Transitional)
```bash
# Update deployment to support both old and new keys
kubectl set env deployment/phi-service \
  ENCRYPTION_KEY_CURRENT=v2 \
  ENCRYPTION_KEY_LEGACY=v1 \
  --namespace=production

# This allows:
# - New data encrypted with v2
# - Old data decrypted with v1
```

#### Step 4: Re-encrypt Existing Data
```bash
# Run batch re-encryption job (custom script)
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: phi-reencryption-$(date +%Y%m%d-%H%M%S)
  namespace: production
spec:
  template:
    spec:
      containers:
      - name: reencrypt
        image: phi-service:latest
        command: ["/app/scripts/reencrypt-data.sh"]
        env:
        - name: OLD_KEY_VERSION
          value: "v1"
        - name: NEW_KEY_VERSION
          value: "v2"
        - name: BATCH_SIZE
          value: "1000"
      restartPolicy: Never
  backoffLimit: 3
EOF

# Monitor progress
kubectl logs -f job/phi-reencryption-<timestamp> -n production
```

#### Step 5: Verify Re-encryption
```bash
# Query database for records still using old key
kubectl exec -it deployment/phi-service -n production -- \
  /app/scripts/verify-encryption-status.sh

# Expected output:
# Total records: 50000
# Encrypted with v2: 50000 (100%)
# Encrypted with v1: 0 (0%)
```

#### Step 6: Remove Legacy Key Support
```bash
# After 100% migration confirmed
kubectl set env deployment/phi-service \
  ENCRYPTION_KEY_CURRENT=v2 \
  ENCRYPTION_KEY_LEGACY- \
  --namespace=production

# Delete old key
kubectl delete secret phi-encryption-key-v1 -n production
```

### Testing Checklist
- [ ] Encrypt sample PHI with new key
- [ ] Decrypt sample PHI with new key
- [ ] Verify old PHI still decryptable (during transition)
- [ ] Performance benchmarks (encryption/decryption speed)
- [ ] Load test (1000 req/s for 5 minutes)

---

## 3. API Key Rotation (OpenAI)

### Overview
Rotate OpenAI API keys used by AI tools (commit generator, compliance analyzer).

### Procedure

#### Step 1: Generate New API Key
```bash
# Log in to OpenAI dashboard
open https://platform.openai.com/api-keys

# Create new key with descriptive name
# Example: "GitOps-Health-Prod-2025-12"
```

#### Step 2: Update Secret
```bash
# Update Kubernetes secret
kubectl create secret generic openai-api-key \
  --from-literal=api-key="sk-proj-..." \
  --namespace=production \
  --dry-run=client -o yaml | kubectl apply -f -

# Or update environment variable (CI/CD)
# GitHub Actions: Settings > Secrets > OPENAI_API_KEY
```

#### Step 3: Validate New Key
```bash
# Test API call
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-..." | jq '.data[0].id'

# Expected output: "gpt-4" or similar model name
```

#### Step 4: Monitor Usage
```bash
# Check OpenAI dashboard for requests
# Ensure old key shows no activity after 1 hour

# Run cost tracker
python tools/ai_cost_tracker.py --check-budget
```

#### Step 5: Revoke Old Key
```bash
# After 24 hours of successful operation
# OpenAI dashboard > API keys > Revoke old key
```

---

## 4. TLS Certificate Rotation

### Overview
Rotate TLS certificates for HTTPS endpoints.

### Prerequisites
- Certificate authority access (Let's Encrypt, internal CA)
- DNS validation or HTTP-01 challenge access
- Load balancer/Ingress controller access

### Procedure (Let's Encrypt with Cert-Manager)

#### Step 1: Verify Cert-Manager Installation
```bash
kubectl get pods -n cert-manager
kubectl get certificates -n production
```

#### Step 2: Request New Certificate
```bash
# Cert-manager auto-renews 30 days before expiry
# Force renewal if needed:
kubectl annotate certificate auth-service-tls \
  cert-manager.io/issue-temporary-certificate="true" \
  -n production

# Monitor issuance
kubectl describe certificate auth-service-tls -n production
```

#### Step 3: Verify New Certificate
```bash
# Check expiry date
kubectl get secret auth-service-tls -n production -o json | \
  jq -r '.data["tls.crt"]' | base64 -d | \
  openssl x509 -noout -dates

# Test HTTPS connection
curl -v https://auth.example.com/health 2>&1 | grep "SSL certificate"
```

#### Step 4: Update Ingress (If Manual)
```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: auth-service-ingress
  namespace: production
spec:
  tls:
  - hosts:
    - auth.example.com
    secretName: auth-service-tls-v2
  rules:
  - host: auth.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: auth-service
            port:
              number: 8080
EOF
```

---

## 5. Emergency Rotation Procedure

### When to Trigger
- ⚠️ Secret exposed in public repository
- ⚠️ Unauthorized access detected
- ⚠️ Employee with secret access leaves company
- ⚠️ Compliance audit finding

### Immediate Actions (Within 1 Hour)
```bash
# 1. Revoke compromised secret immediately
kubectl delete secret <compromised-secret> -n production

# 2. Generate and deploy new secret (see procedures above)

# 3. Force pod restart to pick up new secret
kubectl rollout restart deployment/<service-name> -n production

# 4. Monitor for unauthorized access attempts
kubectl logs -f deployment/<service-name> -n production | grep "401\|403"

# 5. Notify incident response team
# Send email to: security@gitops-health.example.com
```

### Post-Incident Review (Within 24 Hours)
- Root cause analysis
- Update secret rotation procedures
- Implement preventive controls
- Document lessons learned

---

## 6. Automation Recommendations

### GitOps Approach
```yaml
# .github/workflows/secret-rotation-reminder.yml
name: Secret Rotation Reminder
on:
  schedule:
    - cron: '0 0 1 */3 *'  # Every 3 months
jobs:
  remind:
    runs-on: ubuntu-latest
    steps:
      - name: Create rotation issue
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Quarterly Secret Rotation Required',
              body: 'Rotate: JWT secret, API keys, TLS certs',
              labels: ['security', 'high-priority']
            })
```

### HashiCorp Vault Auto-Rotation
```hcl
# vault/policies/auto-rotate-secrets.hcl
path "secret/data/auth-service/*" {
  capabilities = ["create", "update"]
  
  allowed_parameters = {
    "rotation_period" = ["7776000"]  # 90 days
  }
}
```

---

## 7. Audit Trail

### Log All Rotation Events
```bash
# Example audit log entry
{
  "timestamp": "2025-12-10T15:30:00Z",
  "event": "secret_rotation",
  "secret_type": "jwt_signing_key",
  "old_version": "v1",
  "new_version": "v2",
  "rotated_by": "john.doe@example.com",
  "reason": "scheduled_90_day_rotation",
  "status": "success"
}
```

### Compliance Evidence
Keep records of:
- Rotation dates and times
- Personnel who performed rotation
- Validation test results
- Incident reports (if emergency rotation)

---

## 8. Testing & Validation

### Pre-Rotation Checklist
- [ ] Backup current secrets
- [ ] Test secret generation process
- [ ] Review rollback procedure
- [ ] Schedule maintenance window
- [ ] Notify stakeholders

### Post-Rotation Checklist
- [ ] All services healthy (no 5xx errors)
- [ ] Authentication working (sample logins)
- [ ] Encryption/decryption functional
- [ ] Monitoring alerts normal
- [ ] Audit logs captured
- [ ] Document rotation completion

---

## References

- [NIST SP 800-57: Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
- [OWASP Secret Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Kubernetes Secrets Best Practices](https://kubernetes.io/docs/concepts/configuration/secret/)

---

**Contact**: security@gitops-health.example.com  
**Emergency**: +1-555-SECURITY (24/7)
