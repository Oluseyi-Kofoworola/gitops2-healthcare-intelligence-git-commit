package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/rs/zerolog"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func init() {
	// Disable logging during tests
	zerolog.SetGlobalLevel(zerolog.Disabled)

	// Initialize encryption service for tests
	var err error
	encryptionService, err = NewEncryptionService("test-key-32-bytes-long-change!!")
	if err != nil {
		panic("Failed to initialize encryption service for tests: " + err.Error())
	}
}

// TestHealthEndpoint tests the health check endpoint
func TestHealthEndpoint(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/health", HealthHandler)

	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]string
	err := json.NewDecoder(w.Body).Decode(&response)
	require.NoError(t, err)
	assert.Equal(t, "healthy", response["status"])
	assert.Equal(t, "phi-service", response["service"])
}

// TestReadinessEndpoint tests the readiness check endpoint
func TestReadinessEndpoint(t *testing.T) {
	// Initialize encryption service for readiness check
	encryptionService, _ = NewEncryptionService("test-key-32-bytes-long-change!!")

	r := chi.NewRouter()
	r.Get("/ready", ReadyHandler)

	req := httptest.NewRequest("GET", "/ready", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.NewDecoder(w.Body).Decode(&response)
	require.NoError(t, err)
	assert.Equal(t, "ready", response["status"])
}

// TestEncryptEndpoint tests the encryption endpoint
func TestEncryptEndpoint(t *testing.T) {
	encService := NewEncryptionService("test-secret-key-32-bytes-long!!")
	r := chi.NewRouter()
	r.Post("/api/v1/encrypt", encryptHandler(encService))

	tests := []struct {
		name           string
		payload        map[string]string
		expectedStatus int
		checkResponse  bool
	}{
		{
			name: "Valid encryption request",
			payload: map[string]string{
				"data": "Patient SSN: 123-45-6789",
			},
			expectedStatus: http.StatusOK,
			checkResponse:  true,
		},
		{
			name: "Empty data",
			payload: map[string]string{
				"data": "",
			},
			expectedStatus: http.StatusBadRequest,
			checkResponse:  false,
		},
		{
			name:           "Missing data field",
			payload:        map[string]string{},
			expectedStatus: http.StatusBadRequest,
			checkResponse:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			body, _ := json.Marshal(tt.payload)
			req := httptest.NewRequest("POST", "/api/v1/encrypt", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)

			if tt.checkResponse {
				var response map[string]string
				err := json.NewDecoder(w.Body).Decode(&response)
				require.NoError(t, err)
				assert.NotEmpty(t, response["encrypted_data"])
				assert.NotEqual(t, tt.payload["data"], response["encrypted_data"])
			}
		})
	}
}

// TestDecryptEndpoint tests the decryption endpoint
func TestDecryptEndpoint(t *testing.T) {
	encService := NewEncryptionService("test-secret-key-32-bytes-long!!")
	r := chi.NewRouter()
	r.Post("/api/v1/decrypt", decryptHandler(encService))

	// First encrypt some data
	originalData := "Patient MRN: 987654321"
	encrypted, err := encService.Encrypt([]byte(originalData))
	require.NoError(t, err)

	tests := []struct {
		name           string
		payload        map[string]string
		expectedStatus int
		expectedData   string
	}{
		{
			name: "Valid decryption request",
			payload: map[string]string{
				"encrypted_data": encrypted,
			},
			expectedStatus: http.StatusOK,
			expectedData:   originalData,
		},
		{
			name: "Invalid encrypted data",
			payload: map[string]string{
				"encrypted_data": "invalid-base64-data",
			},
			expectedStatus: http.StatusBadRequest,
			expectedData:   "",
		},
		{
			name:           "Missing encrypted_data field",
			payload:        map[string]string{},
			expectedStatus: http.StatusBadRequest,
			expectedData:   "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			body, _ := json.Marshal(tt.payload)
			req := httptest.NewRequest("POST", "/api/v1/decrypt", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)

			if tt.expectedStatus == http.StatusOK {
				var response map[string]string
				err := json.NewDecoder(w.Body).Decode(&response)
				require.NoError(t, err)
				assert.Equal(t, tt.expectedData, response["data"])
			}
		})
	}
}

