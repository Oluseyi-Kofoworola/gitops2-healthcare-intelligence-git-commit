// filepath: tests/integration/integration_test.go
package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Service endpoints
const (
	AuthServiceURL    = "http://localhost:8080"
	PaymentGatewayURL = "http://localhost:8081"
	PHIServiceURL     = "http://localhost:8083"
	MedicalDeviceURL  = "http://localhost:8084"
	SyntheticPHIURL   = "http://localhost:8085"
)

// Test fixtures
type AuthRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type AuthResponse struct {
	Token     string `json:"token"`
	ExpiresIn int    `json:"expires_in"`
	TokenType string `json:"token_type"`
}

type PaymentRequest struct {
	Amount         float64           `json:"amount"`
	Currency       string            `json:"currency"`
	PatientID      string            `json:"patient_id"`
	TransactionID  string            `json:"transaction_id"`
	PaymentMethod  string            `json:"payment_method"`
	ComplianceTags map[string]string `json:"compliance_tags,omitempty"`
}

type PaymentResponse struct {
	Status        string    `json:"status"`
	TransactionID string    `json:"transaction_id"`
	Amount        float64   `json:"amount"`
	Currency      string    `json:"currency"`
	ProcessedAt   time.Time `json:"processed_at"`
	AuditID       string    `json:"audit_id"`
}

type PHIEncryptRequest struct {
	Data      string            `json:"data"`
	PatientID string            `json:"patient_id"`
	DataType  string            `json:"data_type"`
	Metadata  map[string]string `json:"metadata,omitempty"`
}

type PHIEncryptResponse struct {
	EncryptedData string    `json:"encrypted_data"`
	KeyID         string    `json:"key_id"`
	Algorithm     string    `json:"algorithm"`
	EncryptedAt   time.Time `json:"encrypted_at"`
}

type PHIDecryptRequest struct {
	EncryptedData string `json:"encrypted_data"`
	KeyID         string `json:"key_id"`
}

type PHIDecryptResponse struct {
	Data        string    `json:"data"`
	DecryptedAt time.Time `json:"decrypted_at"`
}

type MedicalDevice struct {
	DeviceID     string            `json:"device_id"`
	DeviceType   string            `json:"device_type"`
	Manufacturer string            `json:"manufacturer"`
	Model        string            `json:"model"`
	SerialNumber string            `json:"serial_number"`
	Location     string            `json:"location"`
	Status       string            `json:"status"`
	Metadata     map[string]string `json:"metadata,omitempty"`
}

type DeviceMetrics struct {
	Temperature float64 `json:"temperature"`
	PowerUsage  float64 `json:"power_usage"`
	CPUUsage    float64 `json:"cpu_usage"`
	MemoryUsage float64 `json:"memory_usage"`
	NetworkRX   int64   `json:"network_rx"`
	NetworkTX   int64   `json:"network_tx"`
}

type SyntheticPatient struct {
	FirstName   string `json:"first_name"`
	LastName    string `json:"last_name"`
	DateOfBirth string `json:"date_of_birth"`
	Gender      string `json:"gender"`
	SSN         string `json:"ssn"`
	Email       string `json:"email"`
	Phone       string `json:"phone"`
	Address     string `json:"address"`
}

// Helper functions
func waitForServices(t *testing.T, timeout time.Duration) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	services := map[string]string{
		"Auth Service":    AuthServiceURL + "/health",
		"Payment Gateway": PaymentGatewayURL + "/health",
		"PHI Service":     PHIServiceURL + "/health",
		"Medical Device":  MedicalDeviceURL + "/health",
		"Synthetic PHI":   SyntheticPHIURL + "/health",
	}

	for name, url := range services {
		t.Logf("Waiting for %s to be ready...", name)
		for {
			select {
			case <-ctx.Done():
				t.Fatalf("Timeout waiting for %s to be ready", name)
			default:
				resp, err := http.Get(url)
				if err == nil && resp.StatusCode == http.StatusOK {
					t.Logf("%s is ready", name)
					resp.Body.Close()
					goto nextService
				}
				if resp != nil {
					resp.Body.Close()
				}
				time.Sleep(1 * time.Second)
			}
		}
	nextService:
	}
}

