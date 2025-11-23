package main

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	// HTTP request duration histogram
	httpRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "phi_service_http_request_duration_seconds",
			Help:    "Duration of HTTP requests in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "path", "status"},
	)

	// HTTP request counter
	httpRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "phi_service_http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "path", "status"},
	)

	// Active HTTP requests gauge
	httpActiveRequests = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "phi_service_http_active_requests",
			Help: "Number of active HTTP requests",
		},
	)

	// Encryption operations counter
	encryptionOpsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "phi_service_encryption_operations_total",
			Help: "Total number of encryption operations",
		},
		[]string{"operation", "status"},
	)

	// Encryption duration histogram
	encryptionDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "phi_service_encryption_duration_seconds",
			Help:    "Duration of encryption operations in seconds",
			Buckets: []float64{.001, .005, .01, .025, .05, .1, .25, .5, 1},
		},
		[]string{"operation"},
	)

	// Data size histogram
	dataSize = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "phi_service_data_size_bytes",
			Help:    "Size of data processed in bytes",
			Buckets: []float64{100, 500, 1000, 5000, 10000, 50000, 100000},
		},
		[]string{"operation"},
	)
)

// RecordHTTPRequest records an HTTP request metric
func RecordHTTPRequest(method, path, status string, duration float64) {
	httpRequestDuration.WithLabelValues(method, path, status).Observe(duration)
	httpRequestsTotal.WithLabelValues(method, path, status).Inc()
}

// IncActiveRequests increments active requests
func IncActiveRequests() {
	httpActiveRequests.Inc()
}

// DecActiveRequests decrements active requests
func DecActiveRequests() {
	httpActiveRequests.Dec()
}

// RecordEncryptionOp records an encryption operation
func RecordEncryptionOp(operation, status string, duration float64, size int) {
	encryptionOpsTotal.WithLabelValues(operation, status).Inc()
	encryptionDuration.WithLabelValues(operation).Observe(duration)
	dataSize.WithLabelValues(operation).Observe(float64(size))
}
