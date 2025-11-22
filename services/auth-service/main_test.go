package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealth(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rr := httptest.NewRecorder()
	h.Health(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", rr.Code)
	}
	var body map[string]string
	if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil {
		t.Fatalf("failed to parse body: %v", err)
	}
	if body["status"] != "ok" {
		t.Fatalf("unexpected status %s", body["status"])
	}
}

func TestIntrospect(t *testing.T) {
	h := AuthHandler{}
	req := httptest.NewRequest(http.MethodGet, "/introspect", nil)
	rr := httptest.NewRecorder()
	h.Introspect(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d", rr.Code)
	}
	var body map[string]any
	if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil {
		t.Fatalf("failed to parse body: %v", err)
	}
	if active, ok := body["active"].(bool); !ok || !active {
		t.Fatalf("expected active true")
	}
	if scopes, ok := body["scopes"].([]any); !ok || len(scopes) == 0 {
		t.Fatalf("expected scopes present")
	}
}

func TestStartAuthServer_Routes(t *testing.T) {
	srv := StartAuthServer(":0")
	h := srv.Handler

	// Health
	rr := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	h.ServeHTTP(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("health expected 200 got %d", rr.Code)
	}
	var body map[string]string
	if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil {
		t.Fatalf("failed decoding body: %v", err)
	}
	if body["status"] != "ok" {
		t.Fatalf("unexpected health body: %v", body)
	}

	// Introspect
	rr = httptest.NewRecorder()
	req = httptest.NewRequest(http.MethodGet, "/introspect", nil)
	h.ServeHTTP(rr, req)
	if rr.Code != http.StatusOK {
		t.Fatalf("introspect expected 200 got %d", rr.Code)
	}
}
