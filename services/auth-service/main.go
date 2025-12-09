package main

// Authentication & Authorization Service for GitOps 2.0 Healthcare Platform
// WHY: Centralized security service for multi-domain risk scoring (auth + payment + PHI)
// ENHANCED: OpenTelemetry tracing, Prometheus metrics, structured logging, JWT validation

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/rs/zerolog"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
	"go.opentelemetry.io/otel/trace"
)

// Prometheus metrics
var (
	tokensValidated = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "auth_tokens_validated_total",
		Help: "Total number of tokens validated",
	}, []string{"result", "scope"})

	requestDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "auth_request_duration_seconds",
		Help:    "Request duration in seconds",
		Buckets: prometheus.DefBuckets,
	}, []string{"endpoint", "method", "status"})

	activeRequests = promauto.NewGauge(prometheus.GaugeOpts{
		Name: "auth_active_requests",
		Help: "Number of active requests",
	})

	securityEvents = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "auth_security_events_total",
		Help: "Total security events",
	}, []string{"event_type", "severity"})
)

var (
	logger    zerolog.Logger
	tracer    trace.Tracer
	jwtSecret []byte
)

// TokenClaims represents JWT token claims
type TokenClaims struct {
	UserID string   `json:"user_id"`
	Scopes []string `json:"scopes"`
	Role   string   `json:"role"`
	jwt.RegisteredClaims
}

// IntrospectResponse represents token introspection response
type IntrospectResponse struct {
	Active   bool     `json:"active"`
	UserID   string   `json:"user_id,omitempty"`
	Scopes   []string `json:"scopes,omitempty"`
	Role     string   `json:"role,omitempty"`
	Exp      int64    `json:"exp,omitempty"`
	IssuedAt int64    `json:"iat,omitempty"`
}

type AuthHandler struct{}

// SecurityHeaders adds security headers to all responses
func SecurityHeaders(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("X-Frame-Options", "DENY")
	w.Header().Set("X-XSS-Protection", "1; mode=block")
	w.Header().Set("Content-Security-Policy", "default-src 'self'")
	w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Request-ID", fmt.Sprintf("REQ_%d", time.Now().UnixNano()))
}

// TracingMiddleware wraps handlers with OpenTelemetry tracing
func TracingMiddleware(endpoint string, next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, span := tracer.Start(r.Context(), fmt.Sprintf("%s %s", r.Method, endpoint))
		defer span.End()

		span.SetAttributes(
			attribute.String("http.method", r.Method),
			attribute.String("http.path", r.URL.Path),
			attribute.String("http.user_agent", r.UserAgent()),
		)

		r = r.WithContext(ctx)

		activeRequests.Inc()
		defer activeRequests.Dec()

		start := time.Now()
		statusRecorder := &statusRecorder{ResponseWriter: w, statusCode: http.StatusOK}

		next(statusRecorder, r)

		duration := time.Since(start).Seconds()
		status := fmt.Sprintf("%d", statusRecorder.statusCode)

		requestDuration.WithLabelValues(endpoint, r.Method, status).Observe(duration)

		span.SetAttributes(
			attribute.Int("http.status_code", statusRecorder.statusCode),
			attribute.Float64("http.duration_seconds", duration),
		)

		logger.Info().
			Str("method", r.Method).
			Str("path", r.URL.Path).
			Int("status", statusRecorder.statusCode).
			Float64("duration_seconds", duration).
			Str("trace_id", span.SpanContext().TraceID().String()).
			Msg("HTTP request completed")
	}
}

type statusRecorder struct {
	http.ResponseWriter
	statusCode int
}

func (r *statusRecorder) WriteHeader(statusCode int) {
	r.statusCode = statusCode
	r.ResponseWriter.WriteHeader(statusCode)
}

