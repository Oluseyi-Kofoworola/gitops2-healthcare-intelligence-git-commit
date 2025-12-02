// filepath: tests/contract/auth_contract_test.go
package contract

import (
	"fmt"
	"net/http"
	"testing"

	"github.com/pact-foundation/pact-go/dsl"
	"github.com/stretchr/testify/assert"
)

// TestAuthServiceContract - Consumer-driven contract tests for Auth Service
func TestAuthServiceContract(t *testing.T) {
	// Create Pact DSL
	pact := &dsl.Pact{
		Consumer: "PaymentGateway",
		Provider: "AuthService",
		Host:     "localhost",
	}
	defer pact.Teardown()

	t.Run("Login with valid credentials", func(t *testing.T) {
		pact.
			AddInteraction().
			Given("User admin exists with password admin123").
			UponReceiving("A request to login with valid credentials").
			WithRequest(dsl.Request{
				Method: "POST",
				Path:   dsl.String("/api/v1/login"),
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: map[string]interface{}{
					"username": "admin",
					"password": "admin123",
				},
			}).
			WillRespondWith(dsl.Response{
				Status: 200,
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: dsl.Match(map[string]interface{}{
					"token":      dsl.Like("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."),
					"expires_in": dsl.Like(900),
					"token_type": dsl.Term("Bearer", "Bearer"),
				}),
			})

		// Start mock server
		err := pact.Verify(func() error {
			client := &http.Client{}
			req, _ := http.NewRequest("POST", fmt.Sprintf("http://localhost:%d/api/v1/login", pact.Server.Port), nil)
			req.Header.Set("Content-Type", "application/json")
			
			resp, err := client.Do(req)
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 200, resp.StatusCode)
			return nil
		})

		assert.NoError(t, err)
	})

	t.Run("Login with invalid credentials", func(t *testing.T) {
		pact.
			AddInteraction().
			Given("User with invalid credentials").
			UponReceiving("A request to login with invalid credentials").
			WithRequest(dsl.Request{
				Method: "POST",
				Path:   dsl.String("/api/v1/login"),
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: map[string]interface{}{
					"username": "invalid",
					"password": "wrong",
				},
			}).
			WillRespondWith(dsl.Response{
				Status: 401,
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: dsl.Match(map[string]interface{}{
					"error":   dsl.Like("Unauthorized"),
					"message": dsl.Like("Invalid username or password"),
				}),
			})

		err := pact.Verify(func() error {
			client := &http.Client{}
			req, _ := http.NewRequest("POST", fmt.Sprintf("http://localhost:%d/api/v1/login", pact.Server.Port), nil)
			req.Header.Set("Content-Type", "application/json")
			
			resp, err := client.Do(req)
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 401, resp.StatusCode)
			return nil
		})

		assert.NoError(t, err)
	})

	t.Run("Token validation", func(t *testing.T) {
		pact.
			AddInteraction().
			Given("Valid JWT token exists").
			UponReceiving("A request to validate token").
			WithRequest(dsl.Request{
				Method: "POST",
				Path:   dsl.String("/api/v1/validate"),
				Headers: dsl.MapMatcher{
					"Content-Type":  dsl.String("application/json"),
					"Authorization": dsl.Term("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "Bearer .+"),
				},
			}).
			WillRespondWith(dsl.Response{
				Status: 200,
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: dsl.Match(map[string]interface{}{
					"valid":    dsl.Like(true),
					"username": dsl.Like("admin"),
					"exp":      dsl.Like(1700000000),
				}),
			})

		err := pact.Verify(func() error {
			client := &http.Client{}
			req, _ := http.NewRequest("POST", fmt.Sprintf("http://localhost:%d/api/v1/validate", pact.Server.Port), nil)
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("Authorization", "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
			
			resp, err := client.Do(req)
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 200, resp.StatusCode)
			return nil
		})

		assert.NoError(t, err)
	})

	t.Run("Health check endpoint", func(t *testing.T) {
		pact.
			AddInteraction().
			Given("Auth service is healthy").
			UponReceiving("A health check request").
			WithRequest(dsl.Request{
				Method: "GET",
				Path:   dsl.String("/health"),
			}).
			WillRespondWith(dsl.Response{
				Status: 200,
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: dsl.Match(map[string]interface{}{
					"status":  dsl.Term("healthy", "healthy|degraded|unhealthy"),
					"service": dsl.Like("auth-service"),
					"version": dsl.Like("1.0.0"),
				}),
			})

		err := pact.Verify(func() error {
			resp, err := http.Get(fmt.Sprintf("http://localhost:%d/health", pact.Server.Port))
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 200, resp.StatusCode)
			return nil
		})

		assert.NoError(t, err)
	})

	// Publish pacts to broker (if configured)
	if brokerURL := getPactBrokerURL(); brokerURL != "" {
		pact.WritePact()
		publishPacts(brokerURL, "1.0.0")
	}
}

