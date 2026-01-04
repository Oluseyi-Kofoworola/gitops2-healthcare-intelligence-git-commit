package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/healthcare-gitops/common/config"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"go.opentelemetry.io/otel/trace"
)

var (
	encryptionService *EncryptionService
)

func main() {
	// Initialize structured logging
	initLogging()
	log.Info().Msg("Starting PHI Encryption Service...")

	// Load configuration from environment
	port := config.GetEnv("PORT", "8083")
	masterKey := os.Getenv("MASTER_KEY")
	if masterKey == "" {
		log.Fatal().Msg("MASTER_KEY environment variable is required (must be 32 bytes for AES-256)")
	}
	if len(masterKey) != 32 {
		log.Fatal().Int("length", len(masterKey)).Msg("MASTER_KEY must be exactly 32 bytes for AES-256-GCM")
	}

	// Initialize encryption service
	var err error
	encryptionService, err = NewEncryptionService(masterKey)
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to initialize encryption service")
	}
	log.Info().Msg("Encryption service initialized")

	// Initialize OpenTelemetry tracing (stub for lightweight deployment)
	if err := InitTracerProvider("phi-service"); err != nil {
		log.Warn().Err(err).Msg("Failed to initialize tracer provider, continuing without tracing")
	} else {
		ctx := context.Background()
		defer func() {
			if err := ShutdownTracer(ctx); err != nil {
				log.Error().Err(err).Msg("Failed to shutdown tracer provider")
			}
		}()
		log.Info().Msg("OpenTelemetry tracing initialized (stub mode)")
	}

	// Setup HTTP router
	r := chi.NewRouter()

	// Middleware stack
	r.Use(middleware.Recoverer)                 // Panic recovery
	r.Use(middleware.RealIP)                    // Get real client IP
	r.Use(middleware.RequestID)                 // Generate request ID
	r.Use(LoggingMiddleware)                    // Structured logging
	r.Use(TracingMiddleware)                    // OpenTelemetry tracing
	r.Use(PrometheusMiddleware)                 // Prometheus metrics
	r.Use(CORSMiddleware)                       // CORS support
	r.Use(middleware.Compress(5))               // Gzip compression
	r.Use(middleware.Timeout(30 * time.Second)) // Request timeout

	// Health & readiness endpoints
	r.Get("/health", HealthHandler)
	r.Get("/ready", ReadyHandler)

	// Metrics endpoint
	r.Handle("/metrics", promhttp.Handler())

	// API routes
	r.Route("/api/v1", func(r chi.Router) {
		r.Post("/encrypt", EncryptHandler)
		r.Post("/decrypt", DecryptHandler)
		r.Post("/hash", HashHandler)
		r.Post("/anonymize", AnonymizeHandler)
	})

	// Start HTTP server
	addr := ":" + port
	server := &http.Server{
		Addr:         addr,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in goroutine
	go func() {
		log.Info().Str("address", addr).Msg("HTTP server starting")
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal().Err(err).Msg("HTTP server failed")
		}
	}()

	// Wait for interrupt signal for graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info().Msg("Shutting down server...")

	// Graceful shutdown with 30 second timeout
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Error().Err(err).Msg("Server forced to shutdown")
	}

	log.Info().Msg("Server shutdown complete")
}

// initLogging configures structured logging with zerolog
func initLogging() {
	// Pretty logging for development
	if os.Getenv("ENV") == "development" {
		log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr, TimeFormat: time.RFC3339})
	} else {
		// JSON logging for production
		zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	}

	// Set log level
	logLevel := os.Getenv("LOG_LEVEL")
	switch logLevel {
	case "debug":
		zerolog.SetGlobalLevel(zerolog.DebugLevel)
	case "info":
		zerolog.SetGlobalLevel(zerolog.InfoLevel)
	case "warn":
		zerolog.SetGlobalLevel(zerolog.WarnLevel)
	case "error":
		zerolog.SetGlobalLevel(zerolog.ErrorLevel)
	default:
		zerolog.SetGlobalLevel(zerolog.InfoLevel)
	}
}



// HealthHandler handles health check endpoint
func HealthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "healthy",
		"service": "phi-service",
	})
}

// ReadyHandler handles readiness check endpoint
func ReadyHandler(w http.ResponseWriter, r *http.Request) {
	// Check if encryption service is initialized
	if encryptionService == nil {
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{
			"status": "not ready",
			"reason": "encryption service not initialized",
		})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ready",
		"service": "phi-service",
	})
}

// EncryptRequest represents encryption request payload
type EncryptRequest struct {
	Data string `json:"data"`
}

// EncryptResponse represents encryption response payload
type EncryptResponse struct {
	EncryptedData string `json:"encrypted_data"`
	RequestID     string `json:"request_id,omitempty"`
}

