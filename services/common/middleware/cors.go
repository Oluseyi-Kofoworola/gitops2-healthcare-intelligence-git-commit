// SPDX-License-Identifier: MIT
// Copyright (c) 2025 GitOps Healthcare Intelligence Platform

package middleware

import (
	"net/http"
	"os"
	"strings"
)

// CORSConfig holds CORS configuration
type CORSConfig struct {
	AllowedOrigins   []string
	AllowedMethods   []string
	AllowedHeaders   []string
	ExposedHeaders   []string
	AllowCredentials bool
	MaxAge           int
}

// DefaultCORSConfig returns secure default CORS configuration
func DefaultCORSConfig() *CORSConfig {
	return &CORSConfig{
		AllowedOrigins: getAllowedOrigins(),
		AllowedMethods: []string{
			http.MethodGet,
			http.MethodPost,
			http.MethodPut,
			http.MethodDelete,
			http.MethodOptions,
		},
		AllowedHeaders: []string{
			"Authorization",
			"Content-Type",
			"X-Requested-With",
			"X-Correlation-ID",
		},
		ExposedHeaders: []string{
			"X-Request-ID",
			"X-RateLimit-Remaining",
		},
		AllowCredentials: false, // HIPAA: Don't send credentials cross-origin
		MaxAge:           86400, // 24 hours
	}
}

// getAllowedOrigins reads allowed origins from environment
func getAllowedOrigins() []string {
	originsEnv := os.Getenv("CORS_ALLOWED_ORIGINS")
	if originsEnv == "" {
		// Default: localhost only for development
		return []string{
			"http://localhost:3000",
			"http://localhost:8080",
		}
	}

	origins := strings.Split(originsEnv, ",")
	for i := range origins {
		origins[i] = strings.TrimSpace(origins[i])
	}
	return origins
}

// isOriginAllowed checks if origin is in allowed list
func (c *CORSConfig) isOriginAllowed(origin string) bool {
	for _, allowed := range c.AllowedOrigins {
		if allowed == "*" || allowed == origin {
			return true
		}
	}
	return false
}

// CORSMiddleware adds CORS headers to responses
func CORSMiddleware(config *CORSConfig) func(http.Handler) http.Handler {
	if config == nil {
		config = DefaultCORSConfig()
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			origin := r.Header.Get("Origin")

			// Check if origin is allowed
			if origin != "" && config.isOriginAllowed(origin) {
				w.Header().Set("Access-Control-Allow-Origin", origin)
			}

			// Set other CORS headers
			w.Header().Set("Access-Control-Allow-Methods", strings.Join(config.AllowedMethods, ", "))
			w.Header().Set("Access-Control-Allow-Headers", strings.Join(config.AllowedHeaders, ", "))

			if len(config.ExposedHeaders) > 0 {
				w.Header().Set("Access-Control-Expose-Headers", strings.Join(config.ExposedHeaders, ", "))
			}

			if config.AllowCredentials {
				w.Header().Set("Access-Control-Allow-Credentials", "true")
			}

			if config.MaxAge > 0 {
				w.Header().Set("Access-Control-Max-Age", string(rune(config.MaxAge)))
			}

			// Handle preflight requests
			if r.Method == http.MethodOptions {
				w.WriteHeader(http.StatusOK)
				return
			}

			// Call next handler
			next.ServeHTTP(w, r)
		})
	}
}

// StrictCORSMiddleware only allows specific origins (production mode)
func StrictCORSMiddleware(allowedOrigins []string) func(http.Handler) http.Handler {
	config := &CORSConfig{
		AllowedOrigins:   allowedOrigins,
		AllowedMethods:   []string{http.MethodGet, http.MethodPost, http.MethodOptions},
		AllowedHeaders:   []string{"Authorization", "Content-Type"},
		AllowCredentials: false,
		MaxAge:           3600, // 1 hour
	}

	return CORSMiddleware(config)
}
