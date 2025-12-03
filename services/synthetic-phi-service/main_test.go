package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// TestGeneratePatientHandler_GET tests single patient generation
func TestGeneratePatientHandler_GET(t *testing.T) {
	req := httptest.NewRequest("GET", "/synthetic-patient", nil)
	w := httptest.NewRecorder()

	GeneratePatientHandler(w, req)

	resp := w.Result()
	defer resp.Body.Close()

	// Check status code
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status OK, got %v", resp.StatusCode)
	}

	// Check compliance headers
	if resp.Header.Get("X-PHI-Protected") != "true" {
		t.Error("Expected X-PHI-Protected header to be 'true'")
	}

	if resp.Header.Get("X-Audit-Trail") != "enabled" {
		t.Error("Expected X-Audit-Trail header to be 'enabled'")
	}

	// Parse response
	var patient SyntheticPatient
	if err := json.NewDecoder(resp.Body).Decode(&patient); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Validate patient data
	if patient.ID == "" {
		t.Error("Patient ID should not be empty")
	}

	if patient.FirstName == "" {
		t.Error("Patient first name should not be empty")
	}

	if patient.LastName == "" {
		t.Error("Patient last name should not be empty")
	}

	if patient.MRN == "" {
		t.Error("Patient MRN should not be empty")
	}

	if !patient.Encrypted {
		t.Error("Patient data should be marked as encrypted")
	}

	if len(patient.PHITags) == 0 {
		t.Error("Patient should have PHI tags")
	}

	if len(patient.Diagnosis) == 0 {
		t.Error("Patient should have at least one diagnosis")
	}
}

// TestGeneratePatientHandler_POST tests batch patient generation
func TestGeneratePatientHandler_POST(t *testing.T) {
	reqBody := bytes.NewBufferString(`{"count": 5}`)
	req := httptest.NewRequest("POST", "/synthetic-patient", reqBody)
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	GeneratePatientHandler(w, req)

	resp := w.Result()
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status OK, got %v", resp.StatusCode)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Check count
	count, ok := result["count"].(float64)
	if !ok {
		t.Fatal("Count field missing or wrong type")
	}

	if int(count) != 5 {
		t.Errorf("Expected 5 patients, got %d", int(count))
	}

	// Check patients array
	patients, ok := result["patients"].([]interface{})
	if !ok {
		t.Fatal("Patients field missing or wrong type")
	}

	if len(patients) != 5 {
		t.Errorf("Expected 5 patients in array, got %d", len(patients))
	}

	// Check metadata
	metadata, ok := result["metadata"].(map[string]interface{})
	if !ok {
		t.Fatal("Metadata field missing or wrong type")
	}

	if metadata["compliance"] != "HIPAA_SYNTHETIC" {
		t.Error("Expected HIPAA_SYNTHETIC compliance marker")
	}

	if metadata["phi_safe"] != "true" {
		t.Error("Expected phi_safe to be true")
	}
}

// TestGeneratePatientHandler_POST_InvalidCount tests validation
func TestGeneratePatientHandler_POST_InvalidCount(t *testing.T) {
	testCases := []struct {
		name       string
		count      string
		expectCode int
	}{
		{"Zero count", `{"count": 0}`, http.StatusBadRequest},
		{"Negative count", `{"count": -5}`, http.StatusBadRequest},
		{"Too many", `{"count": 101}`, http.StatusBadRequest},
		{"Invalid JSON", `{"count": "abc"}`, http.StatusBadRequest},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			reqBody := bytes.NewBufferString(tc.count)
			req := httptest.NewRequest("POST", "/synthetic-patient", reqBody)
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			GeneratePatientHandler(w, req)

			resp := w.Result()
			defer resp.Body.Close()

			if resp.StatusCode != tc.expectCode {
				t.Errorf("Expected status %d, got %d", tc.expectCode, resp.StatusCode)
			}
		})
	}
}

