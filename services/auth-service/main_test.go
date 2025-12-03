package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// TestHealth verifies the health endpoint returns correct status
func TestHealth(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rr := httptest.NewRecorder()
	h.Health(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", rr.Code)
	}

	var body map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil {
		t.Fatalf("failed to parse body: %v", err)
	}

	if body["status"] != "healthy" {
		t.Fatalf("unexpected status %v", body["status"])
	}

	if body["service"] != "auth-service" {
		t.Fatalf("unexpected service %v", body["service"])
	}

	// Verify security headers
	if rr.Header().Get("X-Content-Type-Options") != "nosniff" {
		t.Fatal("Missing X-Content-Type-Options header")
	}
}

// TestReadiness verifies the readiness endpoint
func TestReadiness(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/readiness", nil)
	rr := httptest.NewRecorder()
	h.Readiness(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", rr.Code)
	}

	var body map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil {
		t.Fatalf("failed to parse body: %v", err)
	}

	if ready, ok := body["ready"].(bool); !ok || !ready {
		t.Fatalf("expected ready=true, got %v", body["ready"])
	}
}

// TestGenerateToken verifies token generation
func TestGenerateToken(t *testing.T) {
	h := AuthHandler{}

	reqBody := map[string]interface{}{
		"user_id": "user123",
		"scopes":  []string{"payment:write", "phi:read"},
		"role":    "admin",
	}
	bodyBytes, _ := json.Marshal(reqBody)

	req := httptest.NewRequest(http.MethodPost, "/token", bytes.NewReader(bodyBytes))
	rr := httptest.NewRecorder()
	h.GenerateToken(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", rr.Code)
	}

	var response map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Fatalf("failed to parse response: %v", err)
	}

	tokenString, ok := response["token"].(string)
	if !ok || tokenString == "" {
		t.Fatal("expected token in response")
	}

	if response["token_type"] != "Bearer" {
		t.Fatalf("expected token_type=Bearer, got %v", response["token_type"])
	}

	// Verify token can be parsed
	token, err := jwt.ParseWithClaims(tokenString, &TokenClaims{}, func(token *jwt.Token) (interface{}, error) {
		return jwtSecret, nil
	})

	if err != nil || !token.Valid {
		t.Fatalf("generated token is invalid: %v", err)
	}

	claims, ok := token.Claims.(*TokenClaims)
	if !ok {
		t.Fatal("failed to parse token claims")
	}

	if claims.UserID != "user123" {
		t.Fatalf("expected user_id=user123, got %s", claims.UserID)
	}

	if claims.Role != "admin" {
		t.Fatalf("expected role=admin, got %s", claims.Role)
	}
}

// TestGenerateToken_MethodNotAllowed verifies POST-only endpoint
func TestGenerateToken_MethodNotAllowed(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/token", nil)
	rr := httptest.NewRecorder()
	h.GenerateToken(rr, req)

	if rr.Code != http.StatusMethodNotAllowed {
		t.Fatalf("expected 405 got %d", rr.Code)
	}
}

// TestGenerateToken_InvalidBody verifies validation
func TestGenerateToken_InvalidBody(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodPost, "/token", strings.NewReader("invalid json"))
	rr := httptest.NewRecorder()
	h.GenerateToken(rr, req)

	if rr.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 got %d", rr.Code)
	}
}

// TestIntrospect_ValidToken verifies token validation
func TestIntrospect_ValidToken(t *testing.T) {
	h := AuthHandler{}

	// Generate a valid token
	claims := TokenClaims{
		UserID: "test-user",
		Scopes: []string{"payment:write"},
		Role:   "user",
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(15 * time.Minute)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString(jwtSecret)
	if err != nil {
		t.Fatalf("failed to generate token: %v", err)
	}

	// Test introspection
	req := httptest.NewRequest(http.MethodGet, "/introspect", nil)
	req.Header.Set("Authorization", "Bearer "+tokenString)
	rr := httptest.NewRecorder()
	h.Introspect(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", rr.Code)
	}

	var response IntrospectResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Fatalf("failed to parse response: %v", err)
	}

	if !response.Active {
		t.Fatal("expected active=true")
	}

	if response.UserID != "test-user" {
		t.Fatalf("expected user_id=test-user, got %s", response.UserID)
	}

	if response.Role != "user" {
		t.Fatalf("expected role=user, got %s", response.Role)
	}

	if len(response.Scopes) != 1 || response.Scopes[0] != "payment:write" {
		t.Fatalf("unexpected scopes: %v", response.Scopes)
	}
}

// TestIntrospect_MissingToken verifies missing token handling
func TestIntrospect_MissingToken(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/introspect", nil)
	rr := httptest.NewRecorder()
	h.Introspect(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 got %d", rr.Code)
	}

	var response IntrospectResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Fatalf("failed to parse response: %v", err)
	}

	if response.Active {
		t.Fatal("expected active=false for missing token")
	}
}

// TestIntrospect_InvalidTokenFormat verifies token format validation
func TestIntrospect_InvalidTokenFormat(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/introspect", nil)
	req.Header.Set("Authorization", "InvalidFormat token123")
	rr := httptest.NewRecorder()
	h.Introspect(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 got %d", rr.Code)
	}
}

// TestIntrospect_InvalidToken verifies invalid token handling
func TestIntrospect_InvalidToken(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/introspect", nil)
	req.Header.Set("Authorization", "Bearer invalid.token.here")
	rr := httptest.NewRecorder()
	h.Introspect(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 got %d", rr.Code)
	}

	var response IntrospectResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Fatalf("failed to parse response: %v", err)
	}

	if response.Active {
		t.Fatal("expected active=false for invalid token")
	}
}