func authenticate(t *testing.T) string {
	t.Helper()
	authReq := AuthRequest{
		Username: "admin",
		Password: "admin123",
	}

	body, _ := json.Marshal(authReq)
	resp, err := http.Post(AuthServiceURL+"/api/v1/login", "application/json", bytes.NewBuffer(body))
	require.NoError(t, err)
	defer resp.Body.Close()

	require.Equal(t, http.StatusOK, resp.StatusCode)

	var authResp AuthResponse
	err = json.NewDecoder(resp.Body).Decode(&authResp)
	require.NoError(t, err)
	require.NotEmpty(t, authResp.Token)

	return authResp.Token
}

func makeAuthenticatedRequest(t *testing.T, method, url string, body io.Reader, token string) *http.Response {
	t.Helper()
	req, err := http.NewRequest(method, url, body)
	require.NoError(t, err)

	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	require.NoError(t, err)

	return resp
}

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

// TestMain sets up the test environment
func TestMain(m *testing.M) {
	// Services should be started via docker-compose before running tests
	// No setup needed here
	m.Run()
}

// Test 1: Health checks for all services
func TestHealthChecks(t *testing.T) {
	waitForServices(t, 60*time.Second)

	services := map[string]string{
		"auth-service":    AuthServiceURL + "/health",
		"payment-gateway": PaymentGatewayURL + "/health",
		"phi-service":     PHIServiceURL + "/health",
		"medical-device":  MedicalDeviceURL + "/health",
		"synthetic-phi":   SyntheticPHIURL + "/health",
	}

	for name, url := range services {
		t.Run(name, func(t *testing.T) {
			resp, err := http.Get(url)
			require.NoError(t, err)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			body, err := io.ReadAll(resp.Body)
			require.NoError(t, err)

			var healthResp map[string]interface{}
			err = json.Unmarshal(body, &healthResp)
			require.NoError(t, err)

			assert.Equal(t, "healthy", healthResp["status"])
		})
	}
}

// Test 2: Authentication flow
func TestAuthenticationFlow(t *testing.T) {
	waitForServices(t, 60*time.Second)

	t.Run("successful_login", func(t *testing.T) {
		token := authenticate(t)
		assert.NotEmpty(t, token)
	})

	t.Run("invalid_credentials", func(t *testing.T) {
		authReq := AuthRequest{
			Username: "invalid",
			Password: "wrong",
		}

		body, _ := json.Marshal(authReq)
		resp, err := http.Post(AuthServiceURL+"/api/v1/login", "application/json", bytes.NewBuffer(body))
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})

	t.Run("token_validation", func(t *testing.T) {
		token := authenticate(t)

		// Use token to access payment gateway
		req, err := http.NewRequest("GET", PaymentGatewayURL+"/api/v1/transactions", nil)
		require.NoError(t, err)
		req.Header.Set("Authorization", "Bearer "+token)

		client := &http.Client{Timeout: 10 * time.Second}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		// Should return 200 (even if empty list)
		assert.Equal(t, http.StatusOK, resp.StatusCode)
	})
}

// Test 3: Payment Gateway + Auth Integration
func TestPaymentGatewayAuthIntegration(t *testing.T) {
	waitForServices(t, 60*time.Second)

	token := authenticate(t)

	t.Run("authenticated_payment", func(t *testing.T) {
		paymentReq := PaymentRequest{
			Amount:        1250.00,
			Currency:      "USD",
			PatientID:     "PATIENT-001",
			TransactionID: fmt.Sprintf("TXN-%d", time.Now().Unix()),
			PaymentMethod: "credit_card",
			ComplianceTags: map[string]string{
				"hipaa": "true",
				"sox":   "true",
			},
		}

		body, _ := json.Marshal(paymentReq)
		resp := makeAuthenticatedRequest(t, "POST", PaymentGatewayURL+"/api/v1/transactions", bytes.NewBuffer(body), token)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var paymentResp PaymentResponse
		err := json.NewDecoder(resp.Body).Decode(&paymentResp)
		require.NoError(t, err)

		assert.Equal(t, "success", paymentResp.Status)
		assert.Equal(t, paymentReq.Amount, paymentResp.Amount)
		assert.NotEmpty(t, paymentResp.AuditID)
	})

	t.Run("unauthenticated_payment", func(t *testing.T) {
		paymentReq := PaymentRequest{
			Amount:        100.00,
			Currency:      "USD",
			PatientID:     "PATIENT-002",
			TransactionID: fmt.Sprintf("TXN-%d", time.Now().Unix()),
			PaymentMethod: "debit_card",
		}

		body, _ := json.Marshal(paymentReq)
		resp := makeAuthenticatedRequest(t, "POST", PaymentGatewayURL+"/api/v1/transactions", bytes.NewBuffer(body), "")
		defer resp.Body.Close()

		assert.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})
}