// TestGeneratePatientHandler_MethodNotAllowed tests unsupported HTTP methods
func TestGeneratePatientHandler_MethodNotAllowed(t *testing.T) {
	methods := []string{"PUT", "DELETE", "PATCH"}

	for _, method := range methods {
		t.Run(method, func(t *testing.T) {
			req := httptest.NewRequest(method, "/synthetic-patient", nil)
			w := httptest.NewRecorder()

			GeneratePatientHandler(w, req)

			resp := w.Result()
			defer resp.Body.Close()

			if resp.StatusCode != http.StatusMethodNotAllowed {
				t.Errorf("Expected status MethodNotAllowed for %s, got %d", method, resp.StatusCode)
			}
		})
	}
}

// TestHealthHandler tests the health check endpoint
func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	HealthHandler(w, req)

	resp := w.Result()
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status OK, got %v", resp.StatusCode)
	}

	var health map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if health["status"] != "healthy" {
		t.Error("Expected status to be 'healthy'")
	}

	if health["service"] != "synthetic-phi-service" {
		t.Error("Expected service name to be 'synthetic-phi-service'")
	}

	compliance, ok := health["compliance"].([]interface{})
	if !ok {
		t.Fatal("Compliance field missing or wrong type")
	}

	if len(compliance) < 1 {
		t.Error("Expected at least one compliance framework")
	}
}

// TestComplianceHandler tests the compliance status endpoint
func TestComplianceHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/compliance/status", nil)
	w := httptest.NewRecorder()

	ComplianceHandler(w, req)

	resp := w.Result()
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status OK, got %v", resp.StatusCode)
	}

	var compliance map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&compliance); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Verify compliance fields
	requiredFields := []string{
		"hipaa_compliant",
		"phi_data_synthetic",
		"real_phi_exposure",
		"encryption_enabled",
		"audit_trail_active",
		"privacy_by_design",
		"data_minimization",
	}

	for _, field := range requiredFields {
		if _, ok := compliance[field]; !ok {
			t.Errorf("Missing compliance field: %s", field)
		}
	}

	// Verify boolean values
	if compliance["hipaa_compliant"] != true {
		t.Error("Expected hipaa_compliant to be true")
	}

	if compliance["phi_data_synthetic"] != true {
		t.Error("Expected phi_data_synthetic to be true")
	}

	if compliance["real_phi_exposure"] != false {
		t.Error("Expected real_phi_exposure to be false")
	}

	if compliance["purpose_limitation"] != "testing_only" {
		t.Error("Expected purpose_limitation to be 'testing_only'")
	}
}

// TestSyntheticDataGenerator tests the data generator
func TestSyntheticDataGenerator(t *testing.T) {
	generator := NewSyntheticDataGenerator()

	// Test patient generation
	patient, err := generator.GeneratePatient()
	if err != nil {
		t.Fatalf("Failed to generate patient: %v", err)
	}

	// Validate generated data
	if patient == nil {
		t.Fatal("Generated patient should not be nil")
	}

	// Check ID format
	if len(patient.ID) < 9 {
		t.Error("Patient ID should be at least 9 characters (PAT + 6 digits)")
	}

	if patient.ID[:3] != "PAT" {
		t.Error("Patient ID should start with 'PAT'")
	}

	// Check MRN format
	if len(patient.MRN) < 9 {
		t.Error("MRN should be at least 9 characters (MRN + 6 digits)")
	}

	if patient.MRN[:3] != "MRN" {
		t.Error("MRN should start with 'MRN'")
	}

	// Check first name is from safe list
	validFirstNames := map[string]bool{
		"Alex": true, "Jordan": true, "Casey": true, "Taylor": true,
		"Morgan": true, "Riley": true, "Avery": true, "Quinn": true,
	}

	if !validFirstNames[patient.FirstName] {
		t.Errorf("First name %s not in safe list", patient.FirstName)
	}

	// Check last name is from safe list
	validLastNames := map[string]bool{
		"Smith": true, "Johnson": true, "Williams": true, "Brown": true,
		"Jones": true, "Garcia": true, "Miller": true, "Davis": true,
	}

	if !validLastNames[patient.LastName] {
		t.Errorf("Last name %s not in safe list", patient.LastName)
	}

	// Check diagnosis count
	if len(patient.Diagnosis) < 1 || len(patient.Diagnosis) > 3 {
		t.Errorf("Diagnosis count should be 1-3, got %d", len(patient.Diagnosis))
	}

	// Check encryption flag
	if !patient.Encrypted {
		t.Error("Patient data should be marked as encrypted")
	}

	// Check PHI tags
	if len(patient.PHITags) == 0 {
		t.Error("Patient should have PHI tags")
	}
}

