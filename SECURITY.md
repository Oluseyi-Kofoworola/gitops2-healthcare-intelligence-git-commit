# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

---

## Reporting a Vulnerability

**DO NOT** create a public GitHub issue for security vulnerabilities.

### Reporting Process

1. **Email**: Send details to **security@gitops-health.example.com**
2. **PGP Encryption** (Recommended): Use our PGP key below
3. **Expected Response**: Within 48 hours
4. **Resolution Timeline**: Critical issues resolved within 7 days

### PGP Public Key

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
[Production key would go here]
-----END PGP PUBLIC KEY BLOCK-----
```

### What to Include

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if available)
- Your contact information

### Security Issue Template

```markdown
**Vulnerability Type**: [SQL Injection / XSS / CSRF / etc.]

**Affected Component**: [Service name / file path]

**Severity**: [Critical / High / Medium / Low]

**Description**:
[Detailed explanation]

**Steps to Reproduce**:
1. ...
2. ...

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Potential Impact**:
[Data exposure / service disruption / etc.]

**Suggested Fix**:
[If applicable]

**Environment**:
- Version: 
- OS:
- Go version:
- Python version:
```

---

## Security Features

### Authentication & Authorization
- ✅ JWT-based authentication (HMAC-SHA256)
- ✅ Role-Based Access Control (RBAC)
- ✅ Scope-based permissions
- ✅ Token expiration (15 minutes default)
- ✅ Secure secret management (environment variables)

### Data Protection
- ✅ AES-256-GCM encryption for PHI
- ✅ TLS 1.3 for data in transit
- ✅ Input validation and sanitization
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS protection (Content-Security-Policy headers)

### Audit & Compliance
- ✅ Comprehensive audit logging (OpenTelemetry)
- ✅ HIPAA 164.312 technical safeguards
- ✅ SOX Section 404 IT controls
- ✅ FDA 21 CFR Part 11 compliance
- ✅ Immutable audit trail

### Infrastructure Security
- ✅ Container security (non-root user, read-only filesystem)
- ✅ Network policies (Kubernetes)
- ✅ Pod security standards
- ✅ Secrets management (Kubernetes secrets / Vault)
- ✅ Resource limits and quotas

---

## Security Best Practices

### For Developers

1. **Never commit secrets**
   ```bash
   # ✅ GOOD
   export JWT_SECRET=$(openssl rand -base64 64)
   
   # ❌ BAD
   JWT_SECRET="hardcoded-secret"
   ```

2. **Use parameterized queries**
   ```go
   // ✅ GOOD
   db.QueryRow("SELECT * FROM users WHERE id = $1", userID)
   
   // ❌ BAD
   db.QueryRow(fmt.Sprintf("SELECT * FROM users WHERE id = %s", userID))
   ```

3. **Validate all inputs**
   ```go
   // ✅ GOOD
   if !isValidEmail(email) {
       return errors.New("invalid email format")
   }
   
   // ❌ BAD
   user.Email = req.Email  // Direct assignment
   ```

4. **Use security headers**
   ```go
   w.Header().Set("X-Content-Type-Options", "nosniff")
   w.Header().Set("X-Frame-Options", "DENY")
   w.Header().Set("X-XSS-Protection", "1; mode=block")
   w.Header().Set("Content-Security-Policy", "default-src 'self'")
   ```

5. **Implement rate limiting**
   ```go
   limiter := rate.NewLimiter(rate.Limit(10), 100)
   if !limiter.Allow() {
       http.Error(w, "Rate limit exceeded", 429)
       return
   }
   ```

### For DevOps

1. **Rotate secrets regularly** (90 days maximum)
2. **Use least privilege** (minimum required permissions)
3. **Enable audit logging** (all services, all environments)
4. **Scan container images** (Trivy, Anchore)
5. **Monitor for anomalies** (Prometheus alerts)

### For Security Team

1. **Quarterly penetration testing**
2. **Monthly dependency audits** (`pip-audit`, `govulncheck`)
3. **Weekly vulnerability scans** (Trivy, Dependabot)
4. **Continuous compliance monitoring** (OPA policies)

---

## Vulnerability Disclosure Timeline

| Day | Action |
|-----|--------|
| 0 | Vulnerability reported |
| 1-2 | Initial triage and acknowledgment |
| 3-7 | Investigation and fix development |
| 7-14 | Testing and validation |
| 14-21 | Coordinated disclosure preparation |
| 21-30 | Public disclosure (after fix deployed) |

---

## Security Contacts

- **Primary**: security@gitops-health.example.com
- **Escalation**: ciso@gitops-health.example.com
- **Emergency (24/7)**: +1-555-SECURITY

---

## Acknowledgments

We appreciate responsible disclosure and will publicly acknowledge security researchers who:
- Report valid vulnerabilities
- Follow responsible disclosure guidelines
- Allow reasonable time for fixes

**Hall of Fame**: Coming soon!

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)

---

**Last Updated**: December 10, 2025  
**Version**: 2.0.0
