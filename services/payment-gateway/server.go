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

    addr := ":" + cfg.Port
    log.Printf("starting %s on %s (max processing %dms)", cfg.ServiceName, addr, cfg.MaxProcessingMillis)

    return &http.Server{
        Addr:         addr,
        Handler:      router,
        ReadTimeout:  5 * time.Second,
        WriteTimeout: 10 * time.Second,
    }
}
