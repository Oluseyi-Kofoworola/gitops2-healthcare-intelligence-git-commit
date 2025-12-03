# Medical Device Monitoring Service

[![Go Version](https://img.shields.io/badge/Go-1.21+-00ADD8?style=flat&logo=go)](https://go.dev/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FDA Compliance](https://img.shields.io/badge/FDA-21_CFR_Part_11-green.svg)](https://www.fda.gov/)

Production-grade medical device monitoring service for FDA-regulated healthcare environments with real-time telemetry, calibration management, and compliance tracking.

## 🏥 Overview

The Medical Device Monitoring Service provides centralized monitoring, management, and compliance tracking for FDA-regulated medical devices including MRI machines, CT scanners, ventilators, ECG monitors, and infusion pumps.

**Key Features**:
- 🔍 Real-time device monitoring & telemetry
- 📊 Device metrics collection (temperature, power, CPU, memory)
- 🔧 Calibration & maintenance scheduling
- 🚨 Alert management & notifications
- 🔬 Diagnostic operations
- 📋 FDA 21 CFR Part 11 compliance support
- 🔐 Audit trail for all operations
- 📈 OpenTelemetry distributed tracing
- 📊 Prometheus metrics
- 📝 Structured JSON logging

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Medical Device Service                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Device     │  │   Metrics    │  │   Alert      │     │
│  │  Registry    │  │  Collector   │  │  Manager     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                         │                                    │
│  ┌──────────────────────┴────────────────────────┐         │
│  │         REST API (14 Endpoints)                │         │
│  └──────────────────────────────────────────────┬─┘         │
│                                                  │           │
│  ┌────────────────┬─────────────────┬───────────┴─────┐    │
│  │ OpenTelemetry  │   Prometheus    │   Zerolog       │    │
│  │    Tracing     │    Metrics      │   Logging       │    │
│  └────────────────┴─────────────────┴─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │   MRI   │      │   ECG   │      │  Vent   │
    │ Scanner │      │ Monitor │      │ ilator  │
    └─────────┘      └─────────┘      └─────────┘
```

## 🚀 Quick Start

### Prerequisites

- Go 1.21+
- Docker (optional)
- Kubernetes cluster (optional)

### Local Development

```bash
# Clone repository
git clone https://github.com/example/gitops2-enterprise.git
cd services/medical-device

# Install dependencies
go mod download

# Set environment variables
export PORT=8084
export JWT_SECRET=your-secret-key
export OTLP_ENDPOINT=localhost:4317

# Run service
go run .
```

The service will start on `http://localhost:8084`

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8084` | HTTP server port |
| `OTLP_ENDPOINT` | `localhost:4317` | OpenTelemetry collector endpoint |
| `LOG_LEVEL` | `info` | Log level (debug, info, warn, error) |
| `ENV` | `production` | Environment (development, production) |
| `ENABLE_SIMULATOR` | `true` | Enable demo device simulator |

## 📡 API Endpoints

### Device Management

#### Register Device
```http
POST /api/v1/devices
Content-Type: application/json

{
  "id": "MRI-001",
  "type": "MRI",
  "location": "Radiology - Room 101",
  "serial_number": "MRI-2024-001",
  "manufacturer": "Siemens Healthineers",
  "model": "MAGNETOM Vida",
  "firmware_version": "VA30A"
}
```

#### List All Devices
```http
GET /api/v1/devices
```

Response:
```json
{
  "devices": [
    {
      "id": "MRI-001",
      "type": "MRI",
      "status": "operational",
      "location": "Radiology - Room 101",
      "serial_number": "MRI-2024-001",
      "manufacturer": "Siemens Healthineers",
      "model": "MAGNETOM Vida",
      "firmware_version": "VA30A",
      "last_calibration": "2024-11-22T10:00:00Z",
      "next_maintenance": "2024-12-22T10:00:00Z",
      "uptime_seconds": 86400,
      "error_count": 0,
      "alert_level": "none"
    }
  ],
  "count": 1
}
```

#### Get Device Details
```http
GET /api/v1/devices/{deviceID}
```

#### Update Device
```http
PUT /api/v1/devices/{deviceID}
Content-Type: application/json

{
  "status": "maintenance",
  "firmware_version": "VA30B"
}
```

#### Deregister Device
```http
DELETE /api/v1/devices/{deviceID}
```

### Device Metrics

#### Get Device Metrics
```http
GET /api/v1/devices/{deviceID}/metrics
```

Response:
```json
{
  "temperature_celsius": 23.5,
  "power_consumption_watts": 750.2,
  "cpu_utilization_percent": 45.8,
  "memory_usage_percent": 62.3,
  "network_latency_ms": 8.2,
  "last_updated": "2024-11-23T14:30:00Z"
}
```

#### Update Device Metrics
```http
POST /api/v1/devices/{deviceID}/metrics
Content-Type: application/json

{
  "temperature_celsius": 24.0,
  "power_consumption_watts": 800.0,
  "cpu_utilization_percent": 50.0,
  "memory_usage_percent": 65.0,
  "network_latency_ms": 10.0
}
```

### Device Operations

#### Calibrate Device
```http
POST /api/v1/devices/{deviceID}/calibrate
```

Response:
```json
{
  "device_id": "MRI-001",
  "last_calibration": "2024-11-23T14:30:00Z",
  "status": "calibration_complete"
}
```

#### Schedule Maintenance
```http
POST /api/v1/devices/{deviceID}/maintenance
Content-Type: application/json

{
  "scheduled_time": "2024-12-01T09:00:00Z"
}
```

#### Run Diagnostics
```http
POST /api/v1/devices/{deviceID}/diagnostics
```

Response:
```json
{
  "device_id": "MRI-001",
  "type": "MRI",
  "status": "operational",
  "error_count": 0,
  "uptime": 86400,
  "tests_run": 5,
  "tests_passed": 5,
  "tests_failed": 0,
  "result": "pass",
  "timestamp": "2024-11-23T14:30:00Z"
}
```

### Monitoring

#### List Active Alerts
```http
GET /api/v1/alerts
```

#### Get Device Status
```http
GET /api/v1/devices/{deviceID}/status
```

### Health & Metrics

```http
GET /health          # Health check
GET /ready           # Readiness check
GET /metrics         # Prometheus metrics
```

## 📊 Supported Device Types

| Type | Description | Common Models |
|------|-------------|---------------|
| `MRI` | Magnetic Resonance Imaging | Siemens MAGNETOM, GE Signa |
| `CT_Scanner` | Computed Tomography | GE Revolution, Philips iCT |
| `X-Ray` | X-Ray Imaging System | Carestream DRX, Siemens Ysio |
| `ECG` | Electrocardiogram Monitor | GE MAC 2000, Philips IntelliVue |
| `Ventilator` | Mechanical Ventilator | Dräger Evita, Hamilton C6 |
| `Infusion_Pump` | IV Infusion Pump | Baxter Sigma, B.Braun Infusomat |

## 📈 Observability

### OpenTelemetry Tracing

The service exports traces to an OTLP collector:

```yaml
# Span attributes
- device.id
- device.type
- operation.type
- http.method
- http.status_code
```

### Prometheus Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `medical_device_http_requests_total` | Counter | Total HTTP requests |
| `medical_device_http_request_duration_seconds` | Histogram | Request duration |
| `medical_device_operations_total` | Counter | Total device operations |
| `medical_device_operation_duration_seconds` | Histogram | Operation duration |
| `medical_device_registered_total` | Gauge | Total registered devices |
| `medical_device_active_alerts_total` | Gauge | Active alerts count |
| `medical_device_status` | Gauge | Device status (1=operational) |
| `medical_device_uptime_seconds` | Gauge | Device uptime |
| `medical_device_errors_total` | Counter | Device errors |

### Structured Logging

All logs are in JSON format using zerolog:

```json
{
  "level": "info",
  "time": "2024-11-23T14:30:00Z",
  "message": "Device registered",
  "device_id": "MRI-001",
  "type": "MRI",
  "request_id": "abc123"
}
```

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t medical-device-service:latest .
```

### Run Container

```bash
docker run -d \
  -p 8084:8084 \
  -e OTLP_ENDPOINT=otel-collector:4317 \
  -e LOG_LEVEL=info \
  --name medical-device \
  medical-device-service:latest
```

## ☸️ Kubernetes Deployment

### Deploy to Kubernetes

```bash
kubectl apply -f k8s-deployment.yaml
```

### Resources Created

- **Deployment**: 3 replicas with auto-scaling
- **Service**: ClusterIP with load balancing
- **HorizontalPodAutoscaler**: 3-15 replicas based on CPU/memory
- **PodDisruptionBudget**: Ensures 2 pods always available
- **NetworkPolicy**: Zero-trust network security
- **ServiceMonitor**: Prometheus scraping
- **ConfigMap**: Configuration management
- **Secret**: Sensitive data storage

### Access Service

```bash
# Port forward for local access
kubectl port-forward svc/medical-device-service 8084:80

# Test health endpoint
curl http://localhost:8084/health
```

## 🔐 Security & Compliance

### FDA 21 CFR Part 11 Compliance

- ✅ **Audit Trail**: All operations logged with timestamps
- ✅ **Electronic Signatures**: Request ID tracking
- ✅ **Data Integrity**: Immutable event logging
- ✅ **Access Control**: Network policies & RBAC
- ✅ **System Validation**: Comprehensive test coverage

### Security Features

- ✅ Non-root container user (UID 65532)
- ✅ Read-only root filesystem
- ✅ Dropped capabilities (ALL)
- ✅ NetworkPolicy for ingress/egress control
- ✅ CORS middleware
- ✅ Request timeout (30s)
- ✅ Graceful shutdown

## 🧪 Testing

### Run Unit Tests

```bash
go test -v ./...
```

### Run with Coverage

```bash
go test -v -cover -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### Expected Coverage

**Target**: 95%+ code coverage

## 🔧 Configuration

### Device Simulator

The built-in simulator creates sample devices for demo purposes:

```go
// Enable/disable in environment
ENABLE_SIMULATOR=true

// Creates 3 sample devices:
- MRI-001 (Siemens MAGNETOM Vida)
- ECG-002 (GE MAC 2000)
- VENT-003 (Dräger Evita V800)
```

Metrics are updated every 10 seconds with realistic values.

## 📋 Troubleshooting

### Service won't start

```bash
# Check logs
kubectl logs -l app=medical-device-service

# Verify configuration
kubectl get configmap medical-device-config -o yaml
```

### Devices not registering

- Verify device ID is unique
- Check required fields: `id`, `type`
- Review audit logs for validation errors

### Metrics not appearing

- Verify Prometheus ServiceMonitor is created
- Check OTLP endpoint is accessible
- Review network policy allows egress to collector

### High memory usage

- Review device count (each device stores metrics)
- Adjust HPA settings for scale-up threshold
- Consider implementing metrics retention policy

## 🛣️ Roadmap

- [ ] WebSocket support for real-time device updates
- [ ] Integration with HL7 FHIR for device data exchange
- [ ] Advanced analytics & predictive maintenance
- [ ] Multi-tenancy support
- [ ] Device firmware update management
- [ ] Enhanced alert rules engine
- [ ] Integration with PACS systems

## 📚 Related Documentation

- [OpenAPI Specification](./openapi.yaml)
- [Architecture Decision Records](../../docs/)
- [FDA Compliance Guide](../../docs/COMPLIANCE_GUIDE.md)
- [Enterprise Readiness](../../docs/ENTERPRISE_READINESS.md)

## 🤝 Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](../../LICENSE)

## 🆘 Support

- **Issues**: GitHub Issues
- **Email**: support@example.com
- **Slack**: #medical-device-service

---

**Version**: 1.0.0  
**Last Updated**: November 23, 2025  
**Maintainer**: Platform Engineering Team
