package main

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	// HTTP request metrics
	httpRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "medical_device_http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "endpoint", "status"},
	)

	httpRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "medical_device_http_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "endpoint", "status"},
	)

	// Device operation metrics
	deviceOperationsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "medical_device_operations_total",
			Help: "Total number of device operations",
		},
		[]string{"operation", "status"},
	)

	deviceOperationDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "medical_device_operation_duration_seconds",
			Help:    "Device operation duration in seconds",
			Buckets: []float64{0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0},
		},
		[]string{"operation", "status"},
	)

	// Device status metrics
	registeredDevicesTotal = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "medical_device_registered_total",
			Help: "Total number of registered devices",
		},
	)

	activeAlertsTotal = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "medical_device_active_alerts_total",
			Help: "Total number of active device alerts",
		},
	)

	deviceStatusGauge = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "medical_device_status",
			Help: "Device status (1=operational, 0=not operational)",
		},
		[]string{"device_id", "device_type", "status"},
	)

	deviceUptimeSeconds = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "medical_device_uptime_seconds",
			Help: "Device uptime in seconds",
		},
		[]string{"device_id", "device_type"},
	)

	deviceErrorsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "medical_device_errors_total",
			Help: "Total number of device errors",
		},
		[]string{"device_id", "device_type"},
	)
)

// RecordDeviceOperation records metrics for a device operation
func RecordDeviceOperation(operation, status string, duration float64) {
	deviceOperationsTotal.WithLabelValues(operation, status).Inc()
	deviceOperationDuration.WithLabelValues(operation, status).Observe(duration)
}

// UpdateDeviceMetrics updates Prometheus metrics for a device
func UpdateDeviceMetrics(deviceID string, deviceType DeviceType, status DeviceStatus, uptime int64, errors int) {
	statusValue := 0.0
	if status == StatusOperational {
		statusValue = 1.0
	}

	deviceStatusGauge.WithLabelValues(deviceID, string(deviceType), string(status)).Set(statusValue)
	deviceUptimeSeconds.WithLabelValues(deviceID, string(deviceType)).Set(float64(uptime))

	if errors > 0 {
		deviceErrorsTotal.WithLabelValues(deviceID, string(deviceType)).Add(float64(errors))
	}
}

// UpdateRegistryMetrics updates global registry metrics
func UpdateRegistryMetrics(deviceCount, alertCount int) {
	registeredDevicesTotal.Set(float64(deviceCount))
	activeAlertsTotal.Set(float64(alertCount))
}