// DecryptRequest represents decryption request payload
type DecryptRequest struct {
	EncryptedData string `json:"encrypted_data"`
}

// DecryptResponse represents decryption response payload
type DecryptResponse struct {
	Data      string `json:"data"`
	RequestID string `json:"request_id,omitempty"`
}

// HashRequest represents hash request payload
type HashRequest struct {
	Data string `json:"data"`
}

// HashResponse represents hash response payload
type HashResponse struct {
	Hash      string `json:"hash"`
	RequestID string `json:"request_id,omitempty"`
}

// EncryptHandler handles encryption requests
func EncryptHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	var req EncryptRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		RecordEncryptionOp("encrypt", "error", time.Since(start).Seconds(), 0)
		return
	}

	// Encrypt data
	encrypted, err := encryptionService.Encrypt([]byte(req.Data))
	if err != nil {
		log.Error().Err(err).Msg("Encryption failed")
		http.Error(w, "Encryption failed", http.StatusInternalServerError)
		RecordEncryptionOp("encrypt", "error", time.Since(start).Seconds(), len(req.Data))
		span.RecordError(err)
		return
	}

	// Record metrics
	duration := time.Since(start).Seconds()
	RecordEncryptionOp("encrypt", "success", duration, len(req.Data))

	// Get request ID from context
	reqID := middleware.GetReqID(ctx)

	// Send response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(EncryptResponse{
		EncryptedData: encrypted,
		RequestID:     reqID,
	})
}

// DecryptHandler handles decryption requests
func DecryptHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	var req DecryptRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		RecordEncryptionOp("decrypt", "error", time.Since(start).Seconds(), 0)
		return
	}

	// Decrypt data
	decrypted, err := encryptionService.Decrypt(req.EncryptedData)
	if err != nil {
		log.Error().Err(err).Msg("Decryption failed")
		http.Error(w, "Decryption failed", http.StatusInternalServerError)
		RecordEncryptionOp("decrypt", "error", time.Since(start).Seconds(), len(req.EncryptedData))
		span.RecordError(err)
		return
	}

	// Record metrics
	duration := time.Since(start).Seconds()
	RecordEncryptionOp("decrypt", "success", duration, len(req.EncryptedData))

	// Get request ID from context
	reqID := middleware.GetReqID(ctx)

	// Send response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(DecryptResponse{
		Data:      string(decrypted),
		RequestID: reqID,
	})
}

// HashHandler handles hash requests
func HashHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	var req HashRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		RecordEncryptionOp("hash", "error", time.Since(start).Seconds(), 0)
		return
	}

	// Hash data
	hash, err := encryptionService.Hash([]byte(req.Data))
	if err != nil {
		log.Error().Err(err).Msg("Hashing failed")
		http.Error(w, "Hashing failed", http.StatusInternalServerError)
		RecordEncryptionOp("hash", "error", time.Since(start).Seconds(), len(req.Data))
		span.RecordError(err)
		return
	}

	// Record metrics
	duration := time.Since(start).Seconds()
	RecordEncryptionOp("hash", "success", duration, len(req.Data))

	// Get request ID from context
	reqID := middleware.GetReqID(ctx)

	// Send response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(HashResponse{
		Hash:      hash,
		RequestID: reqID,
	})
}

// AnonymizeHandler handles anonymization requests (hash with random salt)
func AnonymizeHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	var req HashRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		RecordEncryptionOp("anonymize", "error", time.Since(start).Seconds(), 0)
		return
	}

	// Generate salt
	salt, err := GenerateSalt()
	if err != nil {
		log.Error().Err(err).Msg("Failed to generate salt")
		http.Error(w, "Anonymization failed", http.StatusInternalServerError)
		RecordEncryptionOp("anonymize", "error", time.Since(start).Seconds(), len(req.Data))
		span.RecordError(err)
		return
	}

	// Hash with salt
	hash, err := encryptionService.HashWithSalt([]byte(req.Data), salt)
	if err != nil {
		log.Error().Err(err).Msg("Hashing with salt failed")
		http.Error(w, "Anonymization failed", http.StatusInternalServerError)
		RecordEncryptionOp("anonymize", "error", time.Since(start).Seconds(), len(req.Data))
		span.RecordError(err)
		return
	}

	// Record metrics
	duration := time.Since(start).Seconds()
	RecordEncryptionOp("anonymize", "success", duration, len(req.Data))

	// Get request ID from context
	reqID := middleware.GetReqID(ctx)

	// Send response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"hash":       hash,
		"salt":       fmt.Sprintf("%x", salt),
		"request_id": reqID,
	})
}
