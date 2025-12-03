package healthcare.compliance_codes

# Valid Compliance Code Whitelists
# WHY: Prevent AI from hallucinating fake compliance references (e.g., "HIPAA-999", "FDA-IMAGINARY")
# WHAT: Authoritative lists of real compliance codes for validation

import future.keywords

# ==================================================================================
# HIPAA: Health Insurance Portability and Accountability Act
# ==================================================================================

valid_hipaa_sections := {
	# Administrative Safeguards (164.308)
	"164.308(a)(1)(i)",   # Security Management Process
	"164.308(a)(1)(ii)(A)", # Risk Analysis
	"164.308(a)(1)(ii)(B)", # Risk Management
	"164.308(a)(2)",      # Assigned Security Responsibility
	"164.308(a)(3)",      # Workforce Security
	"164.308(a)(4)",      # Information Access Management
	"164.308(a)(5)",      # Security Awareness Training
	"164.308(a)(6)",      # Security Incident Procedures
	"164.308(a)(7)",      # Contingency Plan
	"164.308(a)(8)",      # Evaluation
	"164.308(b)(1)",      # Business Associate Contracts
	
	# Physical Safeguards (164.310)
	"164.310(a)(1)",      # Facility Access Controls
	"164.310(a)(2)(i)",   # Contingency Operations
	"164.310(a)(2)(ii)",  # Facility Security Plan
	"164.310(a)(2)(iii)", # Access Control and Validation
	"164.310(a)(2)(iv)",  # Maintenance Records
	"164.310(b)",         # Workstation Use
	"164.310(c)",         # Workstation Security
	"164.310(d)(1)",      # Device and Media Controls
	"164.310(d)(2)(i)",   # Disposal
	"164.310(d)(2)(ii)",  # Media Re-use
	"164.310(d)(2)(iii)", # Accountability
	"164.310(d)(2)(iv)",  # Data Backup and Storage
	
	# Technical Safeguards (164.312)
	"164.312(a)(1)",      # Access Control
	"164.312(a)(2)(i)",   # Unique User Identification
	"164.312(a)(2)(ii)",  # Emergency Access Procedure
	"164.312(a)(2)(iii)", # Automatic Logoff
	"164.312(a)(2)(iv)",  # Encryption and Decryption
	"164.312(b)",         # Audit Controls
	"164.312(c)(1)",      # Integrity Controls
	"164.312(c)(2)",      # Mechanism to Authenticate ePHI
	"164.312(d)",         # Person or Entity Authentication
	"164.312(e)(1)",      # Transmission Security
	"164.312(e)(2)(i)",   # Integrity Controls
	"164.312(e)(2)(ii)",  # Encryption
	
	# Privacy Rule (164.502-164.514)
	"164.502(a)",         # Uses and Disclosures
	"164.506",            # Permitted Uses and Disclosures
	"164.508",            # Authorizations
	"164.510",            # Disclosures Requiring Opportunity to Agree
	"164.512",            # Permitted Disclosures
	"164.514(a)",         # De-identification
	"164.514(b)",         # Safe Harbor Method
	"164.514(e)",         # Limited Data Set
	
	# Breach Notification (164.400-164.414)
	"164.400",            # Breach Definition
	"164.404",            # Notification to Individuals
	"164.406",            # Notification to Media
	"164.408",            # Notification to HHS
	"164.410",            # Notification by Business Associates
	
	# Shorthand references (commonly used in commits)
	"HIPAA-SECURITY",
	"HIPAA-PRIVACY",
	"HIPAA-BREACH",
	"HIPAA-ADMIN",
	"HIPAA-PHYSICAL",
	"HIPAA-TECHNICAL",
}

# ==================================================================================
# FDA: Food and Drug Administration (21 CFR Part 11 & Device Regulations)
# ==================================================================================

valid_fda_codes := {
	# 21 CFR Part 11 - Electronic Records/Signatures
	"21CFR11",
	"21CFR11.10",         # Controls for Closed Systems
	"21CFR11.10(a)",      # Validation
	"21CFR11.10(b)",      # Ability to generate accurate copies
	"21CFR11.10(c)",      # Protection of records
	"21CFR11.10(d)",      # Limiting system access
	"21CFR11.10(e)",      # Audit trails
	"21CFR11.10(f)",      # Operational system checks
	"21CFR11.10(g)",      # Authority checks
	"21CFR11.10(h)",      # Device checks
	"21CFR11.10(i)",      # Education and training
	"21CFR11.30",         # Controls for Open Systems
	"21CFR11.50",         # Signature Manifestations
	"21CFR11.70",         # Signature/Record Linking
	"21CFR11.100",        # General Requirements (e-signatures)
	"21CFR11.200",        # Electronic Signature Components
	"21CFR11.300",        # Controls for Identification Codes/Passwords
	
	# Device Classifications
	"510(k)",             # Premarket Notification
	"FDA-510k",
	"FDA-510K",
	"PMA",                # Premarket Approval
	"FDA-PMA",
	"IDE",                # Investigational Device Exemption
	"FDA-IDE",
	"HDE",                # Humanitarian Device Exemption
	"FDA-HDE",
	
	# Quality System Regulation (21 CFR 820)
	"21CFR820",
	"21CFR820.30",        # Design Controls
	"21CFR820.70",        # Production and Process Controls
	"21CFR820.75",        # Process Validation
	"21CFR820.80",        # Receiving, In-Process, and Finished Device Acceptance
	"21CFR820.181",       # Device Master Record
	"21CFR820.184",       # Device History Record
	
	# Device Classes
	"CLASS-I",
	"CLASS-II",
	"CLASS-III",
	
	# Shorthand
	"FDA-DEVICE",
	"FDA-SOFTWARE",
	"FDA-QSR",
}

