package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"
)

// Simple auth service placeholder demonstrating future critical domain expansion.
// WHY: Supports GitOps 2.0 multi-domain risk scoring (auth + payment + PHI).
// Provides health and token introspection endpoints.

type AuthHandler struct{}

func (h AuthHandler) Health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func (h AuthHandler) Introspect(w http.ResponseWriter, r *http.Request) {
	// Placeholder payload; would validate token & scopes.
	_ = json.NewEncoder(w).Encode(map[string]any{
		"active": true,
		"scopes": []string{"payment:write", "phi:read"},
		"exp":    time.Now().Add(15 * time.Minute).Unix(),
	})
}

// StartAuthServer constructs an HTTP server with routes for health and introspection.
// WHY: Improves testability and allows coverage of server wiring.
func StartAuthServer(addr string) *http.Server {
	mux := http.NewServeMux()
	h := AuthHandler{}
	mux.HandleFunc("/health", h.Health)
	mux.HandleFunc("/introspect", h.Introspect)

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
	srv := StartAuthServer(":8090")
	if err := srv.ListenAndServe(); err != nil {
		log.Fatalf("auth-service failed: %v", err)
	}
}
