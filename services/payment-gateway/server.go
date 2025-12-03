package main

import (
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/rs/zerolog/log"
)

func NewServer(cfg Config) *http.Server {
	router := chi.NewRouter()

	// Add middleware stack
	router.Use(middleware.Recoverer)                 // Recover from panics
	router.Use(middleware.RealIP)                    // Get real client IP
	router.Use(middleware.RequestID)                 // Add request ID
	router.Use(LoggingMiddleware)                    // Structured logging
	router.Use(TracingMiddleware)                    // OpenTelemetry tracing
	router.Use(PrometheusMiddleware)                 // Prometheus metrics
	router.Use(middleware.Compress(5))               // Gzip compression
	router.Use(middleware.Timeout(30 * time.Second)) // Request timeout

	// Payment handler
	handler := PaymentHandler{
		MaxLatency: processingTimeout(cfg.MaxProcessingMillis),
	}

	// Health and readiness endpoints
	router.Get("/health", handler.Health)
	router.Get("/readiness", handler.Readiness)

	// Payment processing endpoints
	router.Post("/charge", handler.Charge)
	router.Post("/process", handler.ProcessPayment)

	// Observability endpoints
	router.Handle("/metrics", promhttp.Handler())
	router.Get("/compliance/status", handler.ComplianceStatusHandler)
	router.Get("/audit/trail", handler.AuditTrailHandler)
	router.Get("/alerts", handler.AlertingHandler)

	addr := ":" + cfg.Port
	log.Info().
		Str("service", cfg.ServiceName).
		Str("address", addr).
		Int("max_processing_ms", cfg.MaxProcessingMillis).
		Msg("Server configured")

	return &http.Server{
		Addr:         addr,
		Handler:      router,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}
}
