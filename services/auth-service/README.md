# Authentication & Authorization Service

Production-grade JWT-based authentication for healthcare platform.

---

## Architecture

```mermaid
flowchart LR
    A[Client] --> B[POST /token]
    A --> C[POST /validate]
    A --> D[POST /refresh]
    
    B --> E[JWT Generator]
    C --> F[JWT Validator]
    D --> G[Token Refresher]
    
    E --> H[RBAC Engine]
    F --> H
    G --> H
    
    H --> I[OpenTelemetry]
    H --> J[Prometheus]
    
    E --> K[Access Token<br/>15min TTL]
    G --> L[Refresh Token<br/>7d TTL]
    
    style E fill:#d4edda
    style F fill:#d4edda
    style G fill:#d4edda
    style H fill:#fff3cd
    style I fill:#e1f5ff
    style J fill:#e1f5ff
```

---

## Overview

Centralized authentication and authorization for GitOps 2.0 Healthcare Platform with compliance support.

### Key Features

- ✅ **JWT Authentication** - JSON Web Tokens with RS256
- ✅ **Scope-Based Authorization** - Fine-grained access control
- ✅ **RBAC Support** - Role-based access (admin, clinician, auditor)
- ✅ **OpenTelemetry Tracing** - Security event tracing
- ✅ **Prometheus Metrics** - Real-time monitoring
- ✅ **Structured Logging** - JSON logs with correlation IDs
- ✅ **Security Headers** - OWASP best practices
- ✅ **Health Checks** - Kubernetes liveness/readiness probes

## Quick Start

### Run Locally

```bash
# Build the service
go build -o auth-service

# Run
./auth-service

# Service starts on port 8090
```

### Using Docker

```bash
# Build image
docker build -t auth-service:latest .

# Run container
docker run -p 8090:8090 auth-service:latest
```

## API Endpoints

### Token Management

#### Generate Token
```bash
POST /token
Content-Type: application/json

{
  "user_id": "user123",
  "scopes": ["payment:write", "phi:read"],
  "role": "admin"
}
```

**Response**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": 1732370400,
  "token_type": "Bearer"
}
```

#### Validate Token (Introspect)
```bash
GET /introspect
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (Valid)**:
```json
{
  "active": true,
  "user_id": "user123",
  "scopes": ["payment:write", "phi:read"],
  "role": "admin",
  "exp": 1732370400,
  "iat": 1732369500
}
```

**Response (Invalid)**:
```json
{
  "active": false
}
```

### Health & Monitoring

#### Health Check
```bash
GET /health

# Response
{
  "status": "healthy",
  "service": "auth-service",
  "version": "1.0.0",
  "timestamp": "2025-11-23T10:30:00Z",
  "security": ["JWT", "OAuth2", "RBAC"]
}
```

#### Readiness Check
```bash
GET /readiness

# Response
{
  "ready": true,
  "service": "auth-service",
  "checks": {
    "jwt_validator": "ready",
    "metrics": "ready",
    "tracing": "ready"
  }
}
```

#### Prometheus Metrics
```bash
GET /metrics

# Prometheus format output
# auth_tokens_validated_total{result="valid",scope="payment:write"} 1234
# auth_request_duration_seconds{endpoint="/introspect",method="GET",status="200"} 0.045
```

## Supported Scopes

The service supports fine-grained permissions:

| Scope | Description |
|-------|-------------|
| `payment:read` | Read payment data |
| `payment:write` | Process payments |
| `phi:read` | Read PHI data |
| `phi:write` | Write PHI data |
| `admin` | Full administrative access |

## Roles

Pre-defined roles with scope bundles:

- **admin** - All scopes
- **payment_processor** - payment:read, payment:write
- **phi_analyst** - phi:read
- **phi_manager** - phi:read, phi:write
- **user** - Limited read access

## Security Features

### JWT Validation

- **Algorithm**: HMAC-SHA256 (HS256)
- **Expiration**: 15 minutes default
- **Claims**: user_id, scopes, role, exp, iat, iss
- **Secret Management**: Environment variable (production: use vault)

### Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'`
- `Strict-Transport-Security: max-age=31536000`

### Rate Limiting

(To be implemented in Kubernetes NetworkPolicy)

## Observability

### OpenTelemetry Tracing

All requests are traced with:
- Request method, path, user agent
- Token validation results
- User ID and scopes (when valid)
- Processing duration
- Error details

**Example trace attributes**:
```
http.method: GET
http.path: /introspect
http.status_code: 200
user.id: user123
user.role: admin
user.scopes: [payment:write, phi:read]
```