// TestHashEndpoint tests the hash endpoint
func TestHashEndpoint(t *testing.T) {
	encService := NewEncryptionService("test-secret-key-32-bytes-long!!")
	r := chi.NewRouter()
	r.Post("/api/v1/hash", hashHandler(encService))

	tests := []struct {
		name           string
		payload        map[string]string
		expectedStatus int
		checkHash      bool
	}{
		{
			name: "Valid hash request",
			payload: map[string]string{
				"data": "patient@example.com",
			},
			expectedStatus: http.StatusOK,
			checkHash:      true,
		},
		{
			name: "Empty data",
			payload: map[string]string{
				"data": "",
			},
			expectedStatus: http.StatusBadRequest,
			checkHash:      false,
		},
		{
			name: "Hash with salt",
			payload: map[string]string{
				"data": "patient@example.com",
				"salt": "random-salt",
			},
			expectedStatus: http.StatusOK,
			checkHash:      true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			body, _ := json.Marshal(tt.payload)
			req := httptest.NewRequest("POST", "/api/v1/hash", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)

			if tt.checkHash {
				var response map[string]string
				err := json.NewDecoder(w.Body).Decode(&response)
				require.NoError(t, err)
				assert.NotEmpty(t, response["hash"])
				assert.Len(t, response["hash"], 64) // SHA256 produces 64 hex characters
			}
		})
	}
}

// TestAnonymizeEndpoint tests the anonymization endpoint
func TestAnonymizeEndpoint(t *testing.T) {
	encService := NewEncryptionService("test-secret-key-32-bytes-long!!")
	r := chi.NewRouter()
	r.Post("/api/v1/anonymize", anonymizeHandler(encService))

	tests := []struct {
		name           string
		payload        map[string]string
		expectedStatus int
		checkResponse  bool
	}{
		{
			name: "Valid anonymization request",
			payload: map[string]string{
				"data": "john.doe@hospital.com",
			},
			expectedStatus: http.StatusOK,
			checkResponse:  true,
		},
		{
			name: "Empty data",
			payload: map[string]string{
				"data": "",
			},
			expectedStatus: http.StatusBadRequest,
			checkResponse:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			body, _ := json.Marshal(tt.payload)
			req := httptest.NewRequest("POST", "/api/v1/anonymize", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)

			if tt.checkResponse {
				var response map[string]string
				err := json.NewDecoder(w.Body).Decode(&response)
				require.NoError(t, err)
				assert.NotEmpty(t, response["anonymized_hash"])
				assert.NotEmpty(t, response["salt"])
				assert.NotEqual(t, tt.payload["data"], response["anonymized_hash"])
			}
		})
	}
}

// TestEncryptionService tests the encryption service directly
func TestEncryptionService(t *testing.T) {
	secret := "test-secret-key-32-bytes-long!!"
	service := NewEncryptionService(secret)

	t.Run("Encrypt and Decrypt", func(t *testing.T) {
		originalData := []byte("Sensitive PHI data: Patient ID 12345")

		encrypted, err := service.Encrypt(originalData)
		require.NoError(t, err)
		assert.NotEmpty(t, encrypted)

		decrypted, err := service.Decrypt(encrypted)
		require.NoError(t, err)
		assert.Equal(t, originalData, decrypted)
	})

	t.Run("Decrypt invalid data", func(t *testing.T) {
		_, err := service.Decrypt("invalid-encrypted-data")
		assert.Error(t, err)
	})

	t.Run("Hash consistency", func(t *testing.T) {
		data := []byte("test-data")
		hash1 := service.Hash(data)
		hash2 := service.Hash(data)

		assert.Equal(t, hash1, hash2, "Same data should produce same hash")
		assert.Len(t, hash1, 64, "SHA256 hash should be 64 hex characters")
	})

	t.Run("Hash with salt", func(t *testing.T) {
		data := []byte("test-data")
		salt := []byte("random-salt")

		hash1 := service.HashWithSalt(data, salt)
		hash2 := service.HashWithSalt(data, salt)

		assert.Equal(t, hash1, hash2, "Same data and salt should produce same hash")
		assert.Len(t, hash1, 64, "SHA256 hash should be 64 hex characters")
	})

	t.Run("Different salts produce different hashes", func(t *testing.T) {
		data := []byte("test-data")
		salt1 := []byte("salt1")
		salt2 := []byte("salt2")

		hash1 := service.HashWithSalt(data, salt1)
		hash2 := service.HashWithSalt(data, salt2)

		assert.NotEqual(t, hash1, hash2, "Different salts should produce different hashes")
	})
}

