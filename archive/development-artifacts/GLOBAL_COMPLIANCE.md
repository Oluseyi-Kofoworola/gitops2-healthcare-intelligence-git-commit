# Global Multi-Region Compliance Framework
## GDPR (Europe), UK-DPA (United Kingdom), APAC Privacy Laws

## Overview
This document extends the GitOps 2.0 Healthcare Intelligence Platform to support **global compliance frameworks** beyond U.S. regulations (HIPAA, FDA, SOX). It demonstrates how the platform adapts to GDPR (Europe), UK-DPA (United Kingdom), and APAC privacy laws (Asia-Pacific).

---

## 🌍 Supported Jurisdictions

| Region | Regulation | Status | Effective Date |
|--------|-----------|--------|---------------|
| **United States** | HIPAA, FDA CFR 21, SOX | ✅ Operational | 2024-01-01 |
| **European Union** | GDPR | ✅ Implemented | 2024-02-01 |
| **United Kingdom** | UK-DPA, NHS Data Security | ✅ Implemented | 2024-02-01 |
| **Asia-Pacific** | APAC Privacy Laws | ✅ Implemented | 2024-02-15 |
| **Canada** | PIPEDA | 🔜 Planned Q2 | 2024-04-01 |
| **Australia** | Privacy Act 1988 | 🔜 Planned Q2 | 2024-04-01 |
| **Singapore** | PDPA | 🔜 Planned Q2 | 2024-04-01 |

---

## 🇪🇺 GDPR Compliance (European Union)

### Key Regulatory Requirements

**Regulation:** General Data Protection Regulation (GDPR)  
**Effective:** May 25, 2018  
**Scope:** Personal data of EU residents  
**Penalties:** Up to €20M or 4% of global annual turnover (whichever is higher)

**Core Principles:**
1. **Lawfulness, Fairness, Transparency** (Art. 5.1.a)
2. **Data Minimization** (Art. 5.1.c)
3. **Purpose Limitation** (Art. 5.1.b)
4. **Storage Limitation** (Art. 5.1.e)
5. **Integrity & Confidentiality** (Art. 5.1.f)
6. **Accountability** (Art. 5.2)

### OPA Policy: GDPR Data Protection

**File:** `policies/global/gdpr_data_protection.rego`

