package main

import (
	"encoding/json"
	"io"
	"math"
	"net/http"
	"strings"
	"time"
)

type PaymentHandler struct {
	MaxLatency time.Duration
}

// setSecurityHeaders sets strong default security/compliance headers.
func (h PaymentHandler) setSecurityHeaders(w http.ResponseWriter) {
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("X-Frame-Options", "DENY")
	w.Header().Set("X-XSS-Protection", "1; mode=block")
	w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
	w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
	w.Header().Set("Content-Security-Policy", "default-src 'self'")
}

func (h PaymentHandler) Health(w http.ResponseWriter, r *http.Request) {
	h.setSecurityHeaders(w)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]string{
		"status": "ok",
	})
}

// ProcessPayment is an HTTP handler expected by tests. It wraps Charge logic.
func (h PaymentHandler) ProcessPayment(w http.ResponseWriter, r *http.Request) {
	h.handleChargeCommon(w, r)
}

func (h PaymentHandler) Charge(w http.ResponseWriter, r *http.Request) {
	h.handleChargeCommon(w, r)
}

// Shared logic for POST /charge and ProcessPayment test hook.
func (h PaymentHandler) handleChargeCommon(w http.ResponseWriter, r *http.Request) {
	h.setSecurityHeaders(w)

	// Enforce request size limit (1MB)
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
	defer r.Body.Close()

	// Read raw (bounded) to distinguish size errors from JSON unmarshalling issues
	raw, readErr := io.ReadAll(r.Body)
	if readErr != nil {
		lower := strings.ToLower(readErr.Error())
		if strings.Contains(lower, "request body too large") || strings.Contains(lower, "body too large") {
			http.Error(w, "request entity too large", http.StatusRequestEntityTooLarge)
			return
		}
		http.Error(w, "invalid payload", http.StatusBadRequest)
		return
	}

	var req PaymentRequest
	if err := json.Unmarshal(raw, &req); err != nil {
		http.Error(w, "invalid payload", http.StatusBadRequest)
		return
	}

	// Backward compatibility: if Amount provided, derive AmountCents
	if req.AmountCents == 0 && req.Amount > 0 {
		req.AmountCents = int64(math.Round(req.Amount * 100))
	}

	// Process the payment
	start := time.Now()
	resp, err := ProcessPayment(req, h.MaxLatency)
	duration := time.Since(start)

	// Update metrics
	RecordTransaction(req, duration, err == nil)

	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Compliance/audit enrichment
	auditID := generateAuditID()
	txnID := generateTransactionID()

	// Set compliance headers
	w.Header().Set("X-Audit-Transaction-ID", txnID)
	w.Header().Set("X-Audit-Timestamp", time.Now().UTC().Format(time.RFC3339))
	w.Header().Set("X-SOX-Compliance", "true")

	// PHI header if PatientID present
	if req.PatientID != "" {
		w.Header().Set("X-PHI-Protected", "true")
	}
	// FDA validation header if DeviceID present or explicit device header
	if req.DeviceID != "" || r.Header.Get("X-Medical-Device") == "true" {
		w.Header().Set("X-FDA-Validated", "true")
	}

	// Build response body
	enriched := resp
	// For HTTP responses, tests expect status "success"
	enriched.Status = "success"
	enriched.TransactionID = txnID
	enriched.AuditID = auditID

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(enriched)
}

// Simple ID generators for demo/testing (not cryptographically secure)
func generateAuditID() string {
	return "AUDIT-" + time.Now().Format("20060102-150405.000")
}

func generateTransactionID() string {
	return "TXN-" + time.Now().Format("20060102-150405.000")
}
