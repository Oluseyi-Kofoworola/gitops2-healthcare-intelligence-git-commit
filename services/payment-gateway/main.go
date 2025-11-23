package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func main() {
	// Initialize structured logging
	initLogging()

	log.Info().Msg("Starting Payment Gateway Service")

	// Load configuration
	cfg := LoadConfig()

	// Initialize OpenTelemetry tracing
	shutdown, err := InitTracing(cfg.ServiceName)
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to initialize tracing")
	}
	defer shutdown(context.Background())

	log.Info().Str("service", cfg.ServiceName).Str("port", cfg.Port).Msg("Configuration loaded")

	// Create server with observability
	server := NewServer(cfg)

	// Start server in goroutine
	go func() {
		log.Info().Str("address", server.Addr).Msg("Starting HTTP server")
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal().Err(err).Msg("Server failed")
		}
	}()

	// Graceful shutdown handling
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info().Msg("Shutdown signal received, gracefully stopping server...")

	// Give outstanding requests 30 seconds to complete
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatal().Err(err).Msg("Server forced to shutdown")
	}

	log.Info().Msg("Server exited gracefully")
}

// initLogging initializes zerolog with JSON output
func initLogging() {
	// Use JSON logging in production, pretty console in development
	if os.Getenv("ENVIRONMENT") == "development" {
		log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr})
	} else {
		zerolog.TimeFieldFormat = time.RFC3339
	}

	// Set log level from environment (default: info)
	logLevel := os.Getenv("LOG_LEVEL")
	switch logLevel {
	case "debug":
		zerolog.SetGlobalLevel(zerolog.DebugLevel)
	case "warn":
		zerolog.SetGlobalLevel(zerolog.WarnLevel)
	case "error":
		zerolog.SetGlobalLevel(zerolog.ErrorLevel)
	default:
		zerolog.SetGlobalLevel(zerolog.InfoLevel)
	}

	log.Info().Str("level", logLevel).Msg("Logging initialized")
}

// InitTracing initializes OpenTelemetry tracing
func InitTracing(serviceName string) (func(context.Context) error, error) {
	// Get OTLP endpoint from environment
	otlpEndpoint := os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
	if otlpEndpoint == "" {
		otlpEndpoint = "http://otel-collector.observability:4317"
		log.Warn().Msg("OTEL_EXPORTER_OTLP_ENDPOINT not set, using default: " + otlpEndpoint)
	}

	tp, err := InitTracerProvider(serviceName, otlpEndpoint)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize tracer provider: %w", err)
	}

	log.Info().
		Str("service", serviceName).
		Str("endpoint", otlpEndpoint).
		Msg("OpenTelemetry tracing initialized")

	return tp.Shutdown, nil
}
