package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"
)

// TestEndToEndPaymentWorkflow tests the complete payment processing workflow
func TestEndToEndPaymentWorkflow(t *testing.T) {
	// Setup test environment
	os.Setenv("PORT", "8081")
	os.Setenv("SERVICE_NAME", "test-payment-gateway")
	os.Setenv("MAX_PROCESSING_MILLIS", "100")
	defer func() {
		os.Unsetenv("PORT")
		os.Unsetenv("SERVICE_NAME")
		os.Unsetenv("MAX_PROCESSING_MILLIS")
	}()

	// Load configuration
	config := LoadConfig()

	// Create server with handlers
	handler := PaymentHandler{MaxLatency: processingTimeout(config.MaxProcessingMillis)}

	// Test health endpoint
	t.Run("HealthCheck", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/health", nil)
		req.Header.Set("User-Agent", "HealthcareComplianceTest/1.0")
		w := httptest.NewRecorder()

		handler.Health(w, req)

		if w.Code != http.StatusOK {
			t.Errorf("Health check failed: expected %d, got %d", http.StatusOK, w.Code)
		}

		// Verify healthcare compliance headers
		if w.Header().Get("X-Content-Type-Options") != "nosniff" {
			t.Error("Missing HIPAA compliance security header: X-Content-Type-Options")
		}

		if w.Header().Get("Strict-Transport-Security") == "" {
			t.Error("Missing security header: Strict-Transport-Security")
		}
	})

	// Test payment processing with compliance validation
	t.Run("PaymentProcessingCompliance", func(t *testing.T) {
		// Test valid payment request
		payment := PaymentRequest{
			Amount:      100.50,
			Currency:    "USD",
			CustomerID:  "CUST-456",
			Method:      "card",
			PatientID:   "PATIENT-123",
			Description: "Medical consultation fee",
		}

		body, _ := json.Marshal(payment)
		req := httptest.NewRequest("POST", "/charge", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("User-Agent", "HealthcareComplianceTest/1.0")

		w := httptest.NewRecorder()
		handler.ProcessPayment(w, req)

		if w.Code != http.StatusOK {
			t.Errorf("Payment processing failed: expected %d, got %d", http.StatusOK, w.Code)
		}

		// Verify HIPAA compliance in response
		var response PaymentResponse
		if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
			t.Fatalf("Failed to parse response: %v", err)
		}

		// Validate audit trail for HIPAA compliance
		if response.TransactionID == "" {
			t.Error("Missing transaction ID for audit trail")
		}

		if response.Status != "success" {
			t.Error("Payment processing should succeed for valid request")
		}

		// Verify SOX compliance headers are present
		auditHeader := w.Header().Get("X-Audit-Transaction-ID")
		if auditHeader == "" {
			t.Error("Missing SOX compliance audit header")
		}
	})

	// Test PHI protection and validation
	t.Run("PHIProtection", func(t *testing.T) {
		// Test with potentially sensitive PHI data
		payment := PaymentRequest{
			Amount:      250.00,
			Currency:    "USD",
			CustomerID:  "CUST-789",
			Method:      "card",
			PatientID:   "SSN-123-45-6789", // Simulated sensitive data
			Description: "Cardiac procedure - John Doe DOB:01/01/1990",
		}

		body, _ := json.Marshal(payment)
		req := httptest.NewRequest("POST", "/charge", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("User-Agent", "HealthcareComplianceTest/1.0")

		w := httptest.NewRecorder()
		handler.ProcessPayment(w, req)

		// Should still process but with enhanced security logging
		if w.Code != http.StatusOK {
			t.Errorf("PHI payment processing failed: expected %d, got %d", http.StatusOK, w.Code)
		}

		// Verify PHI protection headers
		phiProtectionHeader := w.Header().Get("X-PHI-Protected")
		if phiProtectionHeader != "true" {
			t.Error("PHI protection header should be set for healthcare transactions")
		}
	})

	// Test FDA medical device compliance
	t.Run("FDAComplianceValidation", func(t *testing.T) {
		// Simulate medical device payment processing
		payment := PaymentRequest{
			Amount:      1500.00,
			Currency:    "USD",
			CustomerID:  "CUST-FDA-123",
			Method:      "card",
			PatientID:   "DEVICE-PATIENT-456",
			Description: "FDA Class II Medical Device - Cardiac Monitor",
			DeviceID:    "FDA-510K-DEV-789",
		}

		body, _ := json.Marshal(payment)
		req := httptest.NewRequest("POST", "/charge", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("User-Agent", "HealthcareComplianceTest/1.0")
		req.Header.Set("X-Medical-Device", "true")

		w := httptest.NewRecorder()
		handler.ProcessPayment(w, req)

		if w.Code != http.StatusOK {
			t.Errorf("FDA device payment failed: expected %d, got %d", http.StatusOK, w.Code)
		}

		// Verify FDA compliance tracking
		fdaHeader := w.Header().Get("X-FDA-Validated")
		if fdaHeader != "true" {
			t.Error("FDA validation header should be set for medical device transactions")
		}
	})
}

// TestSecurityCompliance validates security implementation
func TestSecurityCompliance(t *testing.T) {
	handler := PaymentHandler{MaxLatency: 200 * time.Millisecond}

	t.Run("SecurityHeaders", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/health", nil)
		req.Header.Set("User-Agent", "HealthcareComplianceTest/1.0")
		w := httptest.NewRecorder()

		handler.Health(w, req)

		securityHeaders := map[string]string{
			"X-Content-Type-Options":    "nosniff",
			"X-Frame-Options":           "DENY",
			"X-XSS-Protection":          "1; mode=block",
			"Strict-Transport-Security": "max-age=31536000; includeSubDomains",
			"Referrer-Policy":           "strict-origin-when-cross-origin",
			"Content-Security-Policy":   "default-src 'self'",
		}

		for header, expectedValue := range securityHeaders {
			actualValue := w.Header().Get(header)
			if actualValue != expectedValue {
				t.Errorf("Security header %s: expected '%s', got '%s'",
					header, expectedValue, actualValue)
			}
		}
	})

	t.Run("RequestSizeLimit", func(t *testing.T) {
		// Create oversized request (> 1MB)
		oversizedData := make([]byte, 2*1024*1024) // 2MB
		req := httptest.NewRequest("POST", "/charge", bytes.NewReader(oversizedData))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("User-Agent", "HealthcareComplianceTest/1.0")
		w := httptest.NewRecorder()

		handler.ProcessPayment(w, req)

		if w.Code != http.StatusRequestEntityTooLarge {
			t.Errorf("Oversized request should be rejected: expected %d, got %d",
				http.StatusRequestEntityTooLarge, w.Code)
		}
	})
}