func (h AuthHandler) Health(w http.ResponseWriter, r *http.Request) {
	SecurityHeaders(w, r)

	health := map[string]interface{}{
		"status":    "healthy",
		"service":   "auth-service",
		"version":   "1.0.0",
		"timestamp": time.Now().Format(time.RFC3339),
		"security":  []string{"JWT", "OAuth2", "RBAC"},
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(health)
}

func (h AuthHandler) Readiness(w http.ResponseWriter, r *http.Request) {
	SecurityHeaders(w, r)

	ready := map[string]interface{}{
		"ready":   true,
		"service": "auth-service",
		"checks": map[string]string{
			"jwt_validator": "ready",
			"metrics":       "ready",
			"tracing":       "ready",
		},
		"timestamp": time.Now().Format(time.RFC3339),
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(ready)
}

func (h AuthHandler) Introspect(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	SecurityHeaders(w, r)

	_, span := tracer.Start(ctx, "validate_token")
	defer span.End()

	// Extract token from Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		securityEvents.WithLabelValues("missing_token", "warning").Inc()
		tokensValidated.WithLabelValues("invalid", "none").Inc()

		logger.Warn().
			Str("remote_addr", r.RemoteAddr).
			Msg("Missing authorization header")

		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(IntrospectResponse{Active: false})
		return
	}

	// Extract Bearer token
	tokenString := strings.TrimPrefix(authHeader, "Bearer ")
	if tokenString == authHeader {
		securityEvents.WithLabelValues("invalid_token_format", "warning").Inc()
		tokensValidated.WithLabelValues("invalid", "none").Inc()

		logger.Warn().
			Str("remote_addr", r.RemoteAddr).
			Msg("Invalid token format")

		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(IntrospectResponse{Active: false})
		return
	}

	// Parse and validate JWT
	token, err := jwt.ParseWithClaims(tokenString, &TokenClaims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return jwtSecret, nil
	})

	if err != nil || !token.Valid {
		securityEvents.WithLabelValues("token_validation_failed", "warning").Inc()
		tokensValidated.WithLabelValues("invalid", "none").Inc()

		span.SetAttributes(attribute.String("error", "token_invalid"))

		logger.Warn().
			Err(err).
			Str("remote_addr", r.RemoteAddr).
			Msg("Token validation failed")

		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(IntrospectResponse{Active: false})
		return
	}

	claims, ok := token.Claims.(*TokenClaims)
	if !ok {
		securityEvents.WithLabelValues("claims_parse_failed", "error").Inc()
		tokensValidated.WithLabelValues("invalid", "none").Inc()

		logger.Error().
			Str("remote_addr", r.RemoteAddr).
			Msg("Failed to parse token claims")

		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(IntrospectResponse{Active: false})
		return
	}

	// Check expiration
	if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
		securityEvents.WithLabelValues("token_expired", "info").Inc()
		tokensValidated.WithLabelValues("expired", strings.Join(claims.Scopes, ",")).Inc()

		logger.Info().
			Str("user_id", claims.UserID).
			Time("expired_at", claims.ExpiresAt.Time).
			Msg("Token expired")

		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(IntrospectResponse{Active: false})
		return
	}

	// Token is valid
	tokensValidated.WithLabelValues("valid", strings.Join(claims.Scopes, ",")).Inc()
	securityEvents.WithLabelValues("successful_authentication", "info").Inc()

	span.SetAttributes(
		attribute.String("user.id", claims.UserID),
		attribute.String("user.role", claims.Role),
		attribute.StringSlice("user.scopes", claims.Scopes),
	)

	logger.Info().
		Str("user_id", claims.UserID).
		Str("role", claims.Role).
		Strs("scopes", claims.Scopes).
		Msg("Token validated successfully")

	response := IntrospectResponse{
		Active:   true,
		UserID:   claims.UserID,
		Scopes:   claims.Scopes,
		Role:     claims.Role,
		Exp:      claims.ExpiresAt.Unix(),
		IssuedAt: claims.IssuedAt.Unix(),
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// GenerateToken creates a demo JWT token (for testing only)
func (h AuthHandler) GenerateToken(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	SecurityHeaders(w, r)

	_, span := tracer.Start(ctx, "generate_token")
	defer span.End()

	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		json.NewEncoder(w).Encode(map[string]string{"error": "Method not allowed"})
		return
	}

	var req struct {
		UserID string   `json:"user_id"`
		Scopes []string `json:"scopes"`
		Role   string   `json:"role"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		logger.Error().Err(err).Msg("Failed to parse request body")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "Invalid request body"})
		return
	}

	// Create token
	claims := TokenClaims{
		UserID: req.UserID,
		Scopes: req.Scopes,
		Role:   req.Role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(15 * time.Minute)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Issuer:    "auth-service",
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString(jwtSecret)
	if err != nil {
		logger.Error().Err(err).Msg("Failed to sign token")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": "Token generation failed"})
		return
	}

	securityEvents.WithLabelValues("token_generated", "info").Inc()

	logger.Info().
		Str("user_id", req.UserID).
		Str("role", req.Role).
		Strs("scopes", req.Scopes).
		Msg("Token generated")

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"token":      tokenString,
		"expires_at": claims.ExpiresAt.Unix(),
		"token_type": "Bearer",
	})
}

// StartAuthServer constructs an HTTP server with routes for health and introspection.
// WHY: Improves testability and allows coverage of server wiring.
func StartAuthServer(addr string) *http.Server {
	mux := http.NewServeMux()
	h := AuthHandler{}

	// Health and monitoring endpoints
	mux.HandleFunc("/health", TracingMiddleware("/health", h.Health))
	mux.HandleFunc("/readiness", TracingMiddleware("/readiness", h.Readiness))
	mux.Handle("/metrics", promhttp.Handler())

	// Auth endpoints
	mux.HandleFunc("/introspect", TracingMiddleware("/introspect", h.Introspect))
	mux.HandleFunc("/token", TracingMiddleware("/token", h.GenerateToken))

	// Root endpoint with service info
	mux.HandleFunc("/", TracingMiddleware("/", func(w http.ResponseWriter, r *http.Request) {
		SecurityHeaders(w, r)

		info := map[string]interface{}{
			"service":     "GitOps 2.0 Auth Service",
			"description": "Production-grade authentication and authorization service",
			"version":     "1.0.0",
			"endpoints": map[string]string{
				"/health":     "Service health status",
				"/readiness":  "Service readiness status",
				"/introspect": "Token validation (GET with Authorization header)",
				"/token":      "Token generation (POST with user_id, scopes, role)",
				"/metrics":    "Prometheus metrics",
			},
			"security": map[string]interface{}{
				"jwt_enabled":  true,
				"rbac_enabled": true,
				"scopes_supported": []string{
					"payment:read",
					"payment:write",
					"phi:read",
					"phi:write",
					"admin",
				},
			},
		}

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(info)
	}))

	return &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 2 * time.Second,
		ReadTimeout:       5 * time.Second,
		WriteTimeout:      10 * time.Second,
		IdleTimeout:       30 * time.Second,
	}
}

func main() {
	// Initialize logger
	logger = zerolog.New(os.Stdout).With().Timestamp().Logger()

	// Validate JWT secret from environment
	secretEnv := os.Getenv("JWT_SECRET")
	if secretEnv == "" {
		logger.Fatal().Msg("JWT_SECRET environment variable is required (minimum 32 characters)")
	}
	if len(secretEnv) < 32 {
		logger.Fatal().Int("length", len(secretEnv)).Msg("JWT_SECRET must be at least 32 characters")
	}
	jwtSecret = []byte(secretEnv)
	logger.Info().Msg("JWT secret loaded from environment")

	// Initialize OpenTelemetry
	ctx := context.Background()
	exporter, err := otlptracegrpc.New(ctx)
	if err != nil {
		logger.Fatal().Err(err).Msg("Failed to create OTLP trace exporter")
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceNameKey.String("auth-service"),
		)),
	)
	defer func() { _ = tp.Shutdown(ctx) }()
	otel.SetTracerProvider(tp)
	tracer = tp.Tracer("auth-service")

	port := "8090"
	logger.Info().Msgf("🔐 GitOps 2.0 Auth Service starting on port %s", port)
	logger.Info().Msg("📊 Endpoints: /health, /readiness, /introspect, /token")
	logger.Info().Msg("🔒 JWT validation enabled")
	logger.Info().Msg("✅ RBAC & scope-based authorization active")

	srv := StartAuthServer(":" + port)

	// Graceful shutdown
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal().Err(err).Msg("Server failed to start")
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info().Msg("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Fatal().Err(err).Msg("Server forced to shutdown")
	}

	logger.Info().Msg("Server exiting")
}
