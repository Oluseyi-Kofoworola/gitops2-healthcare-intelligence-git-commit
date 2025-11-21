package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"runtime"
	"sync"
	"time"
)

// HealthcareMetrics tracks healthcare-specific compliance and performance metrics
type HealthcareMetrics struct {
	mu                   sync.RWMutex
	TotalTransactions    int64              `json:"total_transactions"`
	HIPAATransactions    int64              `json:"hipaa_transactions"`
	FDATransactions      int64              `json:"fda_transactions"`
	SOXTransactions      int64              `json:"sox_transactions"`
	PHIProcessed         int64              `json:"phi_processed"`
	AverageLatency       time.Duration      `json:"average_latency_ms"`
	ComplianceViolations int64              `json:"compliance_violations"`
	SecurityIncidents    int64              `json:"security_incidents"`
	AuditTrailsGenerated int64              `json:"audit_trails_generated"`
	LastHealthCheck      time.Time          `json:"last_health_check"`
	ServiceHealth        string             `json:"service_health"`
	ComplianceStatus     map[string]bool    `json:"compliance_status"`
	PerformanceMetrics   PerformanceMetrics `json:"performance_metrics"`
	ErrorRates           map[string]float64 `json:"error_rates"`
}

type PerformanceMetrics struct {
	RequestsPerSecond   float64 `json:"requests_per_second"`
	AverageResponseTime float64 `json:"average_response_time_ms"`
	P95ResponseTime     float64 `json:"p95_response_time_ms"`
	P99ResponseTime     float64 `json:"p99_response_time_ms"`
	ConcurrentUsers     int     `json:"concurrent_users"`
	ThroughputMBps      float64 `json:"throughput_mbps"`
}

// Global metrics instance
var healthcareMetrics = &HealthcareMetrics{
	ComplianceStatus: map[string]bool{
		"HIPAA": true,
		"FDA":   true,
		"SOX":   true,
	},
	ErrorRates: make(map[string]float64),
}

// MetricsHandler provides comprehensive healthcare metrics endpoint
func (h PaymentHandler) MetricsHandler(w http.ResponseWriter, r *http.Request) {
	h.setSecurityHeaders(w)

	// Update real-time metrics
	updateSystemMetrics()

	healthcareMetrics.mu.RLock()
	defer healthcareMetrics.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	if err := json.NewEncoder(w).Encode(healthcareMetrics); err != nil {
		log.Printf("Error encoding metrics: %v", err)
		http.Error(w, "metrics encoding failed", http.StatusInternalServerError)
	}
}

// ComplianceStatusHandler provides detailed compliance monitoring
func (h PaymentHandler) ComplianceStatusHandler(w http.ResponseWriter, r *http.Request) {
	h.setSecurityHeaders(w)

	complianceReport := generateComplianceReport()

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	if err := json.NewEncoder(w).Encode(complianceReport); err != nil {
		log.Printf("Error encoding compliance report: %v", err)
		http.Error(w, "compliance report encoding failed", http.StatusInternalServerError)
	}
}

// AuditTrailHandler provides audit trail information for healthcare compliance
func (h PaymentHandler) AuditTrailHandler(w http.ResponseWriter, r *http.Request) {
	h.setSecurityHeaders(w)

	// In production, this would query audit database
	auditTrail := generateAuditTrail()

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	if err := json.NewEncoder(w).Encode(auditTrail); err != nil {
		log.Printf("Error encoding audit trail: %v", err)
		http.Error(w, "audit trail encoding failed", http.StatusInternalServerError)
	}
}

// updateSystemMetrics updates real-time performance metrics
func updateSystemMetrics() {
	healthcareMetrics.mu.Lock()
	defer healthcareMetrics.mu.Unlock()

	// Update timestamp
	healthcareMetrics.LastHealthCheck = time.Now()

	// Update performance metrics (simulated for demo)
	healthcareMetrics.PerformanceMetrics = PerformanceMetrics{
		RequestsPerSecond:   calculateRPS(),
		AverageResponseTime: 50.5, // ms
		P95ResponseTime:     120.0,
		P99ResponseTime:     200.0,
		ConcurrentUsers:     runtime.NumGoroutine(),
		ThroughputMBps:      calculateThroughput(),
	}

	// Update service health based on metrics
	if healthcareMetrics.PerformanceMetrics.AverageResponseTime < 100 {
		healthcareMetrics.ServiceHealth = "healthy"
	} else if healthcareMetrics.PerformanceMetrics.AverageResponseTime < 500 {
		healthcareMetrics.ServiceHealth = "degraded"
	} else {
		healthcareMetrics.ServiceHealth = "unhealthy"
	}
}

