# Disaster Recovery Plan
## Healthcare GitOps Intelligence Platform

**Document Version**: 1.0  
**Last Updated**: December 8, 2025  
**Owner**: SRE/DevOps Team  
**Review Frequency**: Quarterly

---

## Executive Summary

This document defines disaster recovery (DR) procedures for the Healthcare GitOps Intelligence Platform, including Recovery Time Objectives (RTO), Recovery Point Objectives (RPO), backup strategies, and incident response runbooks.

### Recovery Objectives
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour
- **Data Retention**: 90 days (compliance requirement)
- **Backup Frequency**: Hourly (critical data), Daily (full backups)

---

## 1. Architecture Overview

### Critical Components
1. **Go Microservices** (5 services)
   - auth-service
   - payment-gateway
   - phi-service
   - medical-device
   - synthetic-phi-service

2. **Data Stores**
   - PostgreSQL (primary database for audit logs, user data)
   - Redis (session cache, rate limiting)
   - Git repositories (source of truth for policies)

3. **Infrastructure**
   - Kubernetes cluster (service orchestration)
   - Load balancers (traffic distribution)
   - Object storage (binary artifacts, logs)

4. **External Dependencies**
   - OpenAI API (AI-powered commit generation)
   - GitHub (code repository, CI/CD)
   - Monitoring (Prometheus, Grafana, Jaeger)

### Failure Scenarios
| Scenario | Impact | Probability | RTO | RPO |
|----------|--------|-------------|-----|-----|
| Single service failure | Partial outage | High | 15 min | 0 |
| Database failure | Full outage | Medium | 2 hours | 1 hour |
| K8s cluster failure | Full outage | Low | 4 hours | 1 hour |
| Region-wide outage | Full outage | Very Low | 8 hours | 1 hour |
| Data corruption | Partial outage | Low | 4 hours | 1 hour |
| Security breach | Varies | Low | 1 hour | 0 |

---

## 2. Backup Strategy

### 2.1 Database Backups (PostgreSQL)

#### Automated Backups
```bash
#!/bin/bash
# Automated PostgreSQL backup script
# Schedule: Every hour via cron

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgresql"
RETENTION_DAYS=90

# Full backup
pg_dump -h $DB_HOST -U $DB_USER -Fc healthcare_gitops > \
  "$BACKUP_DIR/full_backup_$TIMESTAMP.dump"

# Incremental WAL archiving (continuous)
# Set in postgresql.conf:
# wal_level = replica
# archive_mode = on
# archive_command = 'cp %p /backups/wal_archive/%f'

# Cleanup old backups (keep 90 days)
find $BACKUP_DIR -name "*.dump" -mtime +$RETENTION_DAYS -delete

# Upload to cloud storage (S3/Azure Blob)
aws s3 sync $BACKUP_DIR s3://healthcare-gitops-backups/postgresql/ \
  --storage-class STANDARD_IA

# Verify backup integrity
pg_restore --list "$BACKUP_DIR/full_backup_$TIMESTAMP.dump" > /dev/null
if [ $? -eq 0 ]; then
  echo "✅ Backup verified: $TIMESTAMP"
else
  echo "❌ Backup verification failed: $TIMESTAMP"
  # Send alert to PagerDuty
fi
```

#### Backup Schedule
- **Hourly**: Incremental WAL backups (RPO: 1 hour)
- **Daily**: Full database dumps (04:00 UTC)
- **Weekly**: Full backup with integrity verification (Sunday 02:00 UTC)
- **Monthly**: Long-term retention snapshot (1st of month)

#### Storage Locations
- **Primary**: S3/Azure Blob Storage (encrypted, versioned)
- **Secondary**: Cross-region replication (DR region)
- **Tertiary**: Tape backup (monthly, offsite storage)

#### Recovery Procedure
```bash
#!/bin/bash
# Database recovery from backup

BACKUP_FILE="/backups/postgresql/full_backup_20251208_140000.dump"

# Stop application services
kubectl scale deployment --all --replicas=0 -n healthcare-gitops

# Drop and recreate database
psql -h $DB_HOST -U postgres -c "DROP DATABASE healthcare_gitops;"
psql -h $DB_HOST -U postgres -c "CREATE DATABASE healthcare_gitops;"

# Restore from backup
pg_restore -h $DB_HOST -U $DB_USER -d healthcare_gitops $BACKUP_FILE

# Apply WAL logs (if point-in-time recovery needed)
# pg_restore continues with WAL replay to target timestamp

# Verify data integrity
psql -h $DB_HOST -U $DB_USER -d healthcare_gitops -c "SELECT COUNT(*) FROM audit_logs;"

# Restart services
kubectl scale deployment --all --replicas=3 -n healthcare-gitops

# Verify service health
kubectl get pods -n healthcare-gitops
```

