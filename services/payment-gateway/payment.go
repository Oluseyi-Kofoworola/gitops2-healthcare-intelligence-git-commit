package main

import (
	"errors"
	"time"
)

type PaymentRequest struct {
	AmountCents int64  `json:"amount_cents"`
	Currency    string `json:"currency"`
	CustomerID  string `json:"customer_id"`
	Method      string `json:"method"`
}

type PaymentResponse struct {
	Status      string `json:"status"`
	AuthCode    string `json:"auth_code"`
	ProcessedAt int64  `json:"processed_at_unix"`
	HighValue   bool   `json:"high_value,omitempty"` // Added for high-value payment tracking
}

// ProcessPayment simulates payment authorization.
// In a real system, this would call PSPs, fraud checks, ledgers, etc.
func ProcessPayment(req PaymentRequest, maxLatency time.Duration) (PaymentResponse, error) {
	if req.AmountCents <= 0 {
		return PaymentResponse{}, errors.New("invalid amount")
	}
	if req.Currency == "" || req.CustomerID == "" || req.Method == "" {
		return PaymentResponse{}, errors.New("missing required fields")
	}

	// Simulate processing time (bounded by maxLatency)
	sleep := maxLatency / 4
	if sleep <= 0 {
		sleep = 10 * time.Millisecond
	}
	time.Sleep(sleep)

	resp := PaymentResponse{
		Status:      "authorized",
		AuthCode:    "AUTH-" + time.Now().Format("150405"),
		ProcessedAt: time.Now().Unix(),
		HighValue:   req.AmountCents >= 10000, // Set high-value flag for amounts >= $100
	}
	return resp, nil
}
