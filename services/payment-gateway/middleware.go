package main

import (
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/rs/zerolog/log"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

// TracingMiddleware adds OpenTelemetry tracing to HTTP requests
func TracingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		tracer := GetTracer()
		ctx, span := tracer.Start(r.Context(), r.Method+" "+r.URL.Path,
			trace.WithAttributes(
				attribute.String("http.method", r.Method),
				attribute.String("http.url", r.URL.String()),
				attribute.String("http.scheme", r.URL.Scheme),
				attribute.String("http.host", r.Host),
			),
		)
		defer span.End()

		// Add request ID
		requestID := r.Header.Get("X-Request-ID")
		if requestID == "" {
			requestID = uuid.New().String()
		}
		span.SetAttributes(attribute.String("http.request_id", requestID))

		// Propagate context
		r = r.WithContext(ctx)

		// Create response writer wrapper to capture status code
		rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		// Call next handler
		next.ServeHTTP(rw, r)

		// Add response status to span
		span.SetAttributes(
			attribute.Int("http.status_code", rw.statusCode),
			attribute.Bool("http.success", rw.statusCode < 400),
		)

		// Set span status based on HTTP status
		if rw.statusCode >= 500 {
			span.SetAttributes(attribute.Bool("error", true))
		}
	})
}

// LoggingMiddleware logs HTTP requests with structured logging
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Get or generate request ID
		requestID := r.Header.Get("X-Request-ID")
		if requestID == "" {
			requestID = uuid.New().String()
			r.Header.Set("X-Request-ID", requestID)
		}

		// Set request ID in response header
		w.Header().Set("X-Request-ID", requestID)

		// Create response writer wrapper
		rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		// Log request
		log.Info().
			Str("request_id", requestID).
			Str("method", r.Method).
			Str("path", r.URL.Path).
			Str("remote_addr", r.RemoteAddr).
			Str("user_agent", r.UserAgent()).
			Msg("Incoming request")

		// Call next handler
		next.ServeHTTP(rw, r)

		// Log response
		duration := time.Since(start)
		logEvent := log.Info()
		if rw.statusCode >= 500 {
			logEvent = log.Error()
		} else if rw.statusCode >= 400 {
			logEvent = log.Warn()
		}

		logEvent.
			Str("request_id", requestID).
			Str("method", r.Method).
			Str("path", r.URL.Path).
			Int("status", rw.statusCode).
			Dur("duration_ms", duration).
			Int64("bytes", rw.bytesWritten).
			Msg("Request completed")
	})
}

// PrometheusMiddleware records Prometheus metrics for HTTP requests
func PrometheusMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create response writer wrapper
		rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		// Call next handler
		next.ServeHTTP(rw, r)

		// Record metrics
		duration := time.Since(start)

		// Update request duration histogram
		RecordRequestDuration(r.Method, r.URL.Path, rw.statusCode, duration)

		// Update request counter
		RecordRequestCount(r.Method, r.URL.Path, rw.statusCode)
	})
}

// responseWriter wraps http.ResponseWriter to capture status code and bytes written
type responseWriter struct {
	http.ResponseWriter
	statusCode   int
	bytesWritten int64
}

func (rw *responseWriter) WriteHeader(statusCode int) {
	rw.statusCode = statusCode
	rw.ResponseWriter.WriteHeader(statusCode)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
	n, err := rw.ResponseWriter.Write(b)
	rw.bytesWritten += int64(n)
	return n, err
}