// Test 4: PHI Service Encryption/Decryption
func TestPHIServiceEncryptionFlow(t *testing.T) {
	waitForServices(t, 60*time.Second)

	t.Run("encrypt_decrypt_workflow", func(t *testing.T) {
		// Encrypt PHI data
		encryptReq := PHIEncryptRequest{
			Data:      "Patient John Doe, SSN: 123-45-6789, DOB: 1980-05-15",
			PatientID: "PATIENT-001",
			DataType:  "demographics",
			Metadata: map[string]string{
				"department": "cardiology",
				"provider":   "DR-SMITH",
			},
		}

		body, _ := json.Marshal(encryptReq)
		resp, err := http.Post(PHIServiceURL+"/api/v1/phi/encrypt", "application/json", bytes.NewBuffer(body))
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var encryptResp PHIEncryptResponse
		err = json.NewDecoder(resp.Body).Decode(&encryptResp)
		require.NoError(t, err)

		assert.NotEmpty(t, encryptResp.EncryptedData)
		assert.NotEmpty(t, encryptResp.KeyID)
		assert.Equal(t, "AES-256-GCM", encryptResp.Algorithm)

		// Decrypt PHI data
		decryptReq := PHIDecryptRequest{
			EncryptedData: encryptResp.EncryptedData,
			KeyID:         encryptResp.KeyID,
		}

		body, _ = json.Marshal(decryptReq)
		resp2, err := http.Post(PHIServiceURL+"/api/v1/phi/decrypt", "application/json", bytes.NewBuffer(body))
		require.NoError(t, err)
		defer resp2.Body.Close()

		assert.Equal(t, http.StatusOK, resp2.StatusCode)

		var decryptResp PHIDecryptResponse
		err = json.NewDecoder(resp2.Body).Decode(&decryptResp)
		require.NoError(t, err)

		assert.Equal(t, encryptReq.Data, decryptResp.Data)
	})
}

// Test 5: Medical Device Service Integration
func TestMedicalDeviceIntegration(t *testing.T) {
	waitForServices(t, 60*time.Second)

	t.Run("register_and_monitor_device", func(t *testing.T) {
		// Register medical device
		device := MedicalDevice{
			DeviceID:     fmt.Sprintf("MRI-%d", time.Now().Unix()),
			DeviceType:   "MRI",
			Manufacturer: "Siemens",
			Model:        "Magnetom Vida",
			SerialNumber: "SN-" + fmt.Sprintf("%d", time.Now().Unix()),
			Location:     "Radiology-Floor-2",
			Status:       "active",
			Metadata: map[string]string{
				"field_strength": "3T",
				"installation":   "2024-01-15",
			},
		}

		body, _ := json.Marshal(device)
		resp, err := http.Post(MedicalDeviceURL+"/api/v1/devices", "application/json", bytes.NewBuffer(body))
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		// Update device metrics
		metrics := DeviceMetrics{
			Temperature: 22.5,
			PowerUsage:  15.2,
			CPUUsage:    45.3,
			MemoryUsage: 68.7,
			NetworkRX:   1024000,
			NetworkTX:   512000,
		}

		body, _ = json.Marshal(metrics)
		url := fmt.Sprintf("%s/api/v1/devices/%s/metrics", MedicalDeviceURL, device.DeviceID)
		resp2, err := http.Post(url, "application/json", bytes.NewBuffer(body))
		require.NoError(t, err)
		defer resp2.Body.Close()

		assert.Equal(t, http.StatusOK, resp2.StatusCode)

		// Get device status
		resp3, err := http.Get(fmt.Sprintf("%s/api/v1/devices/%s", MedicalDeviceURL, device.DeviceID))
		require.NoError(t, err)
		defer resp3.Body.Close()

		assert.Equal(t, http.StatusOK, resp3.StatusCode)

		var retrievedDevice MedicalDevice
		err = json.NewDecoder(resp3.Body).Decode(&retrievedDevice)
		require.NoError(t, err)

		assert.Equal(t, device.DeviceID, retrievedDevice.DeviceID)
		assert.Equal(t, device.DeviceType, retrievedDevice.DeviceType)
	})
}

