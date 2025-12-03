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

// TestHealthComprehensive verifies the health endpoint returns correct status
func TestHealthComprehensive(t *testing.T) {
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

// TestReadinessComprehensive verifies the readiness endpoint
func TestReadinessComprehensive(t *testing.T) {
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

// TestGenerateTokenComprehensive verifies token generation
func TestGenerateTokenComprehensive(t *testing.T) {
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

// TestGenerateTokenMethodNotAllowed verifies POST-only endpoint
func TestGenerateTokenMethodNotAllowed(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/token", nil)
	rr := httptest.NewRecorder()
	h.GenerateToken(rr, req)

	if rr.Code != http.StatusMethodNotAllowed {
		t.Fatalf("expected 405 got %d", rr.Code)
	}
}

// TestGenerateTokenInvalidBody verifies validation
func TestGenerateTokenInvalidBody(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodPost, "/token", strings.NewReader("invalid json"))
	rr := httptest.NewRecorder()
	h.GenerateToken(rr, req)

	if rr.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 got %d", rr.Code)
	}
}

// TestIntrospectValidToken verifies token validation
func TestIntrospectValidToken(t *testing.T) {
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

// TestIntrospectMissingToken verifies missing token handling
func TestIntrospectMissingToken(t *testing.T) {
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

// TestIntrospectInvalidTokenFormat verifies token format validation
func TestIntrospectInvalidTokenFormat(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/introspect", nil)
	req.Header.Set("Authorization", "InvalidFormat token123")
	rr := httptest.NewRecorder()
	h.Introspect(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 got %d", rr.Code)
	}
}

// TestIntrospectInvalidToken verifies invalid token handling
func TestIntrospectInvalidToken(t *testing.T) {
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

// TestIntrospectExpiredToken verifies expired token handling
func TestIntrospectExpiredToken(t *testing.T) {
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

// TestSecurityHeadersComprehensive verifies security headers are set
func TestSecurityHeadersComprehensive(t *testing.T) {
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
