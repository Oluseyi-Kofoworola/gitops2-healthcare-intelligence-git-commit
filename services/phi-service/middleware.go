package main

import (
	"net/http"
	"time"

	"github.com/go-chi/chi/v5/middleware"
	"github.com/rs/zerolog/log"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/trace"
)

// LoggingMiddleware logs HTTP requests with structured logging
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Wrap response writer to capture status code
		ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

		// Get request ID from context
		reqID := middleware.GetReqID(r.Context())

		log.Info().
			Str("request_id", reqID).
			Str("method", r.Method).
			Str("path", r.URL.Path).
			Str("remote_addr", r.RemoteAddr).
			Str("user_agent", r.UserAgent()).
			Msg("Incoming request")

		next.ServeHTTP(ww, r)

		duration := time.Since(start)

		log.Info().
			Str("request_id", reqID).
			Str("method", r.Method).
			Str("path", r.URL.Path).
			Int("status", ww.Status()).
			Int("bytes", ww.BytesWritten()).
			Dur("duration_ms", duration).
			Msg("Request completed")
	})
}

// TracingMiddleware adds OpenTelemetry tracing to HTTP requests
func TracingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		tracer := GetTracer()

		// Start span
		ctx, span := tracer.Start(r.Context(), r.URL.Path,
			trace.WithAttributes(
				attribute.String("http.method", r.Method),
				attribute.String("http.url", r.URL.String()),
				attribute.String("http.user_agent", r.UserAgent()),
			),
		)
		defer span.End()

		// Wrap response writer to capture status code
		ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

		// Call next handler with traced context
		next.ServeHTTP(ww, r.WithContext(ctx))

		// Record response details
		span.SetAttributes(
			attribute.Int("http.status_code", ww.Status()),
			attribute.Int("http.response_size", ww.BytesWritten()),
		)

		// Mark span as error if status >= 500
		if ww.Status() >= 500 {
			span.SetStatus(codes.Error, http.StatusText(ww.Status()))
		}
	})
}

// PrometheusMiddleware records Prometheus metrics for HTTP requests
func PrometheusMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Increment active requests
		IncActiveRequests()
		defer DecActiveRequests()

		// Wrap response writer to capture status code
		ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

		// Call next handler
		next.ServeHTTP(ww, r)

		// Record metrics
		duration := time.Since(start).Seconds()
		statusCode := ww.Status()
		RecordHTTPRequest(r.Method, r.URL.Path, statusCode, duration)
	})
}

// CORSMiddleware adds CORS headers for development
func CORSMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}