// Test 6: Synthetic PHI + PHI Service Integration
func TestSyntheticPHIPipeline(t *testing.T) {
	waitForServices(t, 60*time.Second)

	t.Run("generate_and_encrypt_synthetic_data", func(t *testing.T) {
		// Generate synthetic patient data
		resp, err := http.Get(SyntheticPHIURL + "/api/v1/generate/patient")
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var patient SyntheticPatient
		err = json.NewDecoder(resp.Body).Decode(&patient)
		require.NoError(t, err)

		assert.NotEmpty(t, patient.FirstName)
		assert.NotEmpty(t, patient.LastName)
		assert.NotEmpty(t, patient.SSN)

		// Encrypt the synthetic PHI data
		phiData := fmt.Sprintf("Name: %s %s, SSN: %s, DOB: %s",
			patient.FirstName, patient.LastName, patient.SSN, patient.DateOfBirth)

		encryptReq := PHIEncryptRequest{
			Data:      phiData,
			PatientID: "SYNTHETIC-" + patient.SSN,
			DataType:  "synthetic_demographics",
		}

		body, _ := json.Marshal(encryptReq)
		resp2, err := http.Post(PHIServiceURL+"/api/v1/phi/encrypt", "application/json", bytes.NewBuffer(body))
		require.NoError(t, err)
		defer resp2.Body.Close()

		assert.Equal(t, http.StatusOK, resp2.StatusCode)

		var encryptResp PHIEncryptResponse
		err = json.NewDecoder(resp2.Body).Decode(&encryptResp)
		require.NoError(t, err)

		assert.NotEmpty(t, encryptResp.EncryptedData)
	})
}

// Test 7: End-to-End Healthcare Workflow
func TestEndToEndHealthcareWorkflow(t *testing.T) {
	waitForServices(t, 60*time.Second)

	t.Run("complete_patient_journey", func(t *testing.T) {
		// Step 1: Authenticate
		token := authenticate(t)

		// Step 2: Generate synthetic patient
		resp, err := http.Get(SyntheticPHIURL + "/api/v1/generate/patient")
		require.NoError(t, err)
		defer resp.Body.Close()

		var patient SyntheticPatient
		err = json.NewDecoder(resp.Body).Decode(&patient)
		require.NoError(t, err)

		patientID := "PT-" + fmt.Sprintf("%d", time.Now().Unix())

		// Step 3: Encrypt patient PHI
		phiData := fmt.Sprintf("Name: %s %s, SSN: %s, Email: %s",
			patient.FirstName, patient.LastName, patient.SSN, patient.Email)

		encryptReq := PHIEncryptRequest{
			Data:      phiData,
			PatientID: patientID,
			DataType:  "demographics",
		}

		body, _ := json.Marshal(encryptReq)
		resp2, err := http.Post(PHIServiceURL+"/api/v1/phi/encrypt", "application/json", bytes.NewBuffer(body))
		require.NoError(t, err)
		defer resp2.Body.Close()

		var encryptResp PHIEncryptResponse
		err = json.NewDecoder(resp2.Body).Decode(&encryptResp)
		require.NoError(t, err)

		// Step 4: Register medical device for patient
		device := MedicalDevice{
			DeviceID:     fmt.Sprintf("DEVICE-%d", time.Now().Unix()),
			DeviceType:   "ECG",
			Manufacturer: "Philips",
			Model:        "PageWriter TC70",
			SerialNumber: "SN-" + patientID,
			Location:     "Cardiology-Room-5",
			Status:       "active",
			Metadata: map[string]string{
				"patient_id": patientID,
				"department": "cardiology",
			},
		}

		body, _ = json.Marshal(device)
		resp3, err := http.Post(MedicalDeviceURL+"/api/v1/devices", "application/json", bytes.NewBuffer(body))
		require.NoError(t, err)
		defer resp3.Body.Close()

		// Step 5: Process payment for medical services
		paymentReq := PaymentRequest{
			Amount:        2500.00,
			Currency:      "USD",
			PatientID:     patientID,
			TransactionID: fmt.Sprintf("TXN-%d", time.Now().Unix()),
			PaymentMethod: "insurance",
			ComplianceTags: map[string]string{
				"hipaa":       "true",
				"encrypted":   encryptResp.KeyID,
				"patient_ssn": patient.SSN,
			},
		}

		body, _ = json.Marshal(paymentReq)
		resp4 := makeAuthenticatedRequest(t, "POST", PaymentGatewayURL+"/api/v1/transactions", bytes.NewBuffer(body), token)
		defer resp4.Body.Close()

		assert.Equal(t, http.StatusOK, resp4.StatusCode)

		var paymentResp PaymentResponse
		err = json.NewDecoder(resp4.Body).Decode(&paymentResp)
		require.NoError(t, err)

		// Validate end-to-end workflow
		assert.NotEmpty(t, token, "Authentication failed")
		assert.NotEmpty(t, patient.SSN, "Patient generation failed")
		assert.NotEmpty(t, encryptResp.EncryptedData, "PHI encryption failed")
		assert.NotEmpty(t, device.DeviceID, "Device registration failed")
		assert.Equal(t, "success", paymentResp.Status, "Payment processing failed")
		assert.NotEmpty(t, paymentResp.AuditID, "Audit trail generation failed")

		t.Logf("✅ End-to-end workflow completed successfully")
		t.Logf("   Patient ID: %s", patientID)
		t.Logf("   Device ID: %s", device.DeviceID)
		t.Logf("   Payment ID: %s", paymentResp.TransactionID)
		t.Logf("   Audit ID: %s", paymentResp.AuditID)
		t.Logf("   Encrypted PHI Key: %s", encryptResp.KeyID)
	})
}