### Prometheus Metrics

**Authentication Metrics**:
- `auth_tokens_validated_total` - Token validations by result and scope
- `auth_request_duration_seconds` - Request duration histogram
- `auth_active_requests` - Current active requests
- `auth_security_events_total` - Security events by type and severity

**Event Types**:
- `successful_authentication` - Valid token
- `token_validation_failed` - Invalid token
- `token_expired` - Expired token
- `missing_token` - No token provided
- `invalid_token_format` - Malformed token
- `token_generated` - New token created

### Structured Logging

All logs in JSON format:
```json
{
  "timestamp": "2025-11-23T10:30:00Z",
  "level": "info",
  "service": "auth-service",
  "trace_id": "abc123...",
  "user_id": "user123",
  "role": "admin",
  "scopes": ["payment:write", "phi:read"],
  "message": "Token validated successfully"
}
```

## Example Usage

### Complete Flow

```bash
# 1. Generate a token
TOKEN_RESPONSE=$(curl -X POST http://localhost:8090/token \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "scopes": ["payment:write", "phi:read"],
    "role": "payment_processor"
  }')

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.token')

# 2. Use the token to access protected resources
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8090/introspect

# 3. Call other services with the token
curl -H "Authorization: Bearer $TOKEN" \
  http://payment-gateway:8082/process

# 4. Token expires after 15 minutes, generate a new one
```

### Integration with Other Services

```go
// In payment-gateway or other services
func ValidateToken(token string) (*UserClaims, error) {
    resp, err := http.Get("http://auth-service:8090/introspect")
    // ... handle response
}
```

## Development

### Running Tests

```bash
# Unit tests
go test -v

# With coverage
go test -v -cover

# Coverage report
go test -v -coverprofile=coverage.out
go tool cover -html=coverage.out
```

**Expected Coverage**: 95%+

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8090` | Service port |
| `JWT_SECRET` | `demo-secret-change-in-production` | JWT signing secret |
| `TOKEN_EXPIRY` | `15m` | Token expiration time |
| `LOG_LEVEL` | `info` | Logging level |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` | OpenTelemetry endpoint |

## Production Deployment

### JWT Secret Management

**DO NOT** use the default secret in production:

```bash
# Generate a strong secret
openssl rand -base64 64

# Set in environment
export JWT_SECRET="your-strong-secret-here"

# Or use Kubernetes secrets
kubectl create secret generic auth-service-secret \
  --from-literal=jwt-secret=$(openssl rand -base64 64)
```

### Kubernetes Deployment

```bash
kubectl apply -f k8s-deployment.yaml
```

Deployment includes:
- 3 replicas for high availability
- HPA (3-10 pods)
- PodDisruptionBudget (min 2 available)
- NetworkPolicy (restricted access)
- Resource limits
- Security context
- Health/readiness probes

## Compliance

### HIPAA

- Audit logging of all authentication events
- Secure token transmission (HTTPS only)
- Session timeout enforcement
- Access control via scopes

### SOX

- Audit trail of authentication events
- Role-based access control
- Separation of duties via scopes
- Tamper-evident logging

### Security Best Practices

- No sensitive data in logs (tokens redacted)
- Secure headers on all responses
- Token expiration enforced
- Failed auth attempts logged

## Troubleshooting

### Token Validation Fails

```bash
# Check token expiration
curl -H "Authorization: Bearer $TOKEN" http://localhost:8090/introspect

# Verify secret matches
echo $JWT_SECRET

# Check metrics for validation errors
curl http://localhost:8090/metrics | grep auth_tokens_validated_total
```

### High Latency

```bash
# Check metrics
curl http://localhost:8090/metrics | grep auth_request_duration

# Check active requests
curl http://localhost:8090/metrics | grep auth_active_requests

# View traces in Jaeger
open http://jaeger.example.com
```

### Security Events

```bash
# Check security event metrics
curl http://localhost:8090/metrics | grep auth_security_events_total

# View logs
kubectl logs -l app=auth-service -f | grep '"level":"warn"'
```

## Roadmap

- [ ] OAuth 2.0 / OIDC support
- [ ] Refresh tokens
- [ ] Multi-factor authentication (MFA)
- [ ] API key authentication
- [ ] Rate limiting per user
- [ ] Token revocation list
- [ ] Integration with external identity providers
- [ ] Audit log export to SIEM

## License

Internal use only - GitOps 2.0 Enterprise Platform

## Support

For issues or questions:
- Security Team (for vulnerability reports)
- Platform Engineering Team
- Compliance Team (for audit questions)
