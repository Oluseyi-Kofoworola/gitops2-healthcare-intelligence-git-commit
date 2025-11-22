package main

import (
	"log"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
)

func NewServer(cfg Config) *http.Server {
	router := chi.NewRouter()
	handler := PaymentHandler{
		MaxLatency: processingTimeout(cfg.MaxProcessingMillis),
	}

	router.Get("/health", handler.Health)
	router.Post("/charge", handler.Charge)
	// Provide explicit route for ProcessPayment if integration tests call HTTP path differently
	router.Post("/process", handler.ProcessPayment)

	// Optional monitoring endpoints used by healthcare monitoring
	router.Get("/metrics", handler.MetricsHandler)
	router.Get("/compliance/status", handler.ComplianceStatusHandler)
	router.Get("/audit/trail", handler.AuditTrailHandler)
	router.Get("/alerts", handler.AlertingHandler)

	addr := ":" + cfg.Port
	log.Printf("starting %s on %s (max processing %dms)", cfg.ServiceName, addr, cfg.MaxProcessingMillis)

	return &http.Server{
		Addr:         addr,
		Handler:      router,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
	}
}