// TestIntrospect_ExpiredToken verifies expired token handling
func TestIntrospect_ExpiredToken(t *testing.T) {
	h := AuthHandler{}

	// Generate an expired token
	claims := TokenClaims{
		UserID: "test-user",
		Scopes: []string{"payment:write"},
		Role:   "user",
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(-1 * time.Hour)), // Expired 1 hour ago
			IssuedAt:  jwt.NewNumericDate(time.Now().Add(-2 * time.Hour)),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString(jwtSecret)
	if err != nil {
		t.Fatalf("failed to generate token: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "/introspect", nil)
	req.Header.Set("Authorization", "Bearer "+tokenString)
	rr := httptest.NewRecorder()
	h.Introspect(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 got %d", rr.Code)
	}

	var response IntrospectResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Fatalf("failed to parse response: %v", err)
	}

	if response.Active {
		t.Fatal("expected active=false for expired token")
	}
}

// TestStartAuthServer_Routes verifies all routes are registered
func TestStartAuthServer_Routes(t *testing.T) {
	srv := StartAuthServer(":0")
	h := srv.Handler

	tests := []struct {
		name           string
		path           string
		method         string
		expectedStatus int
	}{
		{"Health", "/health", "GET", http.StatusOK},
		{"Readiness", "/readiness", "GET", http.StatusOK},
		{"Root", "/", "GET", http.StatusOK},
		{"Metrics", "/metrics", "GET", http.StatusOK},
		{"Token POST", "/token", "POST", http.StatusBadRequest}, // Missing body
		{"Token GET", "/token", "GET", http.StatusMethodNotAllowed},
		{"Introspect No Auth", "/introspect", "GET", http.StatusUnauthorized},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rr := httptest.NewRecorder()
			var req *http.Request
			if tt.method == "POST" {
				req = httptest.NewRequest(tt.method, tt.path, strings.NewReader(""))
			} else {
				req = httptest.NewRequest(tt.method, tt.path, nil)
			}
			h.ServeHTTP(rr, req)

			if rr.Code != tt.expectedStatus {
				t.Fatalf("%s: expected %d got %d", tt.name, tt.expectedStatus, rr.Code)
			}
		})
	}
}

// TestSecurityHeaders verifies security headers are set
func TestSecurityHeaders(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rr := httptest.NewRecorder()
	h.Health(rr, req)

	expectedHeaders := map[string]string{
		"X-Content-Type-Options":    "nosniff",
		"X-Frame-Options":           "DENY",
		"X-XSS-Protection":          "1; mode=block",
		"Content-Security-Policy":   "default-src 'self'",
		"Strict-Transport-Security": "max-age=31536000; includeSubDomains",
		"Content-Type":              "application/json",
	}

	for header, expected := range expectedHeaders {
		actual := rr.Header().Get(header)
		if actual != expected {
			t.Fatalf("expected %s=%s, got %s", header, expected, actual)
		}
	}

	// Verify X-Request-ID is present
	if rr.Header().Get("X-Request-ID") == "" {
		t.Fatal("expected X-Request-ID header")
	}
}

// TestTokenClaims_Scopes verifies multiple scopes
func TestTokenClaims_Scopes(t *testing.T) {
	h := AuthHandler{}

	claims := TokenClaims{
		UserID: "admin-user",
		Scopes: []string{"payment:read", "payment:write", "phi:read", "phi:write", "admin"},
		Role:   "admin",
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(15 * time.Minute)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, _ := token.SignedString(jwtSecret)

	req := httptest.NewRequest(http.MethodGet, "/introspect", nil)
	req.Header.Set("Authorization", "Bearer "+tokenString)
	rr := httptest.NewRecorder()
	h.Introspect(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", rr.Code)
	}

	var response IntrospectResponse
	json.Unmarshal(rr.Body.Bytes(), &response)

	if len(response.Scopes) != 5 {
		t.Fatalf("expected 5 scopes, got %d", len(response.Scopes))
	}

	// Verify all scopes are present
	scopeMap := make(map[string]bool)
	for _, scope := range response.Scopes {
		scopeMap[scope] = true
	}

	expectedScopes := []string{"payment:read", "payment:write", "phi:read", "phi:write", "admin"}
	for _, scope := range expectedScopes {
		if !scopeMap[scope] {
			t.Fatalf("expected scope %s not found", scope)
		}
	}
}

// BenchmarkTokenGeneration benchmarks token generation performance
func BenchmarkTokenGeneration(b *testing.B) {
	h := AuthHandler{}

	reqBody := map[string]interface{}{
		"user_id": "bench-user",
		"scopes":  []string{"payment:write"},
		"role":    "user",
	}
	bodyBytes, _ := json.Marshal(reqBody)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req := httptest.NewRequest(http.MethodPost, "/token", bytes.NewReader(bodyBytes))
		rr := httptest.NewRecorder()
		h.GenerateToken(rr, req)
	}
}

// BenchmarkTokenValidation benchmarks token validation performance
func BenchmarkTokenValidation(b *testing.B) {
	h := AuthHandler{}

	// Generate a valid token
	claims := TokenClaims{
		UserID: "bench-user",
		Scopes: []string{"payment:write"},
		Role:   "user",
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(15 * time.Minute)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, _ := token.SignedString(jwtSecret)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req := httptest.NewRequest(http.MethodGet, "/introspect", nil)
		req.Header.Set("Authorization", "Bearer "+tokenString)
		rr := httptest.NewRecorder()
		h.Introspect(rr, req)
	}
}