// TestPerformanceCompliance validates latency requirements
func TestPerformanceCompliance(t *testing.T) {
	handler := PaymentHandler{MaxLatency: 100 * time.Millisecond}

	t.Run("LatencyCompliance", func(t *testing.T) {
		payment := PaymentRequest{
			Amount:     100.00,
			Currency:   "USD",
			CustomerID: "CUST-PERF-123",
			Method:     "card",
			PatientID:  "PERF-TEST-123",
		}

		body, _ := json.Marshal(payment)
		req := httptest.NewRequest("POST", "/charge", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("User-Agent", "HealthcareComplianceTest/1.0")

		start := time.Now()
		w := httptest.NewRecorder()
		handler.ProcessPayment(w, req)
		duration := time.Since(start)

		if duration > 200*time.Millisecond {
			t.Errorf("Request took too long: %v (should be < 200ms)", duration)
		}

		if w.Code != http.StatusOK {
			t.Errorf("Performance test failed: expected %d, got %d", http.StatusOK, w.Code)
		}
	})
}

// TestAuditTrailCompliance validates SOX compliance
func TestAuditTrailCompliance(t *testing.T) {
	handler := PaymentHandler{MaxLatency: 200 * time.Millisecond}

	t.Run("SOXAuditTrail", func(t *testing.T) {
		payment := PaymentRequest{
			Amount:      500.00,
			Currency:    "USD",
			CustomerID:  "CUST-AUDIT-789",
			Method:      "card",
			PatientID:   "AUDIT-TEST-789",
			Description: "SOX compliance test transaction",
		}

		body, _ := json.Marshal(payment)
		req := httptest.NewRequest("POST", "/charge", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("User-Agent", "HealthcareComplianceTest/1.0")

		w := httptest.NewRecorder()
		handler.ProcessPayment(w, req)

		// Verify audit trail headers
		auditHeaders := []string{
			"X-Audit-Transaction-ID",
			"X-Audit-Timestamp",
			"X-SOX-Compliance",
		}

		for _, header := range auditHeaders {
			if w.Header().Get(header) == "" {
				t.Errorf("Missing SOX audit header: %s", header)
			}
		}

		// Verify response contains audit information
		var response PaymentResponse
		json.Unmarshal(w.Body.Bytes(), &response)

		if response.AuditID == "" {
			t.Error("Missing audit ID in response for SOX compliance")
		}
	})
}