```rego
package global.gdpr

import rego.v1

# METADATA
# title: GDPR Data Protection Policy
# description: Enforces GDPR compliance for commits affecting personal data processing
# authors:
#   - Platform Engineering Team
# scope: package
# schemas:
#   - input: schema.commit_input

##############################################################################
# GDPR Compliance Requirements
##############################################################################

# Article 5.1.f: Integrity and confidentiality
# Personal data must be processed securely using appropriate technical measures

deny contains msg if {
    affects_personal_data
    not has_encryption_controls
    msg := "GDPR Art. 5.1.f violation: Personal data processing must implement encryption controls"
}

# Article 32: Security of processing
# Pseudonymization and encryption of personal data required

deny contains msg if {
    affects_personal_data
    not has_pseudonymization
    msg := "GDPR Art. 32 violation: Personal data must be pseudonymized or anonymized"
}

# Article 25: Data protection by design and by default
# Privacy-enhancing technologies must be implemented

deny contains msg if {
    is_new_data_processing_feature
    not has_privacy_impact_assessment
    msg := "GDPR Art. 25 violation: New data processing features require Privacy Impact Assessment (PIA)"
}

# Article 33: Breach notification
# Data breaches must be logged and reported within 72 hours

deny contains msg if {
    affects_personal_data
    not has_breach_detection_logging
    msg := "GDPR Art. 33 violation: Personal data processing must implement breach detection and logging"
}

# Article 17: Right to erasure ("Right to be forgotten")
# Systems must support data deletion on request

deny contains msg if {
    creates_new_data_storage
    not has_deletion_mechanism
    msg := "GDPR Art. 17 violation: Data storage must implement erasure mechanism for 'right to be forgotten'"
}

# Article 20: Right to data portability
# Data must be exportable in structured, machine-readable format

deny contains msg if {
    creates_new_data_storage
    not has_data_export_api
    msg := "GDPR Art. 20 violation: Data storage must provide export API for data portability"
}

##############################################################################
# Helper Rules
##############################################################################

affects_personal_data if {
    some file in input.files
    contains(file.path, "personal-data")
}

affects_personal_data if {
    some file in input.files
    regex.match(`(?i)(pii|personal.*info|user.*data|customer.*data)`, file.content)
}

has_encryption_controls if {
    some file in input.files
    regex.match(`(?i)(encrypt|aes-256|rsa|crypto)`, file.content)
}

has_pseudonymization if {
    some file in input.files
    regex.match(`(?i)(pseudonymize|anonymize|hash|tokenize)`, file.content)
}

has_privacy_impact_assessment if {
    # Check commit metadata for PIA reference
    regex.match(`(?i)PIA-\d{4}-\d{3}`, input.commit.message)
}

has_privacy_impact_assessment if {
    # Check for PIA documentation file
    some file in input.files
    regex.match(`(?i)privacy.*impact.*assessment`, file.path)
}

is_new_data_processing_feature if {
    regex.match(`(?i)^feat\(.*data.*\):`, input.commit.message)
}

has_breach_detection_logging if {
    some file in input.files
    regex.match(`(?i)(audit.*log|security.*monitor|breach.*detect)`, file.content)
}

creates_new_data_storage if {
    some file in input.files
    regex.match(`(?i)(database|storage|repository|data.*store)`, file.path)
}

has_deletion_mechanism if {
    some file in input.files
    regex.match(`(?i)(delete|erase|remove.*user|forget)`, file.content)
}

has_data_export_api if {
    some file in input.files
    regex.match(`(?i)(export|download.*data|api/v\d+/data)`, file.content)
}

##############################################################################
# Required Metadata for GDPR Commits
##############################################################################

# GDPR requires specific metadata in commit messages
gdpr_metadata_required contains field if {
    affects_personal_data
    required_fields := [
        "GDPR-Compliance",
        "Data-Category",
        "Legal-Basis",
        "Data-Retention",
        "Privacy-Impact"
    ]
    some field in required_fields
    not has_metadata_field(field)
}

deny contains msg if {
    count(gdpr_metadata_required) > 0
    msg := sprintf(
        "GDPR compliance metadata missing: %v. Required fields for personal data processing.",
        [gdpr_metadata_required]
    )
}

has_metadata_field(field) if {
    regex.match(sprintf(`(?i)%s:`, [field]), input.commit.message)
}

##############################################################################
# Data Subject Rights Enforcement
##############################################################################

# Article 15: Right of access
# Systems must support data access requests

deny contains msg if {
    creates_new_data_storage
    not has_access_request_api
    msg := "GDPR Art. 15 violation: Data storage must provide access request API"
}

has_access_request_api if {
    some file in input.files
    regex.match(`(?i)(access.*request|data.*subject.*request|dsr)`, file.content)
}

##############################################################################
# Cross-Border Data Transfer
##############################################################################

# Article 44-50: International data transfers
# Data transfers outside EU require adequate safeguards

deny contains msg if {
    transfers_data_outside_eu
    not has_transfer_safeguards
    msg := "GDPR Art. 44-50 violation: Cross-border data transfer requires Standard Contractual Clauses (SCC) or adequacy decision"
}

transfers_data_outside_eu if {
    some file in input.files
    regex.match(`(?i)(aws.*us-east|azure.*eastus|gcp.*us-central)`, file.content)
}

has_transfer_safeguards if {
    # Check for Standard Contractual Clauses reference
    regex.match(`(?i)(SCC|standard.*contractual.*clauses|adequacy.*decision)`, input.commit.message)
}

##############################################################################
# Testing Requirements
##############################################################################

# GDPR-related changes require specific testing
required_tests contains test if {
    affects_personal_data
    gdpr_tests := [
        "Data encryption validation",
        "Pseudonymization verification",
        "Data deletion testing (right to be forgotten)",
        "Data export testing (data portability)",
        "Access control verification",
        "Audit logging validation"
    ]
    some test in gdpr_tests
}

##############################################################################
# Suggested Reviewers
##############################################################################

required_reviewers contains reviewer if {
    affects_personal_data
    reviewers := ["@dpo", "@privacy-team", "@legal-team", "@security-team"]
    some reviewer in reviewers
}

# DPO (Data Protection Officer) required for HIGH impact
deny contains msg if {
    affects_personal_data
    input.risk_level == "HIGH"
    not has_dpo_approval
    msg := "GDPR compliance: Data Protection Officer (DPO) approval required for HIGH risk personal data changes"
}

has_dpo_approval if {
    some reviewer in input.reviewers
    reviewer == "@dpo"
}
```

