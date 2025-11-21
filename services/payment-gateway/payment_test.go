package main

import (
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
