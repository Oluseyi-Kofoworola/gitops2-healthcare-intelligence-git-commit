package main

import (
	"testing"
	"time"
)

func TestValidateApprovalLevel(t *testing.T) {
	mgr := &SOXFinancialControlManager{}

	table := []struct {
		amount float64
		level  string
		ok     bool
	}{
		{999, "STAFF_LEVEL", true},
		{1000, "STAFF_LEVEL", false},
		{1000, "MANAGER_LEVEL", true},
		{9999, "MANAGER_LEVEL", true},
		{10000, "MANAGER_LEVEL", false},
		{10000, "DIRECTOR_LEVEL", true},
		{99999, "DIRECTOR_LEVEL", true},
		{100000, "DIRECTOR_LEVEL", false},
		{100000, "VP_LEVEL", true},
		{999999, "VP_LEVEL", true},
		{1000000, "VP_LEVEL", false},
		{1000000, "C_LEVEL", true},
	}

	for _, tc := range table {
		err := mgr.validateApprovalLevel(tc.amount, tc.level)
		if tc.ok && err != nil {
			t.Fatalf("amount %.0f with %s expected ok, got err %v", tc.amount, tc.level, err)
		}
		if !tc.ok && err == nil {
			t.Fatalf("amount %.0f with %s expected error", tc.amount, tc.level)
		}
	}
}

func TestProcessFinancialTransactionSegregation(t *testing.T) {
	mgr := &SOXFinancialControlManager{}

	txn := FinancialTransaction{
		TransactionID: "TX-1",
		Amount:        15000,
		Currency:      "USD",
		AccountFrom:   "A",
		AccountTo:     "B",
		Timestamp:     time.Now(),
		ApprovalLevel: "DIRECTOR_LEVEL",
		ApproverID:    "approver-1",
		Description:   "payment",
		ControlNumber: "CTRL-1",
	}

	// violation: same initiator and approver
	if err := mgr.ProcessFinancialTransaction(txn, "u1", "u1"); err == nil {
		t.Fatalf("expected segregation of duties violation")
	}

	// success: different approver
	if err := mgr.ProcessFinancialTransaction(txn, "u1", "u2"); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(mgr.AuditTrails) == 0 {
		t.Fatalf("expected audit trails recorded")
	}
}

func TestGenerateSOXComplianceReport(t *testing.T) {
	mgr := &SOXFinancialControlManager{}

	// seed some trails
	mgr.logAuditTrail("TX-1", "INITIATED", "u1", "seed")
	mgr.logAuditTrail("TX-1", "VIOLATION", "u1", "seed viol")
	mgr.logAuditTrail("TX-2", "APPROVED", "u2", "seed ok")

	start := time.Now().Add(-1 * time.Hour)
	end := time.Now().Add(1 * time.Hour)

	report := mgr.GenerateSOXComplianceReport(start, end)
	if report["total_transactions"].(int) == 0 {
		t.Fatalf("expected transactions counted")
	}
}