### GDPR Commit Example

```
security(gdpr): implement pseudonymization for EU customer data

Business Impact: CRITICAL - GDPR compliance enhancement for EU region
Compliance: GDPR Art. 5.1.f, Art. 32, Art. 25

GDPR Compliance:
  Data-Category: Personal Identifiable Information (PII) - Customer names, emails
  Legal-Basis: Legitimate interest (Art. 6.1.f) - Service delivery
  Data-Retention: 24 months post-account-closure
  Privacy-Impact: HIGH - Implements pseudonymization layer
  Cross-Border-Transfer: NO - Data remains in EU region (eu-west-1)
  Privacy-Impact-Assessment: PIA-2024-012 (approved by DPO)

Technical Details:
  - Implemented SHA-256 hashing for customer identifiers
  - Added encryption at rest (AES-256-GCM)
  - Created data export API endpoint (Art. 20 - Data portability)
  - Implemented deletion mechanism (Art. 17 - Right to be forgotten)
  - Added audit logging for all data access (Art. 33 - Breach detection)

Data Subject Rights Implemented:
  - Right of access (Art. 15): GET /api/v1/gdpr/access-request
  - Right to erasure (Art. 17): DELETE /api/v1/gdpr/delete-request
  - Right to data portability (Art. 20): GET /api/v1/gdpr/export-data

Risk Level: HIGH
Testing:
  - Data encryption validation
  - Pseudonymization verification
  - Data deletion testing (right to be forgotten)
  - Data export testing (data portability)
  - Access control verification
  - Audit logging validation
  - GDPR compliance scan (DPO review)

Validation: Privacy Impact Assessment PIA-2024-012 approved
Reviewers: @dpo, @privacy-team, @legal-team, @security-team, @eu-compliance-team

References:
  - GDPR Art. 5.1.f (Integrity and confidentiality)
  - GDPR Art. 32 (Security of processing)
  - GDPR Art. 25 (Data protection by design)
  - ICO Guidance: Pseudonymization (2023)

AI Model: GPT-4-Turbo (gdpr-compliance-v1.2)
Generation Time: 9.3s
Confidence: 96%
```

---

## 🇬🇧 UK-DPA Compliance (United Kingdom)

### Key Regulatory Requirements

**Regulation:** UK Data Protection Act 2018 + UK GDPR  
**Effective:** January 31, 2020 (post-Brexit)  
**Scope:** Personal data of UK residents  
**Penalties:** Up to £17.5M or 4% of global annual turnover

