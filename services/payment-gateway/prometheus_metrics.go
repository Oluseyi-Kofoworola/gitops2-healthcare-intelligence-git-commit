package main

import (
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	// Request duration histogram
	requestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "payment_gateway_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "path", "status"},
	)

	// Request counter
	requestCount = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "payment_gateway_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "path", "status"},
	)

	// Active requests gauge
	activeRequests = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "payment_gateway_active_requests",
			Help: "Number of active HTTP requests",
		},
	)

	// Payment transaction metrics
	paymentTransactions = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "payment_gateway_transactions_total",
			Help: "Total number of payment transactions",
		},
		[]string{"status", "compliance_type"},
	)

	// Payment processing duration
	paymentProcessingDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "payment_gateway_processing_duration_seconds",
			Help:    "Payment processing duration in seconds",
			Buckets: []float64{.001, .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10},
		},
		[]string{"status"},
	)
)

// RecordRequestDuration records HTTP request duration
func RecordRequestDuration(method, path string, statusCode int, duration time.Duration) {
	requestDuration.WithLabelValues(
		method,
		path,
		http.StatusText(statusCode),
	).Observe(duration.Seconds())
}

// RecordRequestCount increments HTTP request counter
func RecordRequestCount(method, path string, statusCode int) {
	requestCount.WithLabelValues(
		method,
		path,
		http.StatusText(statusCode),
	).Inc()
}

// RecordPaymentTransaction records a payment transaction
func RecordPaymentTransaction(success bool, complianceType string) {
	status := "success"
	if !success {
		status = "failure"
	}
	paymentTransactions.WithLabelValues(status, complianceType).Inc()
}

// RecordPaymentDuration records payment processing duration
func RecordPaymentDuration(duration time.Duration, success bool) {
	status := "success"
	if !success {
		status = "failure"
	}
	paymentProcessingDuration.WithLabelValues(status).Observe(duration.Seconds())
}