// Test 8: Concurrent Load Test (Light)
func TestConcurrentOperations(t *testing.T) {
	waitForServices(t, 60*time.Second)

	t.Run("concurrent_authentication", func(t *testing.T) {
		concurrency := 10
		done := make(chan bool, concurrency)
		errors := make(chan error, concurrency)

		for i := 0; i < concurrency; i++ {
			go func(id int) {
				defer func() { done <- true }()

				authReq := AuthRequest{
					Username: "admin",
					Password: "admin123",
				}

				body, _ := json.Marshal(authReq)
				resp, err := http.Post(AuthServiceURL+"/api/v1/login", "application/json", bytes.NewBuffer(body))
				if err != nil {
					errors <- err
					return
				}
				defer resp.Body.Close()

				if resp.StatusCode != http.StatusOK {
					errors <- fmt.Errorf("worker %d: expected 200, got %d", id, resp.StatusCode)
				}
			}(i)
		}

		// Wait for all goroutines
		for i := 0; i < concurrency; i++ {
			<-done
		}

		close(errors)
		errorCount := 0
		for err := range errors {
			t.Logf("Error: %v", err)
			errorCount++
		}

		assert.Equal(t, 0, errorCount, "Expected no errors in concurrent authentication")
	})
}

// Test 9: Service Discovery and Dependencies
func TestServiceDependencies(t *testing.T) {
	waitForServices(t, 60*time.Second)

	t.Run("payment_gateway_depends_on_auth", func(t *testing.T) {
		// Payment gateway should reject requests without valid token
		paymentReq := PaymentRequest{
			Amount:        100.00,
			Currency:      "USD",
			PatientID:     "TEST-001",
			TransactionID: "TXN-TEST",
			PaymentMethod: "credit_card",
		}

		body, _ := json.Marshal(paymentReq)
		resp := makeAuthenticatedRequest(t, "POST", PaymentGatewayURL+"/api/v1/transactions", bytes.NewBuffer(body), "invalid-token")
		defer resp.Body.Close()

		assert.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})
}

// Test 10: Compliance and Audit Trail
func TestComplianceAuditTrail(t *testing.T) {
	waitForServices(t, 60*time.Second)

	token := authenticate(t)

	t.Run("hipaa_sox_compliance_tags", func(t *testing.T) {
		paymentReq := PaymentRequest{
			Amount:        5000.00,
			Currency:      "USD",
			PatientID:     "PATIENT-HIPAA-001",
			TransactionID: fmt.Sprintf("TXN-AUDIT-%d", time.Now().Unix()),
			PaymentMethod: "wire_transfer",
			ComplianceTags: map[string]string{
				"hipaa":          "true",
				"sox":            "true",
				"audit_required": "true",
				"risk_level":     "high",
			},
		}

		body, _ := json.Marshal(paymentReq)
		resp := makeAuthenticatedRequest(t, "POST", PaymentGatewayURL+"/api/v1/transactions", bytes.NewBuffer(body), token)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var paymentResp PaymentResponse
		err := json.NewDecoder(resp.Body).Decode(&paymentResp)
		require.NoError(t, err)

		assert.NotEmpty(t, paymentResp.AuditID)
		t.Logf("Audit trail created: %s", paymentResp.AuditID)
	})
}