// TestSyntheticDataGenerator_Uniqueness tests that generated data is unique
func TestSyntheticDataGenerator_Uniqueness(t *testing.T) {
	generator := NewSyntheticDataGenerator()

	// Generate multiple patients
	patients := make([]*SyntheticPatient, 100)
	ids := make(map[string]bool)
	mrns := make(map[string]bool)

	for i := 0; i < 100; i++ {
		patient, err := generator.GeneratePatient()
		if err != nil {
			t.Fatalf("Failed to generate patient %d: %v", i, err)
		}

		// Check ID uniqueness
		if ids[patient.ID] {
			t.Errorf("Duplicate ID found: %s", patient.ID)
		}
		ids[patient.ID] = true

		// Check MRN uniqueness
		if mrns[patient.MRN] {
			t.Errorf("Duplicate MRN found: %s", patient.MRN)
		}
		mrns[patient.MRN] = true

		patients[i] = patient
	}

	// Verify we generated 100 unique IDs and MRNs
	if len(ids) != 100 {
		t.Errorf("Expected 100 unique IDs, got %d", len(ids))
	}

	if len(mrns) != 100 {
		t.Errorf("Expected 100 unique MRNs, got %d", len(mrns))
	}
}

// BenchmarkGeneratePatient benchmarks patient generation
func BenchmarkGeneratePatient(b *testing.B) {
	generator := NewSyntheticDataGenerator()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := generator.GeneratePatient()
		if err != nil {
			b.Fatal(err)
		}
	}
}

// BenchmarkGeneratePatientHandler_GET benchmarks the HTTP handler
func BenchmarkGeneratePatientHandler_GET(b *testing.B) {
	req := httptest.NewRequest("GET", "/synthetic-patient", nil)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		w := httptest.NewRecorder()
		GeneratePatientHandler(w, req)
	}
}

// TestHealthcareComplianceHeaders tests that all endpoints have proper headers
func TestHealthcareComplianceHeaders(t *testing.T) {
	testCases := []struct {
		name    string
		handler http.HandlerFunc
		path    string
	}{
		{"Patient generation", GeneratePatientHandler, "/synthetic-patient"},
		{"Health check", HealthHandler, "/health"},
		{"Compliance status", ComplianceHandler, "/compliance/status"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", tc.path, nil)
			w := httptest.NewRecorder()

			tc.handler(w, req)

			resp := w.Result()
			defer resp.Body.Close()

			// Check required compliance headers
			requiredHeaders := map[string]string{
				"X-PHI-Protected":        "true",
				"X-Audit-Trail":          "enabled",
				"X-Encryption-Status":    "AES-256",
				"X-SOX-Compliant":        "true",
				"X-Content-Type-Options": "nosniff",
				"X-Frame-Options":        "DENY",
				"Content-Type":           "application/json",
			}

			for header, expected := range requiredHeaders {
				actual := resp.Header.Get(header)
				if actual != expected {
					t.Errorf("Expected %s header to be '%s', got '%s'", header, expected, actual)
				}
			}

			// Check request ID exists
			requestID := resp.Header.Get("X-Request-ID")
			if requestID == "" {
				t.Error("Expected X-Request-ID header to be present")
			}

			if requestID[:4] != "REQ_" {
				t.Error("Expected X-Request-ID to start with 'REQ_'")
			}
		})
	}
}
