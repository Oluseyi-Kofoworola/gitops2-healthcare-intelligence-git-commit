package main

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestProcessPayment_Success(t *testing.T) {
	req := PaymentRequest{
		AmountCents: 1000,
		Currency:    "USD",
		CustomerID:  "cust-123",
		Method:      "card",
	}

	resp, err := ProcessPayment(req, 200*time.Millisecond)
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}

	if resp.Status != "authorized" {
		t.Fatalf("expected status authorized, got %s", resp.Status)
	}
	if resp.AuthCode == "" {
		t.Fatalf("expected auth code to be set")
	}
}

func TestProcessPayment_InvalidAmount(t *testing.T) {
	req := PaymentRequest{
		AmountCents: 0,
		Currency:    "USD",
		CustomerID:  "cust-123",
		Method:      "card",
	}

	_, err := ProcessPayment(req, 200*time.Millisecond)
	if err == nil {
		t.Fatalf("expected error for invalid amount")
	}
}

func TestProcessPayment_InvalidJSON(t *testing.T) {
	h := PaymentHandler{MaxLatency: 50 * time.Millisecond}
	req := httptest.NewRequest(http.MethodPost, "/charge", bytes.NewBufferString("{not-json}"))
	req.Header.Set("Content-Type", "application/json")
	rr := httptest.NewRecorder()

	h.ProcessPayment(rr, req)

	if rr.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 for invalid JSON, got %d", rr.Code)
	}
}

func TestMetricsAndComplianceEndpoints(t *testing.T) {
	h := PaymentHandler{MaxLatency: 10 * time.Millisecond}

	// Hit metrics endpoint
	t.Run("metrics", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/metrics", nil)
		rr := httptest.NewRecorder()
		h.MetricsHandler(rr, req)
		if rr.Code != http.StatusOK {
			t.Fatalf("metrics expected 200, got %d", rr.Code)
		}
		if ct := rr.Header().Get("Content-Type"); ct != "application/json" {
			t.Fatalf("expected application/json, got %s", ct)
		}
	})

	// Compliance status
	t.Run("compliance", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/compliance/status", nil)
		rr := httptest.NewRecorder()
		h.ComplianceStatusHandler(rr, req)
		if rr.Code != http.StatusOK {
			t.Fatalf("compliance expected 200, got %d", rr.Code)
		}
	})

	// Audit trail
	t.Run("audit", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/audit/trail", nil)
		rr := httptest.NewRecorder()
		h.AuditTrailHandler(rr, req)
		if rr.Code != http.StatusOK {
			t.Fatalf("audit expected 200, got %d", rr.Code)
		}
	})

	// Alerts
	t.Run("alerts", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/alerts", nil)
		rr := httptest.NewRecorder()
		h.AlertingHandler(rr, req)
		if rr.Code != http.StatusOK {
			t.Fatalf("alerts expected 200, got %d", rr.Code)
		}
	})
}

func TestRecordTransactionAndHelpers(t *testing.T) {
	// Reset a fresh metrics struct for isolation
	healthcareMetrics = &HealthcareMetrics{
		ComplianceStatus: map[string]bool{"HIPAA": true, "FDA": true, "SOX": true},
		ErrorRates:       make(map[string]float64),
	}

	// Record a standard transaction
	RecordTransaction(PaymentRequest{AmountCents: 1000, Currency: "USD", CustomerID: "c1", Method: "card"}, 20*time.Millisecond, true)
	// Record a HIPAA + FDA with failure
	RecordTransaction(PaymentRequest{AmountCents: 2000, Currency: "USD", CustomerID: "c2", Method: "card", PatientID: "p1", DeviceID: "d1"}, 40*time.Millisecond, false)

	if healthcareMetrics.TotalTransactions != 2 {
		t.Fatalf("expected 2 total transactions, got %d", healthcareMetrics.TotalTransactions)
	}
	if healthcareMetrics.HIPAATransactions != 1 || healthcareMetrics.FDATransactions != 1 || healthcareMetrics.SOXTransactions != 2 {
		t.Fatalf("unexpected domain counters: hipaa=%d fda=%d sox=%d", healthcareMetrics.HIPAATransactions, healthcareMetrics.FDATransactions, healthcareMetrics.SOXTransactions)
	}

	// AverageLatency should be > 0
	if healthcareMetrics.AverageLatency <= 0 {
		t.Fatalf("expected average latency to be computed")
	}

	// Update system metrics to exercise calculateRPS/Throughput paths
	updateSystemMetrics()
	if healthcareMetrics.PerformanceMetrics.RequestsPerSecond <= 0 {
		t.Fatalf("expected RPS > 0")
	}
	if healthcareMetrics.PerformanceMetrics.ThroughputMBps <= 0 {
		t.Fatalf("expected throughput > 0")
	}
}

func TestServerRoutes(t *testing.T) {
	cfg := Config{Port: "0", ServiceName: "payment-gateway", MaxProcessingMillis: 50}
	srv := NewServer(cfg)

	// exercise a few routes with the server's handler
	h := srv.Handler

	// health
	rr := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	h.ServeHTTP(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("health expected 200, got %d", rr.Code)
	}

	// metrics
	rr = httptest.NewRecorder()
	req = httptest.NewRequest(http.MethodGet, "/metrics", nil)
	h.ServeHTTP(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("metrics expected 200, got %d", rr.Code)
	}
}