**Expected Recovery Time**: 1-2 hours (depending on database size)

---

### 2.2 Redis Backups (Session Cache)

#### Automated Backups
```bash
#!/bin/bash
# Redis backup script (RDB snapshots)
# Schedule: Every 6 hours

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/redis"

# Trigger BGSAVE (background save)
redis-cli -h $REDIS_HOST BGSAVE

# Wait for save to complete
while [ $(redis-cli -h $REDIS_HOST LASTSAVE) -eq $LASTSAVE ]; do
  sleep 5
done

# Copy RDB file
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/dump_$TIMESTAMP.rdb"

# Upload to cloud storage
aws s3 cp "$BACKUP_DIR/dump_$TIMESTAMP.rdb" \
  s3://healthcare-gitops-backups/redis/

echo "✅ Redis backup completed: $TIMESTAMP"
```

#### Recovery Procedure
```bash
#!/bin/bash
# Redis recovery

# Stop Redis
systemctl stop redis

# Restore RDB file
cp /backups/redis/dump_20251208_140000.rdb /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb

# Start Redis (automatically loads dump.rdb)
systemctl start redis

# Verify
redis-cli -h $REDIS_HOST PING
```

**Expected Recovery Time**: 5-10 minutes  
**Note**: Session data loss acceptable (users re-authenticate)

---

### 2.3 Configuration & Secrets Backup

#### Git Repository Backups
```bash
#!/bin/bash
# Backup Git repositories (policies, configurations)

BACKUP_DIR="/backups/git"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Clone all critical repos
repos=(
  "git@github.com:org/healthcare-gitops-policies.git"
  "git@github.com:org/healthcare-gitops-intelligence.git"
)

for repo in "${repos[@]}"; do
  repo_name=$(basename $repo .git)
  git clone --mirror $repo "$BACKUP_DIR/${repo_name}_$TIMESTAMP.git"
done

# Upload to S3
aws s3 sync $BACKUP_DIR s3://healthcare-gitops-backups/git/
```

#### Kubernetes Secrets Backup
```bash
#!/bin/bash
# Backup Kubernetes secrets (encrypted)

kubectl get secrets -n healthcare-gitops -o yaml | \
  kubeseal --format yaml > /backups/k8s/sealed-secrets.yaml

# Upload encrypted secrets
aws s3 cp /backups/k8s/sealed-secrets.yaml \
  s3://healthcare-gitops-backups/k8s/
```

---

## 3. Runbooks for Common Failure Scenarios

### 3.1 Single Service Failure

**Symptoms**:
- Service health check failures
- 5xx errors in logs
- Pod CrashLoopBackOff

**Diagnosis**:
```bash
# Check pod status
kubectl get pods -n healthcare-gitops

# Check logs
kubectl logs <pod-name> -n healthcare-gitops --tail=100

# Check events
kubectl describe pod <pod-name> -n healthcare-gitops
```

**Recovery Steps**:
1. **Restart pod** (quick recovery):
   ```bash
   kubectl delete pod <pod-name> -n healthcare-gitops
   # New pod auto-created by deployment
   ```

2. **Rollback deployment** (if recent change caused failure):
   ```bash
   kubectl rollout undo deployment/<service-name> -n healthcare-gitops
   kubectl rollout status deployment/<service-name> -n healthcare-gitops
   ```

3. **Scale up replicas** (if insufficient capacity):
   ```bash
   kubectl scale deployment/<service-name> --replicas=5 -n healthcare-gitops
   ```

**Expected Recovery**: 5-15 minutes

---

### 3.2 Database Connection Failure

**Symptoms**:
- "Connection refused" errors
- Timeout errors in service logs
- All services unhealthy

**Diagnosis**:
```bash
# Check database connectivity
psql -h $DB_HOST -U $DB_USER -d healthcare_gitops -c "SELECT 1;"

# Check connection pool
kubectl exec -it <pod-name> -n healthcare-gitops -- \
  pg_isready -h $DB_HOST

# Check network policies
kubectl get networkpolicies -n healthcare-gitops
```

