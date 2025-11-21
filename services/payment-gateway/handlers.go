package main

import (
	"encoding/json"
	"net/http"
	"time"
)

type PaymentHandler struct {
    MaxLatency time.Duration
}

func (h PaymentHandler) Health(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    _ = json.NewEncoder(w).Encode(map[string]string{
        "status": "ok",
    })
}

func (h PaymentHandler) Charge(w http.ResponseWriter, r *http.Request) {
    defer r.Body.Close()

    var req PaymentRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "invalid payload", http.StatusBadRequest)
        return
    }

    resp, err := ProcessPayment(req, h.MaxLatency)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    _ = json.NewEncoder(w).Encode(resp)
}