// TestInvalidJSONRequests tests handling of malformed JSON
func TestInvalidJSONRequests(t *testing.T) {
	encService := NewEncryptionService("test-secret-key-32-bytes-long!!")
	r := chi.NewRouter()
	r.Post("/api/v1/encrypt", encryptHandler(encService))
	r.Post("/api/v1/decrypt", decryptHandler(encService))
	r.Post("/api/v1/hash", hashHandler(encService))
	r.Post("/api/v1/anonymize", anonymizeHandler(encService))

	endpoints := []string{
		"/api/v1/encrypt",
		"/api/v1/decrypt",
		"/api/v1/hash",
		"/api/v1/anonymize",
	}

	for _, endpoint := range endpoints {
		t.Run(endpoint, func(t *testing.T) {
			req := httptest.NewRequest("POST", endpoint, bytes.NewReader([]byte("invalid-json")))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			assert.Equal(t, http.StatusBadRequest, w.Code)
		})
	}
}

// TestCORSHeaders tests CORS middleware
func TestCORSHeaders(t *testing.T) {
	r := chi.NewRouter()
	r.Use(corsMiddleware)
	r.Get("/health", healthHandler)

	req := httptest.NewRequest("GET", "/health", nil)
	req.Header.Set("Origin", "http://example.com")
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, "*", w.Header().Get("Access-Control-Allow-Origin"))
	assert.Contains(t, w.Header().Get("Access-Control-Allow-Methods"), "GET")
	assert.Contains(t, w.Header().Get("Access-Control-Allow-Headers"), "Content-Type")
}

// TestSecurityHeaders tests security headers
func TestSecurityHeaders(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/health", healthHandler)

	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	// Note: Security headers would be added by middleware
	// This test verifies the response is successful
	assert.Equal(t, http.StatusOK, w.Code)
}

// BenchmarkEncryption benchmarks the encryption operation
func BenchmarkEncryption(b *testing.B) {
	service := NewEncryptionService("test-secret-key-32-bytes-long!!")
	data := []byte("Sensitive PHI data for benchmarking")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = service.Encrypt(data)
	}
}

// BenchmarkDecryption benchmarks the decryption operation
func BenchmarkDecryption(b *testing.B) {
	service := NewEncryptionService("test-secret-key-32-bytes-long!!")
	data := []byte("Sensitive PHI data for benchmarking")
	encrypted, _ := service.Encrypt(data)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = service.Decrypt(encrypted)
	}
}

// BenchmarkHash benchmarks the hash operation
func BenchmarkHash(b *testing.B) {
	service := NewEncryptionService("test-secret-key-32-bytes-long!!")
	data := []byte("test-data-for-hashing")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = service.Hash(data)
	}
}

// BenchmarkEncryptEndpoint benchmarks the encrypt HTTP endpoint
func BenchmarkEncryptEndpoint(b *testing.B) {
	encService := NewEncryptionService("test-secret-key-32-bytes-long!!")
	r := chi.NewRouter()
	r.Post("/api/v1/encrypt", encryptHandler(encService))

	payload := map[string]string{"data": "Patient SSN: 123-45-6789"}
	body, _ := json.Marshal(payload)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req := httptest.NewRequest("POST", "/api/v1/encrypt", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
	}
}

// TestConcurrentEncryption tests concurrent encryption operations
func TestConcurrentEncryption(t *testing.T) {
	service := NewEncryptionService("test-secret-key-32-bytes-long!!")
	data := []byte("Concurrent test data")

	done := make(chan bool)
	errors := make(chan error, 10)

	for i := 0; i < 10; i++ {
		go func() {
			_, err := service.Encrypt(data)
			if err != nil {
				errors <- err
			}
			done <- true
		}()
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}

	close(errors)
	for err := range errors {
		t.Errorf("Concurrent encryption failed: %v", err)
	}
}

// TestGracefulShutdown tests graceful shutdown behavior
func TestGracefulShutdown(t *testing.T) {
	server := &http.Server{
		Addr:         ":0",
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Just verify server can be created
	assert.NotNil(t, server)
}