// TestPHIServiceContract - Contract tests for PHI Service
func TestPHIServiceContract(t *testing.T) {
	pact := &dsl.Pact{
		Consumer: "PaymentGateway",
		Provider: "PHIService",
		Host:     "localhost",
	}
	defer pact.Teardown()

	t.Run("Encrypt PHI data", func(t *testing.T) {
		pact.
			AddInteraction().
			Given("PHI service is ready to encrypt data").
			UponReceiving("A request to encrypt patient data").
			WithRequest(dsl.Request{
				Method: "POST",
				Path:   dsl.String("/api/v1/phi/encrypt"),
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: map[string]interface{}{
					"data":       dsl.Like("Patient SSN: 123-45-6789"),
					"patient_id": dsl.Like("PATIENT-001"),
					"data_type":  dsl.Term("demographics", "demographics|medical_record|diagnosis"),
				},
			}).
			WillRespondWith(dsl.Response{
				Status: 200,
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: dsl.Match(map[string]interface{}{
					"encrypted_data": dsl.Like("AES256GCM-encrypted-data..."),
					"key_id":         dsl.Like("key-12345"),
					"algorithm":      dsl.Term("AES-256-GCM", "AES-256-GCM"),
					"encrypted_at":   dsl.Like("2025-11-23T10:00:00Z"),
				}),
			})

		err := pact.Verify(func() error {
			resp, err := http.Post(
				fmt.Sprintf("http://localhost:%d/api/v1/phi/encrypt", pact.Server.Port),
				"application/json",
				nil,
			)
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 200, resp.StatusCode)
			return nil
		})

		assert.NoError(t, err)
	})

	t.Run("Decrypt PHI data", func(t *testing.T) {
		pact.
			AddInteraction().
			Given("Encrypted PHI data exists").
			UponReceiving("A request to decrypt patient data").
			WithRequest(dsl.Request{
				Method: "POST",
				Path:   dsl.String("/api/v1/phi/decrypt"),
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: map[string]interface{}{
					"encrypted_data": dsl.Like("AES256GCM-encrypted-data..."),
					"key_id":         dsl.Like("key-12345"),
				},
			}).
			WillRespondWith(dsl.Response{
				Status: 200,
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: dsl.Match(map[string]interface{}{
					"data":         dsl.Like("Patient SSN: 123-45-6789"),
					"decrypted_at": dsl.Like("2025-11-23T10:00:00Z"),
				}),
			})

		err := pact.Verify(func() error {
			resp, err := http.Post(
				fmt.Sprintf("http://localhost:%d/api/v1/phi/decrypt", pact.Server.Port),
				"application/json",
				nil,
			)
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 200, resp.StatusCode)
			return nil
		})

		assert.NoError(t, err)
	})
}

// TestMedicalDeviceContract - Contract tests for Medical Device Service
func TestMedicalDeviceContract(t *testing.T) {
	pact := &dsl.Pact{
		Consumer: "MonitoringDashboard",
		Provider: "MedicalDeviceService",
		Host:     "localhost",
	}
	defer pact.Teardown()

	t.Run("Register medical device", func(t *testing.T) {
		pact.
			AddInteraction().
			Given("Medical device registration is available").
			UponReceiving("A request to register a new device").
			WithRequest(dsl.Request{
				Method: "POST",
				Path:   dsl.String("/api/v1/devices"),
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: map[string]interface{}{
					"device_id":     dsl.Like("MRI-001"),
					"device_type":   dsl.Term("MRI", "MRI|CT_Scanner|X-Ray|ECG|Ventilator|Pump"),
					"manufacturer":  dsl.Like("Siemens"),
					"model":         dsl.Like("Magnetom Vida"),
					"serial_number": dsl.Like("SN-12345"),
					"location":      dsl.Like("Radiology-Floor-2"),
					"status":        dsl.Term("active", "active|inactive|maintenance"),
				},
			}).
			WillRespondWith(dsl.Response{
				Status: 200,
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: dsl.Match(map[string]interface{}{
					"device_id":   dsl.Like("MRI-001"),
					"status":      dsl.Like("registered"),
					"message":     dsl.Like("Device registered successfully"),
					"location":    dsl.Like("Radiology-Floor-2"),
					"device_type": dsl.Like("MRI"),
				}),
			})

		err := pact.Verify(func() error {
			resp, err := http.Post(
				fmt.Sprintf("http://localhost:%d/api/v1/devices", pact.Server.Port),
				"application/json",
				nil,
			)
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 200, resp.StatusCode)
			return nil
		})

		assert.NoError(t, err)
	})

	t.Run("Get device metrics", func(t *testing.T) {
		pact.
			AddInteraction().
			Given("Device MRI-001 exists with metrics").
			UponReceiving("A request to get device metrics").
			WithRequest(dsl.Request{
				Method: "GET",
				Path:   dsl.String("/api/v1/devices/MRI-001/metrics"),
			}).
			WillRespondWith(dsl.Response{
				Status: 200,
				Headers: dsl.MapMatcher{
					"Content-Type": dsl.String("application/json"),
				},
				Body: dsl.Match(map[string]interface{}{
					"device_id":    dsl.Like("MRI-001"),
					"temperature":  dsl.Like(22.5),
					"power_usage":  dsl.Like(15.2),
					"cpu_usage":    dsl.Like(45.3),
					"memory_usage": dsl.Like(68.7),
					"network_rx":   dsl.Like(1024000),
					"network_tx":   dsl.Like(512000),
					"timestamp":    dsl.Like("2025-11-23T10:00:00Z"),
				}),
			})

		err := pact.Verify(func() error {
			resp, err := http.Get(fmt.Sprintf("http://localhost:%d/api/v1/devices/MRI-001/metrics", pact.Server.Port))
			if err != nil {
				return err
			}
			defer resp.Body.Close()

			assert.Equal(t, 200, resp.StatusCode)
			return nil
		})

		assert.NoError(t, err)
	})
}

// Helper functions
func getPactBrokerURL() string {
	// Return Pact Broker URL if configured
	// For local development, return empty string
	return ""
}

func publishPacts(brokerURL, version string) error {
	// Publish pacts to broker
	// Implementation depends on Pact Broker setup
	return nil
}
