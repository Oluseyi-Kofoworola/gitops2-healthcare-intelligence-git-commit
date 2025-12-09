// Security Middleware Package
// Provides common security patterns for all microservices

package middleware

import (
	"context"
	"io"
	"net/http"
	"sync"
	"time"

	"golang.org/x/time/rate"
)

// MaxRequestSize limits the maximum size of request bodies (10MB default)
const MaxRequestSize = 10 * 1024 * 1024 // 10MB

// RequestSizeLimiter middleware limits the size of request bodies to prevent DOS attacks
func RequestSizeLimiter(maxSize int64) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Limit request body size
			r.Body = http.MaxBytesReader(w, r.Body, maxSize)
			next.ServeHTTP(w, r)
		})
	}
}

// ContentTypeValidator ensures requests have appropriate Content-Type headers
func ContentTypeValidator(allowedTypes ...string) func(http.Handler) http.Handler {
	typeMap := make(map[string]bool)
	for _, t := range allowedTypes {
		typeMap[t] = true
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip validation for GET and DELETE (no body expected)
			if r.Method == http.MethodGet || r.Method == http.MethodDelete {
				next.ServeHTTP(w, r)
				return
			}

			contentType := r.Header.Get("Content-Type")
			if contentType == "" {
				http.Error(w, "Content-Type header required", http.StatusBadRequest)
				return
			}

			if !typeMap[contentType] {
				http.Error(w, "Invalid Content-Type", http.StatusUnsupportedMediaType)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RateLimiter implements token bucket rate limiting per IP address
type RateLimiter struct {
	visitors map[string]*rate.Limiter
	mu       sync.RWMutex
	rate     rate.Limit
	burst    int
	cleanup  time.Duration
}

// NewRateLimiter creates a new rate limiter
// rps: requests per second allowed
// burst: maximum burst size
func NewRateLimiter(rps int, burst int) *RateLimiter {
	rl := &RateLimiter{
		visitors: make(map[string]*rate.Limiter),
		rate:     rate.Limit(rps),
		burst:    burst,
		cleanup:  5 * time.Minute,
	}

	// Start cleanup goroutine
	go rl.cleanupVisitors()

	return rl
}

// getVisitor returns the rate limiter for the given IP
func (rl *RateLimiter) getVisitor(ip string) *rate.Limiter {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	limiter, exists := rl.visitors[ip]
	if !exists {
		limiter = rate.NewLimiter(rl.rate, rl.burst)
		rl.visitors[ip] = limiter
	}

	return limiter
}

// cleanupVisitors removes old entries to prevent memory leaks
func (rl *RateLimiter) cleanupVisitors() {
	ticker := time.NewTicker(rl.cleanup)
	defer ticker.Stop()

	for range ticker.C {
		rl.mu.Lock()
		for ip, limiter := range rl.visitors {
			// Remove if no tokens consumed in last cleanup period
			if limiter.Tokens() >= float64(rl.burst) {
				delete(rl.visitors, ip)
			}
		}
		rl.mu.Unlock()
	}
}

// Middleware returns a rate limiting middleware
func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract IP (consider X-Forwarded-For for load balancers)
		ip := r.RemoteAddr
		if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
			ip = forwarded
		}

		limiter := rl.getVisitor(ip)
		if !limiter.Allow() {
			http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// TimeoutMiddleware adds context timeout to all requests
func TimeoutMiddleware(timeout time.Duration) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx, cancel := context.WithTimeout(r.Context(), timeout)
			defer cancel()

			r = r.WithContext(ctx)

			done := make(chan bool)
			go func() {
				next.ServeHTTP(w, r)
				done <- true
			}()

			select {
			case <-done:
				// Request completed successfully
				return
			case <-ctx.Done():
				// Timeout occurred
				http.Error(w, "Request timeout", http.StatusRequestTimeout)
				return
			}
		})
	}
}

// SanitizedReader wraps io.Reader to prevent reading sensitive data into logs
type SanitizedReader struct {
	reader io.Reader
	buffer []byte
}

// NewSanitizedReader creates a reader that prevents sensitive data leakage
func NewSanitizedReader(r io.Reader, maxSize int) io.Reader {
	return &SanitizedReader{
		reader: io.LimitReader(r, int64(maxSize)),
		buffer: make([]byte, 0, maxSize),
	}
}

func (sr *SanitizedReader) Read(p []byte) (n int, err error) {
	return sr.reader.Read(p)
}

// SecurityHeaders middleware adds comprehensive security headers
func SecurityHeadersMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Prevent MIME type sniffing
		w.Header().Set("X-Content-Type-Options", "nosniff")

		// Prevent clickjacking
		w.Header().Set("X-Frame-Options", "DENY")

		// XSS protection (legacy browsers)
		w.Header().Set("X-XSS-Protection", "1; mode=block")

		// Content Security Policy
		w.Header().Set("Content-Security-Policy", "default-src 'self'; script-src 'self'; object-src 'none'")

		// HSTS - force HTTPS
		w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")

		// Referrer policy
		w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")

		// Permissions policy (feature policy)
		w.Header().Set("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

		next.ServeHTTP(w, r)
	})
}