# ==================================================================================
# SOX: Sarbanes-Oxley Act (Financial Controls)
# ==================================================================================

valid_sox_sections := {
	# Key SOX Sections
	"SOX-302",            # Corporate Responsibility for Financial Reports
	"SOX-404",            # Management Assessment of Internal Controls
	"SOX-409",            # Real-Time Disclosure
	"SOX-802",            # Criminal Penalties for Document Destruction
	"SOX-806",            # Whistleblower Protection
	"SOX-906",            # Corporate Responsibility for Financial Reports (Criminal)
	
	# IT Controls (commonly referenced)
	"ITGC",               # IT General Controls
	"ITAC",               # IT Application Controls
	"SOX-ITGC",
	"SOX-ITAC",
	"SOX-ACCESS",
	"SOX-CHANGE",
	"SOX-OPERATIONS",
	
	# COBIT Framework (often used for SOX compliance)
	"COBIT-DS5",          # Ensure Systems Security
	"COBIT-AI7",          # Install and Accredit Solutions
	"COBIT-DS10",         # Manage Problems
	"COBIT-DS11",         # Manage Data
}

# ==================================================================================
# GDPR: General Data Protection Regulation
# ==================================================================================

valid_gdpr_articles := {
	# Key Articles
	"GDPR-ART5",          # Principles
	"GDPR-ART6",          # Lawfulness of Processing
	"GDPR-ART7",          # Conditions for Consent
	"GDPR-ART9",          # Special Categories (Sensitive Data)
	"GDPR-ART15",         # Right of Access
	"GDPR-ART16",         # Right to Rectification
	"GDPR-ART17",         # Right to Erasure (Right to be Forgotten)
	"GDPR-ART18",         # Right to Restriction of Processing
	"GDPR-ART20",         # Right to Data Portability
	"GDPR-ART21",         # Right to Object
	"GDPR-ART25",         # Data Protection by Design and Default
	"GDPR-ART30",         # Records of Processing Activities
	"GDPR-ART32",         # Security of Processing
	"GDPR-ART33",         # Breach Notification to Authority
	"GDPR-ART34",         # Breach Notification to Data Subject
	"GDPR-ART35",         # Data Protection Impact Assessment
	"GDPR-ART44",         # General Principle for Transfers
	"GDPR-ART49",         # Derogations for Specific Situations
	
	# Shorthand
	"GDPR-CONSENT",
	"GDPR-BREACH",
	"GDPR-RIGHTS",
	"GDPR-SECURITY",
	"GDPR-TRANSFER",
}

# ==================================================================================
# ISO Standards (Healthcare & Security)
# ==================================================================================

valid_iso_codes := {
	"ISO27001",           # Information Security Management
	"ISO27002",           # Code of Practice for Information Security
	"ISO27017",           # Cloud Security Controls
	"ISO27018",           # PII Protection in Cloud
	"ISO27701",           # Privacy Information Management
	"ISO13485",           # Medical Devices - Quality Management
	"ISO14971",           # Medical Devices - Risk Management
	"ISO62304",           # Medical Device Software Lifecycle
	"ISO82304",           # Health Software - General Requirements
}

# ==================================================================================
# NIST Standards (Cybersecurity Framework)
# ==================================================================================

valid_nist_codes := {
	"NIST-CSF",           # Cybersecurity Framework
	"NIST-800-53",        # Security and Privacy Controls
	"NIST-800-171",       # Protecting CUI
	"NIST-SP800-66",      # HIPAA Security Rule Implementation
}

# ==================================================================================
# Validation Rules
# ==================================================================================

# Check if a compliance code is valid across all domains
is_valid_compliance_code(code) if {
	upper_code := upper(code)
	upper_code in valid_hipaa_sections
}

is_valid_compliance_code(code) if {
	upper_code := upper(code)
	upper_code in valid_fda_codes
}

is_valid_compliance_code(code) if {
	upper_code := upper(code)
	upper_code in valid_sox_sections
}

is_valid_compliance_code(code) if {
	upper_code := upper(code)
	upper_code in valid_gdpr_articles
}

is_valid_compliance_code(code) if {
	upper_code := upper(code)
	upper_code in valid_iso_codes
}

is_valid_compliance_code(code) if {
	upper_code := upper(code)
	upper_code in valid_nist_codes
}

# Extract compliance codes from commit message
# WHY: Parse structured metadata like "HIPAA: 164.312(e)(1)" or "FDA-510k: CLASS-II"
extract_compliance_codes(message) := codes if {
	lines := split(message, "\n")
	compliance_lines := [line | 
		some i
		line := lines[i]
		# Match lines with compliance prefixes
		regex.match("(?i)^(hipaa|fda|sox|gdpr|iso|nist)[:_-]", line)
	]
	
	# Extract codes from lines (after colon/dash)
	codes := [trim_space(code) |
		some line in compliance_lines
		parts := split(line, ":")
		count(parts) > 1
		raw_codes := split(parts[1], ",")
		some raw_code in raw_codes
		code := trim_space(raw_code)
		code != ""
	]
}

# Deny commits with invalid compliance codes (hallucinations)
deny[reason] if {
	some c in input.commits
	codes := extract_compliance_codes(c.message)
	count(codes) > 0  # Only validate if codes present
	
	some code in codes
	not is_valid_compliance_code(code)
	
	reason := sprintf(
		"commit %s references invalid compliance code: %s (possible AI hallucination)",
		[c.sha, code]
	)
}

# Helper: trim whitespace
trim_space(s) := trimmed if {
	trimmed := trim(s, " \t\r\n")
}