**Recovery Steps**:
1. **Restart database** (if hung):
   ```bash
   # For managed DB (AWS RDS)
   aws rds reboot-db-instance --db-instance-identifier healthcare-gitops-db
   
   # For self-hosted
   systemctl restart postgresql
   ```

2. **Increase connection limits**:
   ```sql
   ALTER SYSTEM SET max_connections = 200;
   SELECT pg_reload_conf();
   ```

3. **Clear connection pools**:
   ```bash
   # Restart services to reset connection pools
   kubectl rollout restart deployment -n healthcare-gitops
   ```

**Expected Recovery**: 10-30 minutes

---

### 3.3 Complete Database Loss

**Symptoms**:
- Database unreachable
- Data corruption detected
- Hardware failure

**Recovery Steps**:
1. **Assess damage**:
   ```bash
   # Check database status
   psql -h $DB_HOST -U postgres -c "SELECT version();"
   
   # Check disk space
   df -h /var/lib/postgresql
   ```

2. **Restore from latest backup**:
   ```bash
   # Download latest backup
   aws s3 cp s3://healthcare-gitops-backups/postgresql/latest.dump \
     /tmp/restore.dump
   
   # Restore (see section 2.1)
   pg_restore -h $DB_HOST -U $DB_USER -d healthcare_gitops /tmp/restore.dump
   ```

3. **Apply WAL logs** (point-in-time recovery):
   ```bash
   # Replay WAL logs to specific timestamp
   recovery_target_time = '2025-12-08 14:30:00 UTC'
   ```

4. **Verify data integrity**:
   ```sql
   SELECT COUNT(*) FROM audit_logs;
   SELECT MAX(created_at) FROM commits;
   ```

5. **Restart services**:
   ```bash
   kubectl scale deployment --all --replicas=3 -n healthcare-gitops
   ```

**Expected Recovery**: 2-4 hours (depending on data size)  
**Data Loss**: Up to 1 hour (RPO)

---

### 3.4 Kubernetes Cluster Failure

**Symptoms**:
- API server unreachable
- All pods evicted
- Node failures

**Recovery Steps**:
1. **Switch to DR cluster** (if multi-cluster setup):
   ```bash
   # Update DNS to point to DR cluster
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z1234567890ABC \
     --change-batch file://dns-failover.json
   ```

2. **Restore cluster from backup**:
   ```bash
   # For managed K8s (EKS/AKS)
   # Restore cluster from latest snapshot
   
   # For self-managed
   # Rebuild cluster with infrastructure-as-code (Terraform)
   cd infrastructure/
   terraform apply -auto-approve
   ```

3. **Redeploy applications**:
   ```bash
   # Apply all Kubernetes manifests
   kubectl apply -f k8s/ -n healthcare-gitops
   
   # Wait for rollout
   kubectl rollout status deployment --all -n healthcare-gitops
   ```

4. **Restore secrets**:
   ```bash
   kubectl apply -f /backups/k8s/sealed-secrets.yaml
   ```

**Expected Recovery**: 4-8 hours (cluster rebuild)

---

### 3.5 Security Breach / Compromise

**Symptoms**:
- Unauthorized access detected
- Malicious activity in logs
- Security alerts from CloudTrail/Azure Monitor

**Immediate Actions** (within 1 hour):
1. **Isolate compromised systems**:
   ```bash
   # Block all traffic to affected services
   kubectl patch networkpolicy deny-all -n healthcare-gitops --type=merge \
     -p '{"spec":{"podSelector":{},"policyTypes":["Ingress","Egress"]}}'
   ```

2. **Rotate all secrets**:
   ```bash
   # Rotate database passwords
   psql -c "ALTER USER healthcare_gitops_user WITH PASSWORD 'new_password';"
   
   # Rotate API keys
   # (update in secrets manager, redeploy services)
   
   # Invalidate all sessions
   redis-cli FLUSHDB
   ```

3. **Enable forensics logging**:
   ```bash
   # Increase log verbosity
   kubectl set env deployment --all LOG_LEVEL=DEBUG -n healthcare-gitops
   
   # Enable audit logging
   kubectl create -f audit-policy.yaml
   ```

4. **Notify stakeholders**:
   - Security team (immediate)
   - Legal/compliance (within 1 hour)
   - Customers (within 24-72 hours, depending on breach severity)

**Investigation** (1-7 days):
- Collect logs, network captures
- Analyze attack vectors
- Determine data exposure
- Document timeline of events

**Recovery** (varies):
- Patch vulnerabilities
- Rebuild compromised systems
- Implement additional security controls
- Resume normal operations

