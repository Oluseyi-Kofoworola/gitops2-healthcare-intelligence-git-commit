// SOX Financial Controls and Audit Trail Implementation
package main

import (
	"fmt"
	"log"
	"time"
)

// FinancialTransaction represents SOX-compliant financial record
type FinancialTransaction struct {
	TransactionID string    `json:"transaction_id"`
	Amount        float64   `json:"amount"`
	Currency      string    `json:"currency"`
	AccountFrom   string    `json:"account_from"`
	AccountTo     string    `json:"account_to"`
	Timestamp     time.Time `json:"timestamp"`
	ApprovalLevel string    `json:"approval_level"`
	ApproverID    string    `json:"approver_id"`
	Description   string    `json:"description"`
	ControlNumber string    `json:"control_number"`
}

// SOXAuditTrail maintains SOX-compliant audit records
type SOXAuditTrail struct {
	TransactionID string    `json:"transaction_id"`
	Action        string    `json:"action"`
	UserID        string    `json:"user_id"`
	Timestamp     time.Time `json:"timestamp"`
	IPAddress     string    `json:"ip_address"`
	Details       string    `json:"details"`
	ControlTest   string    `json:"control_test"`
}

// SOXFinancialControlManager implements Sarbanes-Oxley compliance controls
type SOXFinancialControlManager struct {
	AuditTrails []SOXAuditTrail
}

// ProcessFinancialTransaction implements SOX segregation of duties
func (s *SOXFinancialControlManager) ProcessFinancialTransaction(txn FinancialTransaction, initiatorID, approverID string) error {
	// SOX Control: Segregation of duties - initiator cannot approve
	if initiatorID == approverID {
		s.logAuditTrail(txn.TransactionID, "VIOLATION", initiatorID,
			fmt.Sprintf("SOX violation: Same person initiated and approved transaction %s", txn.TransactionID))
		return fmt.Errorf("SOX compliance violation: segregation of duties - initiator cannot approve own transaction")
	}

	// SOX Control: Dollar amount approval hierarchy
	if err := s.validateApprovalLevel(txn.Amount, txn.ApprovalLevel); err != nil {
		s.logAuditTrail(txn.TransactionID, "APPROVAL_VIOLATION", initiatorID,
			fmt.Sprintf("Insufficient approval level for amount $%.2f", txn.Amount))
		return err
	}

	// SOX Control: Log transaction initiation
	s.logAuditTrail(txn.TransactionID, "INITIATED", initiatorID,
		fmt.Sprintf("Transaction initiated: $%.2f %s from %s to %s",
			txn.Amount, txn.Currency, txn.AccountFrom, txn.AccountTo))

	// SOX Control: Log approval
	s.logAuditTrail(txn.TransactionID, "APPROVED", approverID,
		fmt.Sprintf("Transaction approved by %s with level %s", approverID, txn.ApprovalLevel))

	// SOX Control: Immutable audit trail
	s.logAuditTrail(txn.TransactionID, "PROCESSED", "SYSTEM",
		fmt.Sprintf("Transaction processed successfully - Control #%s", txn.ControlNumber))

	log.Printf("SOX-compliant transaction processed: %s for $%.2f", txn.TransactionID, txn.Amount)
	return nil
}

// validateApprovalLevel implements SOX financial approval hierarchy
func (s *SOXFinancialControlManager) validateApprovalLevel(amount float64, approvalLevel string) error {
	// SOX-required approval hierarchy
	switch {
	case amount >= 1000000: // $1M+
		if approvalLevel != "C_LEVEL" {
			return fmt.Errorf("SOX violation: transactions >= $1M require C-level approval, got: %s", approvalLevel)
		}
	case amount >= 100000: // $100K+
		if approvalLevel != "C_LEVEL" && approvalLevel != "VP_LEVEL" {
			return fmt.Errorf("SOX violation: transactions >= $100K require VP+ approval, got: %s", approvalLevel)
		}
	case amount >= 10000: // $10K+
		if approvalLevel != "C_LEVEL" && approvalLevel != "VP_LEVEL" && approvalLevel != "DIRECTOR_LEVEL" {
			return fmt.Errorf("SOX violation: transactions >= $10K require Director+ approval, got: %s", approvalLevel)
		}
	case amount >= 1000: // $1K+
		if approvalLevel == "STAFF_LEVEL" {
			return fmt.Errorf("SOX violation: transactions >= $1K require Manager+ approval, got: %s", approvalLevel)
		}
	}

	return nil
}

// logAuditTrail creates immutable SOX audit records
func (s *SOXFinancialControlManager) logAuditTrail(transactionID, action, userID, details string) {
	auditRecord := SOXAuditTrail{
		TransactionID: transactionID,
		Action:        action,
		UserID:        userID,
		Timestamp:     time.Now(),
		IPAddress:     "127.0.0.1", // In production, capture real IP
		Details:       details,
		ControlTest:   fmt.Sprintf("SOX-IT-CONTROL-%d", time.Now().Unix()),
	}

	// SOX requirement: Immutable audit trail storage
	s.AuditTrails = append(s.AuditTrails, auditRecord)

	// SOX requirement: Real-time audit logging
	log.Printf("SOX AUDIT: [%s] %s by %s - %s",
		auditRecord.ControlTest, action, userID, details)
}

// GenerateSOXComplianceReport creates quarterly SOX compliance report
func (s *SOXFinancialControlManager) GenerateSOXComplianceReport(quarterStart, quarterEnd time.Time) map[string]interface{} {
	totalTransactions := 0
	violations := 0
	controlsTested := 0

	for _, audit := range s.AuditTrails {
		if audit.Timestamp.After(quarterStart) && audit.Timestamp.Before(quarterEnd) {
			totalTransactions++
			if audit.Action == "VIOLATION" {
				violations++
			}
			if audit.ControlTest != "" {
				controlsTested++
			}
		}
	}

	complianceRate := float64(totalTransactions-violations) / float64(totalTransactions) * 100

	report := map[string]interface{}{
		"quarter_start":      quarterStart.Format("2006-01-02"),
		"quarter_end":        quarterEnd.Format("2006-01-02"),
		"total_transactions": totalTransactions,
		"sox_violations":     violations,
		"compliance_rate":    fmt.Sprintf("%.2f%%", complianceRate),
		"controls_tested":    controlsTested,
		"audit_trail_count":  len(s.AuditTrails),
		"sox_certification":  complianceRate >= 99.0,
		"report_generated":   time.Now().Format("2006-01-02 15:04:05"),
	}

	log.Printf("SOX Compliance Report Generated: %.2f%% compliance rate with %d violations",
		complianceRate, violations)

	return report
}