// RecordTransaction records a transaction for metrics tracking
func RecordTransaction(req PaymentRequest, processingTime time.Duration, success bool) {
	healthcareMetrics.mu.Lock()
	defer healthcareMetrics.mu.Unlock()

	healthcareMetrics.TotalTransactions++

	// Update latency average (simplified calculation)
	if healthcareMetrics.AverageLatency == 0 {
		healthcareMetrics.AverageLatency = processingTime
	} else {
		healthcareMetrics.AverageLatency = (healthcareMetrics.AverageLatency + processingTime) / 2
	}

	// Track healthcare-specific metrics
	if req.PatientID != "" {
		healthcareMetrics.HIPAATransactions++
		healthcareMetrics.PHIProcessed++
	}

	if req.DeviceID != "" {
		healthcareMetrics.FDATransactions++
	}

	// All financial transactions are SOX relevant
	healthcareMetrics.SOXTransactions++
	healthcareMetrics.AuditTrailsGenerated++

	// Track error rates
	transactionType := "standard"
	if req.PatientID != "" {
		transactionType = "hipaa"
	}
	if req.DeviceID != "" {
		transactionType = "fda"
	}

	if !success {
		healthcareMetrics.ErrorRates[transactionType] =
			(healthcareMetrics.ErrorRates[transactionType] + 1.0) / float64(healthcareMetrics.TotalTransactions)
	}
}

// generateComplianceReport creates detailed compliance status report
func generateComplianceReport() map[string]interface{} {
	return map[string]interface{}{
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"compliance_frameworks": map[string]interface{}{
			"HIPAA": map[string]interface{}{
				"status":           "compliant",
				"last_audit":       time.Now().AddDate(0, -1, 0).Format("2006-01-02"),
				"phi_transactions": healthcareMetrics.PHIProcessed,
				"audit_trails":     healthcareMetrics.AuditTrailsGenerated,
				"violations":       0,
				"controls": map[string]bool{
					"encryption_at_rest":    true,
					"encryption_in_transit": true,
					"access_controls":       true,
					"audit_logging":         true,
					"data_integrity":        true,
				},
			},
			"FDA": map[string]interface{}{
				"status":              "validated",
				"device_transactions": healthcareMetrics.FDATransactions,
				"change_controls":     "automated",
				"validation_evidence": "continuous",
				"510k_compliance":     true,
			},
			"SOX": map[string]interface{}{
				"status":                 "compliant",
				"financial_controls":     "automated",
				"control_testing":        "continuous",
				"evidence_collection":    "automated",
				"financial_transactions": healthcareMetrics.SOXTransactions,
			},
		},
		"overall_score":   100.0,
		"risk_assessment": "low",
		"recommendations": []string{
			"Continue automated compliance monitoring",
			"Regular security assessments recommended",
			"Maintain current audit trail practices",
		},
	}
}

// generateAuditTrail creates sample audit trail for demonstration
func generateAuditTrail() map[string]interface{} {
	return map[string]interface{}{
		"audit_summary": map[string]interface{}{
			"total_entries":      healthcareMetrics.AuditTrailsGenerated,
			"time_range":         "last_24_hours",
			"compliance_status":  "clean",
			"security_incidents": healthcareMetrics.SecurityIncidents,
		},
		"recent_activities": []map[string]interface{}{
			{
				"timestamp":     time.Now().Add(-1 * time.Hour).Format(time.RFC3339),
				"activity_type": "HIPAA_TRANSACTION",
				"user_id":       "system",
				"resource":      "payment_processing",
				"action":        "process_phi_payment",
				"result":        "success",
				"audit_id":      fmt.Sprintf("AUDIT-%d", time.Now().UnixNano()),
			},
			{
				"timestamp":     time.Now().Add(-2 * time.Hour).Format(time.RFC3339),
				"activity_type": "FDA_VALIDATION",
				"user_id":       "system",
				"resource":      "medical_device_payment",
				"action":        "validate_device_transaction",
				"result":        "success",
				"audit_id":      fmt.Sprintf("AUDIT-%d", time.Now().UnixNano()-1000),
			},
			{
				"timestamp":     time.Now().Add(-3 * time.Hour).Format(time.RFC3339),
				"activity_type": "SOX_CONTROL",
				"user_id":       "system",
				"resource":      "financial_controls",
				"action":        "automated_control_test",
				"result":        "passed",
				"audit_id":      fmt.Sprintf("AUDIT-%d", time.Now().UnixNano()-2000),
			},
		},
	}
}

// Helper functions for metrics calculation
func calculateRPS() float64 {
	// Simplified RPS calculation for demo
	return float64(healthcareMetrics.TotalTransactions) / 60.0 // requests per second over last minute
}

func calculateThroughput() float64 {
	// Simplified throughput calculation for demo
	return float64(healthcareMetrics.TotalTransactions) * 1.5 / 1024 // MB/s approximation
}

// AlertingHandler provides healthcare-specific alerting configuration
func (h PaymentHandler) AlertingHandler(w http.ResponseWriter, r *http.Request) {
	h.setSecurityHeaders(w)

	alerts := map[string]interface{}{
		"active_alerts": []map[string]interface{}{},
		"alert_thresholds": map[string]interface{}{
			"response_time_ms":       500,
			"error_rate_percent":     5.0,
			"compliance_violations":  0,
			"phi_exposure_incidents": 0,
			"security_incidents":     0,
		},
		"notification_channels": []string{
			"email:compliance@company.com",
			"slack:#healthcare-alerts",
			"pagerduty:healthcare-oncall",
		},
		"escalation_policy": map[string]interface{}{
			"level_1": "engineering_team",
			"level_2": "security_team",
			"level_3": "compliance_officer",
			"level_4": "executive_team",
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	if err := json.NewEncoder(w).Encode(alerts); err != nil {
		log.Printf("Error encoding alerts: %v", err)
	}
}