**Post-Incident**:
- Conduct blameless post-mortem
- Update security procedures
- Implement preventive measures
- Report to regulatory bodies (if PHI exposed)

---

## 4. Disaster Recovery Testing

### 4.1 Testing Schedule
- **Monthly**: Single service failure simulation
- **Quarterly**: Database restore test
- **Semi-Annually**: Full DR failover drill
- **Annually**: Region-wide outage simulation

### 4.2 Test Procedures

#### Database Restore Test
```bash
#!/bin/bash
# Test database restore procedure (non-production)

# 1. Create test database
psql -c "CREATE DATABASE healthcare_gitops_test;"

# 2. Restore from latest backup
pg_restore -d healthcare_gitops_test /backups/postgresql/latest.dump

# 3. Verify record counts
TEST_COUNT=$(psql -d healthcare_gitops_test -t -c "SELECT COUNT(*) FROM audit_logs;")
PROD_COUNT=$(psql -d healthcare_gitops -t -c "SELECT COUNT(*) FROM audit_logs;")

if [ "$TEST_COUNT" -eq "$PROD_COUNT" ]; then
  echo "✅ Restore test PASSED"
else
  echo "❌ Restore test FAILED: $TEST_COUNT vs $PROD_COUNT"
fi

# 4. Cleanup
psql -c "DROP DATABASE healthcare_gitops_test;"
```

#### Failover Drill
1. Schedule maintenance window (communicate to users)
2. Trigger controlled failover to DR region
3. Monitor service availability during transition
4. Verify data consistency post-failover
5. Fail back to primary region
6. Document issues and improvements

### 4.3 Success Criteria
- RTO met: Services restored within 4 hours
- RPO met: Data loss < 1 hour
- Data integrity: 100% (no corruption)
- Service availability: 99.9% during recovery
- Team readiness: All steps executed correctly

---

## 5. Communication Plan

### 5.1 Incident Severity Levels

| Level | Description | Response Time | Notification |
|-------|-------------|---------------|--------------|
| **SEV-1** | Complete outage, security breach | 15 minutes | All stakeholders |
| **SEV-2** | Partial outage, degraded performance | 1 hour | Engineering, management |
| **SEV-3** | Minor issues, workaround available | 4 hours | Engineering team |
| **SEV-4** | Cosmetic issues, no impact | Next business day | Engineering team |

### 5.2 Notification Templates

#### SEV-1 Incident Alert
```
Subject: [SEV-1] Production Outage - Healthcare GitOps Platform

We are experiencing a complete service outage affecting all users.

Impact: All services unavailable
Start Time: 2025-12-08 14:30 UTC
Estimated Resolution: 2025-12-08 18:30 UTC (RTO: 4 hours)

Our team is actively working on recovery. Updates every 30 minutes.

Status Page: https://status.healthcare-gitops.com
```

#### Recovery Complete
```
Subject: [RESOLVED] Production Outage - Services Restored

The production outage has been resolved. All services are operational.

Resolution Time: 2025-12-08 16:45 UTC (2h 15m)
Root Cause: Database connection pool exhaustion
Data Loss: None (RPO met)

Post-mortem report will be published within 48 hours.
```

---

## 6. Contact Information

### On-Call Rotation
- **Primary**: SRE Team (PagerDuty: +1-555-0100)
- **Secondary**: Engineering Lead (PagerDuty: +1-555-0101)
- **Escalation**: CTO (Phone: +1-555-0102)

### Vendor Support
- **AWS Support**: Enterprise (24/7) - Case Portal
- **Database Support**: PostgreSQL Professional Services
- **Security**: Incident Response Team (security@healthcare-gitops.com)

---

## 7. Continuous Improvement

### Post-Incident Review
After every incident:
1. Conduct blameless post-mortem (within 48 hours)
2. Document root cause analysis
3. Identify preventive measures
4. Update runbooks with lessons learned
5. Track action items to completion

### Metrics Tracking
- **MTTR** (Mean Time To Recover): Target < 2 hours
- **MTBF** (Mean Time Between Failures): Target > 720 hours (30 days)
- **Backup Success Rate**: Target 99.9%
- **RTO Achievement**: Target 95% (meet 4-hour RTO)
- **RPO Achievement**: Target 99% (data loss < 1 hour)

---

## Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-08 | SRE Team | Initial version |

---

**Next Review Date**: 2026-03-08 (Quarterly)  
**Document Owner**: SRE/DevOps Lead  
**Approver**: CTO
