package main

// Diagnostic utilities for medical device service
// This file provides diagnostic and health check functions

import (
	"encoding/json"
	"net/http"
)

// DiagnosticInfo represents diagnostic information about the service
type DiagnosticInfo struct {
	Status      string `json:"status"`
	ServiceName string `json:"service_name"`
	Version     string `json:"version"`
}

// HealthCheckHandler handles health check requests
func HealthCheckHandler(w http.ResponseWriter, r *http.Request) {
	info := DiagnosticInfo{
		Status:      "healthy",
		ServiceName: "medical-device",
		Version:     "1.0.0",
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(info)
}