**Key Differences from EU GDPR:**
1. **NHS Data Security Standards** (healthcare-specific)
2. **ICO (Information Commissioner's Office)** as regulator
3. **National security exemptions** (broader than EU)
4. **UK-specific adequacy decisions** for international transfers

### OPA Policy: UK-DPA Healthcare

**File:** `policies/global/uk_dpa_healthcare.rego`

```rego
package global.uk_dpa

import rego.v1

# METADATA
# title: UK Data Protection Act & NHS Data Security Standards
# description: Enforces UK-DPA and NHS-specific compliance requirements
# authors:
#   - Platform Engineering Team
# scope: package

##############################################################################
# NHS Data Security Standards (Healthcare-Specific)
##############################################################################

# NHS DSPT (Data Security and Protection Toolkit) requirements

deny contains msg if {
    affects_nhs_patient_data
    not has_nhs_number_protection
    msg := "UK NHS DSPT violation: NHS numbers must be encrypted and access-controlled"
}

deny contains msg if {
    affects_nhs_patient_data
    not has_nhs_audit_trail
    msg := "UK NHS DSPT violation: All NHS patient data access must be audit-logged"
}

# NHS Data Security Standard 1: Staff responsibilities
deny contains msg if {
    affects_nhs_patient_data
    not has_role_based_access_control
    msg := "UK NHS Standard 1 violation: Role-based access control (RBAC) required for NHS data"
}

# NHS Data Security Standard 2: Secure system access
deny contains msg if {
    affects_nhs_patient_data
    not has_multi_factor_authentication
    msg := "UK NHS Standard 2 violation: Multi-factor authentication (MFA) required for NHS data access"
}

##############################################################################
# UK-DPA Specific Requirements
##############################################################################

# UK GDPR Article 9: Special category data (health data)
deny contains msg if {
    affects_health_data_uk
    not has_explicit_consent_mechanism
    msg := "UK-DPA Art. 9 violation: Health data processing requires explicit consent mechanism"
}

# ICO Code of Practice: Anonymisation
deny contains msg if {
    shares_data_for_research
    not has_anonymization_validation
    msg := "ICO Code violation: Data shared for research must be anonymized per ICO guidelines"
}

##############################################################################
# Helper Rules
##############################################################################

affects_nhs_patient_data if {
    some file in input.files
    regex.match(`(?i)(nhs.*number|patient.*nhs)`, file.content)
}

has_nhs_number_protection if {
    some file in input.files
    regex.match(`(?i)(encrypt.*nhs|mask.*nhs.*number)`, file.content)
}

has_nhs_audit_trail if {
    some file in input.files
    regex.match(`(?i)(nhs.*audit|patient.*access.*log)`, file.content)
}

has_role_based_access_control if {
    some file in input.files
    regex.match(`(?i)(rbac|role.*based.*access|permission.*matrix)`, file.content)
}

has_multi_factor_authentication if {
    some file in input.files
    regex.match(`(?i)(mfa|multi.*factor|two.*factor|2fa)`, file.content)
}

affects_health_data_uk if {
    some file in input.files
    regex.match(`(?i)(health.*record|medical.*data|diagnosis|prescription)`, file.content)
    input.region == "uk"
}

has_explicit_consent_mechanism if {
    some file in input.files
    regex.match(`(?i)(consent.*form|explicit.*consent|opt-in)`, file.content)
}

shares_data_for_research if {
    regex.match(`(?i)(research|clinical.*trial|study)`, input.commit.message)
}

has_anonymization_validation if {
    some file in input.files
    regex.match(`(?i)(k-anonymity|l-diversity|differential.*privacy)`, file.content)
}

##############################################################################
# Required Metadata
##############################################################################

uk_dpa_metadata_required contains field if {
    affects_nhs_patient_data
    required_fields := [
        "UK-DPA-Compliance",
        "NHS-DSPT-Standard",
        "ICO-Registration",
        "Data-Protection-Impact-Assessment"
    ]
    some field in required_fields
    not has_metadata_field(field)
}

deny contains msg if {
    count(uk_dpa_metadata_required) > 0
    msg := sprintf(
        "UK-DPA compliance metadata missing: %v",
        [uk_dpa_metadata_required]
    )
}

has_metadata_field(field) if {
    regex.match(sprintf(`(?i)%s:`, [field]), input.commit.message)
}

##############################################################################
# Caldicott Principles (NHS Healthcare Ethics)
##############################################################################

# Principle 1: Justify the purpose
deny contains msg if {
    affects_nhs_patient_data
    not has_justified_purpose
    msg := "Caldicott Principle 1 violation: Purpose for NHS patient data use must be justified in commit message"
}

has_justified_purpose if {
    regex.match(`(?i)(Business Impact:|Purpose:)`, input.commit.message)
}

# Principle 2: Don't use patient data unless absolutely necessary
deny contains msg if {
    accesses_full_patient_record
    not has_data_minimization_justification
    msg := "Caldicott Principle 2 violation: Full patient record access requires data minimization justification"
}

accesses_full_patient_record if {
    some file in input.files
    regex.match(`(?i)(select \*|get.*all.*patient.*data)`, file.content)
}

has_data_minimization_justification if {
    regex.match(`(?i)(data.*minimization|minimum.*necessary)`, input.commit.message)
}

##############################################################################
# Required Reviewers
##############################################################################

required_reviewers contains reviewer if {
    affects_nhs_patient_data
    reviewers := ["@caldicott-guardian", "@uk-dpo", "@nhs-compliance-team"]
    some reviewer in reviewers
}
```

### UK-DPA Commit Example

```
security(uk-nhs): implement NHS number encryption and Caldicott compliance

Business Impact: CRITICAL - UK NHS data protection enhancement
Compliance: UK-DPA, NHS DSPT, Caldicott Principles

UK-DPA Compliance:
  NHS-DSPT-Standard: Standards 1, 2, 6 (Staff responsibilities, Secure access, Audit)
  ICO-Registration: Z1234567 (Healthcare data controller)
  Data-Protection-Impact-Assessment: DPIA-UK-2024-008 (approved by Caldicott Guardian)
  Legal-Basis: Article 9(2)(h) - Healthcare provision

Caldicott Principles:
  Principle-1-Purpose: Patient safety - Secure NHS number handling for prescriptions
  Principle-2-Minimization: Only NHS number and prescription data accessed (not full record)
  Principle-3-Access: Role-based access control (Pharmacist, GP, Consultant only)
  Principle-7-Duty: Caldicott Guardian approval obtained

Technical Details:
  - Implemented NHS number encryption (AES-256-GCM with NHS-specific key)
  - Added role-based access control (RBAC) for NHS data
  - Implemented multi-factor authentication (MFA) for system access
  - Created audit trail for all NHS number access
  - Added anonymization for research data sharing

NHS Data Security Standards:
  - Standard 1: Role-based access (Pharmacist, GP, Consultant roles defined)
  - Standard 2: MFA enabled (TOTP + biometric)
  - Standard 6: Audit logging (CloudWatch + NHS audit export)

Risk Level: HIGH
Testing:
  - NHS number encryption validation
  - RBAC verification (role matrix testing)
  - MFA integration testing
  - Audit trail validation
  - ICO anonymization compliance check
  - Caldicott Guardian review

Reviewers: @caldicott-guardian, @uk-dpo, @nhs-compliance-team, @security-team

References:
  - UK GDPR Article 9 (Special category data)
  - NHS DSPT Standards 1, 2, 6
  - Caldicott Principles (NHS Digital)
  - ICO Code of Practice on Anonymisation (2012)

AI Model: GPT-4-Turbo (uk-nhs-compliance-v1.1)
Generation Time: 10.1s
Confidence: 94%
```

---

## 🌏 APAC Privacy Laws (Asia-Pacific)

### Supported APAC Jurisdictions

| Country | Regulation | Key Requirements |
|---------|-----------|-----------------|
| **Singapore** | PDPA (Personal Data Protection Act) | Consent, purpose limitation, data breach notification |
| **Australia** | Privacy Act 1988 (APPs) | 13 Australian Privacy Principles |
| **Japan** | APPI (Act on Protection of Personal Information) | Purpose specification, cross-border transfer rules |
| **South Korea** | PIPA (Personal Information Protection Act) | Strictest in APAC - consent, encryption, breach notification |
| **Hong Kong** | PDPO (Personal Data Ordinance) | 6 Data Protection Principles |
| **New Zealand** | Privacy Act 2020 | 13 Privacy Principles |

### OPA Policy: APAC Privacy Compliance

**File:** `policies/global/apac_privacy.rego`

```rego
package global.apac

import rego.v1

# METADATA
# title: APAC Privacy Laws Compliance
# description: Enforces privacy compliance for Asia-Pacific jurisdictions
# authors:
#   - Platform Engineering Team
# scope: package

##############################################################################
# Singapore PDPA (Personal Data Protection Act)
##############################################################################

# PDPA Section 11: Consent obligation
deny contains msg if {
    input.region == "singapore"
    affects_personal_data
    not has_consent_mechanism
    msg := "Singapore PDPA Section 11 violation: Personal data collection requires explicit consent mechanism"
}

# PDPA Section 18: Purpose limitation
deny contains msg if {
    input.region == "singapore"
    uses_data_for_new_purpose
    not has_purpose_change_notification
    msg := "Singapore PDPA Section 18 violation: Using data for new purpose requires notification and consent"
}

# PDPA Section 26: Data breach notification (within 72 hours)
deny contains msg if {
    input.region == "singapore"
    affects_personal_data
    not has_breach_notification_mechanism
    msg := "Singapore PDPA Section 26 violation: Data breach notification mechanism required (72-hour deadline)"
}

##############################################################################
# Australia Privacy Act 1988 (Australian Privacy Principles - APPs)
##############################################################################

# APP 1: Open and transparent management of personal information
deny contains msg if {
    input.region == "australia"
    affects_personal_data
    not has_privacy_policy_reference
    msg := "Australia APP 1 violation: Privacy policy must be referenced for personal data handling"
}

# APP 11: Security of personal information
deny contains msg if {
    input.region == "australia"
    affects_personal_data
    not has_security_safeguards
    msg := "Australia APP 11 violation: Personal information must have appropriate security safeguards"
}

# APP 8: Cross-border disclosure
deny contains msg if {
    input.region == "australia"
    transfers_data_overseas
    not has_overseas_transfer_safeguards
    msg := "Australia APP 8 violation: Overseas data transfer requires accountability safeguards"
}

##############################################################################
# Japan APPI (Act on Protection of Personal Information)
##############################################################################

# APPI Article 15: Purpose of utilization
deny contains msg if {
    input.region == "japan"
    affects_personal_data
    not has_specified_purpose
    msg := "Japan APPI Art. 15 violation: Purpose of personal data utilization must be specified"
}

# APPI Article 23: Cross-border data transfer
deny contains msg if {
    input.region == "japan"
    transfers_data_outside_japan
    not has_japan_transfer_consent
    msg := "Japan APPI Art. 23 violation: Cross-border data transfer requires individual consent or adequate safeguards"
}

##############################################################################
# South Korea PIPA (Personal Information Protection Act)
##############################################################################

# PIPA Article 24: Encryption of personal information
deny contains msg if {
    input.region == "south_korea"
    stores_personal_data
    not has_korea_approved_encryption
    msg := "South Korea PIPA Art. 24 violation: Personal information must be encrypted with KISA-approved algorithms"
}

# PIPA Article 39: Breach notification (immediate)
deny contains msg if {
    input.region == "south_korea"
    affects_personal_data
    not has_immediate_breach_notification
    msg := "South Korea PIPA Art. 39 violation: Data breach notification must be immediate (no 72-hour grace period)"
}

##############################################################################
# Helper Rules
##############################################################################

affects_personal_data if {
    some file in input.files
    regex.match(`(?i)(personal.*data|pii|user.*info)`, file.content)
}

has_consent_mechanism if {
    some file in input.files
    regex.match(`(?i)(consent.*checkbox|opt-in|agree.*terms)`, file.content)
}

uses_data_for_new_purpose if {
    regex.match(`(?i)(repurpose|secondary.*use|new.*purpose)`, input.commit.message)
}

has_purpose_change_notification if {
    some file in input.files
    regex.match(`(?i)(purpose.*change.*notification|re-consent)`, file.content)
}

has_breach_notification_mechanism if {
    some file in input.files
    regex.match(`(?i)(breach.*notify|incident.*response|alert.*pdpc)`, file.content)
}

has_privacy_policy_reference if {
    regex.match(`(?i)(privacy.*policy|APP.*compliance)`, input.commit.message)
}

has_security_safeguards if {
    some file in input.files
    regex.match(`(?i)(encrypt|access.*control|security.*measure)`, file.content)
}

transfers_data_overseas if {
    some file in input.files
    regex.match(`(?i)(aws.*us-|azure.*eastus|cross.*border)`, file.content)
}

has_overseas_transfer_safeguards if {
    regex.match(`(?i)(transfer.*agreement|adequacy.*decision|binding.*rules)`, input.commit.message)
}

has_specified_purpose if {
    regex.match(`(?i)(Purpose:|Data.*usage:)`, input.commit.message)
}

transfers_data_outside_japan if {
    input.region == "japan"
    some file in input.files
    not regex.match(`(?i)(ap-northeast-1|japan)`, file.content)
}

has_japan_transfer_consent if {
    regex.match(`(?i)(cross.*border.*consent|APPI.*Art.*23.*compliance)`, input.commit.message)
}

stores_personal_data if {
    some file in input.files
    regex.match(`(?i)(database|storage|persist)`, file.path)
}

has_korea_approved_encryption if {
    some file in input.files
    # KISA-approved: AES, SEED, ARIA
    regex.match(`(?i)(aes-256|seed|aria)`, file.content)
}

has_immediate_breach_notification if {
    some file in input.files
    regex.match(`(?i)(immediate.*notify|real.*time.*alert|instant.*breach)`, file.content)
}

##############################################################################
# Required Metadata by Region
##############################################################################

apac_metadata_required contains field if {
    input.region in ["singapore", "australia", "japan", "south_korea"]
    affects_personal_data
    required_fields := [
        "APAC-Region",
        "Privacy-Framework",
        "Data-Localization",
        "Cross-Border-Transfer"
    ]
    some field in required_fields
    not has_metadata_field(field)
}

deny contains msg if {
    count(apac_metadata_required) > 0
    msg := sprintf(
        "APAC privacy compliance metadata missing: %v",
        [apac_metadata_required]
    )
}

has_metadata_field(field) if {
    regex.match(sprintf(`(?i)%s:`, [field]), input.commit.message)
}

##############################################################################
# Required Reviewers
##############################################################################

required_reviewers contains reviewer if {
    input.region == "singapore"
    affects_personal_data
    reviewers := ["@pdpc-officer", "@apac-compliance-team"]
    some reviewer in reviewers
}

required_reviewers contains reviewer if {
    input.region == "australia"
    affects_personal_data
    reviewers := ["@privacy-officer-au", "@oaic-compliance-team"]
    some reviewer in reviewers
}

required_reviewers contains reviewer if {
    input.region == "japan"
    affects_personal_data
    reviewers := ["@ppc-officer-jp", "@apac-compliance-team"]
    some reviewer in reviewers
}

required_reviewers contains reviewer if {
    input.region == "south_korea"
    affects_personal_data
    reviewers := ["@pipc-officer-kr", "@kisa-compliance-team"]
    some reviewer in reviewers
}
```

### APAC Commit Example (Singapore)

```
security(apac-sg): implement PDPA consent mechanism for Singapore users

Business Impact: CRITICAL - Singapore PDPA compliance for customer data
Compliance: Singapore PDPA Sections 11, 13, 18, 26

APAC Compliance:
  APAC-Region: Singapore
  Privacy-Framework: PDPA (Personal Data Protection Act 2012)
  Data-Localization: ap-southeast-1 (Singapore AWS region)
  Cross-Border-Transfer: NO - Data remains within Singapore jurisdiction
  PDPC-Registration: UEN202300123A (registered data controller)

Singapore PDPA Compliance:
  Section-11-Consent: Explicit opt-in checkbox implemented (granular consent)
  Section-13-Purpose: "Customer service and order fulfillment" (specified in consent form)
  Section-18-Purpose-Limitation: Notification mechanism for purpose changes
  Section-26-Breach-Notification: 72-hour breach notification to PDPC automated

Technical Details:
  - Implemented consent management UI (opt-in/opt-out granular controls)
  - Added purpose specification in data collection forms
  - Created data breach detection and PDPC notification API
  - Implemented data retention policy (24 months post-account-deletion)
  - Added withdrawal of consent mechanism (user dashboard)

Data Protection Measures:
  - Encryption: AES-256-GCM at rest, TLS 1.3 in transit
  - Access control: Role-based (customer service, admin, data analyst)
  - Audit logging: All data access logged to CloudWatch
  - Data minimization: Only collect necessary fields (name, email, phone)

Risk Level: HIGH
Testing:
  - Consent flow testing (opt-in, opt-out, withdrawal)
  - Purpose specification validation
  - Data breach notification simulation
  - PDPC compliance audit
  - Data localization verification (Singapore region only)

Validation: PDPC compliance review completed
Reviewers: @pdpc-officer, @apac-compliance-team, @legal-team-sg, @security-team

References:
  - Singapore PDPA 2012 (Sections 11, 13, 18, 26)
  - PDPC Guidelines on Consent (2019)
  - PDPC Data Breach Notification Guide (2021)

AI Model: GPT-4-Turbo (apac-pdpa-compliance-v1.0)
Generation Time: 11.2s
Confidence: 92%
```

---

## 🌐 Multi-Region Architecture

### Global Deployment Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GitOps 2.0 Global Platform                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
        ┌───────────────────────┴───────────────────────┐
        │                                               │
        ▼                                               ▼
┌──────────────────┐                           ┌──────────────────┐
│   US Region      │                           │   EU Region      │
│   (us-east-1)    │                           │   (eu-west-1)    │
├──────────────────┤                           ├──────────────────┤
│ • HIPAA          │                           │ • GDPR           │
│ • FDA CFR 21     │                           │ • GDPR Art. 5-50│
│ • SOX            │                           │ • Data residency │
│ • PHI storage    │                           │ • DPO oversight  │
└──────────────────┘                           └──────────────────┘
        │                                               │
        ▼                                               ▼
┌──────────────────┐                           ┌──────────────────┐
│   UK Region      │                           │  APAC Region     │
│   (eu-west-2)    │                           │  (ap-southeast-1)│
├──────────────────┤                           ├──────────────────┤
│ • UK-DPA         │                           │ • Singapore PDPA │
│ • NHS DSPT       │                           │ • Australia APPs │
│ • Caldicott      │                           │ • Japan APPI     │
│ • ICO compliance │                           │ • Korea PIPA     │
└──────────────────┘                           └──────────────────┘
```

### Data Residency Enforcement

**OPA Policy:** `policies/global/data_residency.rego`

```rego
package global.data_residency

import rego.v1

# Enforce data residency based on user region

deny contains msg if {
    stores_user_data
    target_region := get_deployment_region
    user_region := input.user_region
    
    not is_compliant_region(user_region, target_region)
    
    msg := sprintf(
        "Data residency violation: %s user data cannot be stored in %s region. Use %s.",
        [user_region, target_region, get_compliant_region(user_region)]
    )
}

is_compliant_region("eu", target) if {
    target in ["eu-west-1", "eu-central-1", "eu-north-1"]
}

is_compliant_region("uk", target) if {
    target == "eu-west-2"  # London region
}

is_compliant_region("singapore", target) if {
    target == "ap-southeast-1"
}

is_compliant_region("us", target) if {
    startswith(target, "us-")
}

get_deployment_region := region if {
    some file in input.files
    regex.match(sprintf(`region.*=.*"(%s)"`, [region]), file.content)
}

get_compliant_region("eu") := "eu-west-1 (Ireland) or eu-central-1 (Frankfurt)"
get_compliant_region("uk") := "eu-west-2 (London)"
get_compliant_region("singapore") := "ap-southeast-1 (Singapore)"
get_compliant_region("us") := "us-east-1 or us-west-2"

stores_user_data if {
    some file in input.files
    regex.match(`(?i)(user.*storage|customer.*database|personal.*data)`, file.content)
}
```

---

## 📊 Global Compliance Dashboard

### Multi-Region Metrics

| Region | Framework | Compliance Score | Incidents (30d) | Audit Status |
|--------|-----------|------------------|----------------|--------------|
| **US** | HIPAA/FDA/SOX | 100% ✅ | 0 | Passed (Q1 2024) |
| **EU** | GDPR | 100% ✅ | 0 | Passed (Q1 2024) |
| **UK** | UK-DPA/NHS | 100% ✅ | 0 | Passed (Q1 2024) |
| **Singapore** | PDPA | 98% 🟡 | 1 (minor) | In Progress |
| **Australia** | Privacy Act | 97% 🟡 | 2 (minor) | Scheduled Q2 |

**Global Average:** 99% compliance ✅

---

## 🚀 Roadmap: Future Jurisdictions

### Q2 2024
- 🔜 Canada (PIPEDA)
- 🔜 Australia (full APPs implementation)
- 🔜 Brazil (LGPD - Lei Geral de Proteção de Dados)

### Q3 2024
- 🔜 India (DPDPA - Digital Personal Data Protection Act)
- 🔜 South Africa (POPIA)
- 🔜 Middle East (UAE PDPL)

### Q4 2024
- 🔜 Latin America (Argentina, Mexico privacy laws)
- 🔜 Africa (Kenya, Nigeria data protection acts)

---

*Next: See `/policies/global/` directory for full OPA policy implementations*
