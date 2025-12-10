// SPDX-License-Identifier: MIT
// Copyright (c) 2025 GitOps Healthcare Intelligence Platform

package validation

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"regexp"
	"strings"
	"unicode"
)

var (
	// ErrWeakSecret is returned when a secret doesn't meet strength requirements
	ErrWeakSecret = errors.New("secret does not meet strength requirements")
	
	// Email validation regex (RFC 5322 simplified)
	emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
	
	// UUID validation regex (RFC 4122)
	uuidRegex = regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`)
)

// SecretStrengthRequirements defines requirements for secrets
type SecretStrengthRequirements struct {
	MinLength      int
	MinUniqueChars int
	RequireUpper   bool
	RequireLower   bool
	RequireDigit   bool
	RequireSpecial bool
}

// DefaultSecretRequirements returns HIPAA-compliant secret requirements
func DefaultSecretRequirements() SecretStrengthRequirements {
	return SecretStrengthRequirements{
		MinLength:      32,  // 256 bits when base64-encoded
		MinUniqueChars: 10,  // Prevent "aaaaa..." secrets
		RequireUpper:   false,
		RequireLower:   false,
		RequireDigit:   false,
		RequireSpecial: false,
	}
}

// ValidateSecretStrength checks if a secret meets security requirements
func ValidateSecretStrength(secret string, reqs SecretStrengthRequirements) error {
	if len(secret) < reqs.MinLength {
		return fmt.Errorf("%w: minimum length is %d, got %d", ErrWeakSecret, reqs.MinLength, len(secret))
	}
	
	// Check character diversity
	uniqueChars := make(map[rune]bool)
	hasUpper := false
	hasLower := false
	hasDigit := false
	hasSpecial := false
	
	for _, ch := range secret {
		uniqueChars[ch] = true
		
		if unicode.IsUpper(ch) {
			hasUpper = true
		}
		if unicode.IsLower(ch) {
			hasLower = true
		}
		if unicode.IsDigit(ch) {
			hasDigit = true
		}
		if unicode.IsPunct(ch) || unicode.IsSymbol(ch) {
			hasSpecial = true
		}
	}
	
	if len(uniqueChars) < reqs.MinUniqueChars {
		return fmt.Errorf("%w: insufficient entropy (only %d unique characters)", ErrWeakSecret, len(uniqueChars))
	}
	
	if reqs.RequireUpper && !hasUpper {
		return fmt.Errorf("%w: must contain uppercase letters", ErrWeakSecret)
	}
	if reqs.RequireLower && !hasLower {
		return fmt.Errorf("%w: must contain lowercase letters", ErrWeakSecret)
	}
	if reqs.RequireDigit && !hasDigit {
		return fmt.Errorf("%w: must contain digits", ErrWeakSecret)
	}
	if reqs.RequireSpecial && !hasSpecial {
		return fmt.Errorf("%w: must contain special characters", ErrWeakSecret)
	}
	
	return nil
}

// GenerateSecureSecret generates a cryptographically secure random secret
func GenerateSecureSecret(length int) (string, error) {
	if length < 32 {
		return "", errors.New("secret length must be at least 32 bytes")
	}
	
	bytes := make([]byte, length)
	if _, err := rand.Read(bytes); err != nil {
		return "", fmt.Errorf("failed to generate random bytes: %w", err)
	}
	
	return base64.StdEncoding.EncodeToString(bytes), nil
}

// IsValidEmail checks if a string is a valid email address
func IsValidEmail(email string) bool {
	if len(email) > 254 {  // RFC 5321
		return false
	}
	return emailRegex.MatchString(email)
}

// IsValidUUID checks if a string is a valid UUID v4
func IsValidUUID(uuid string) bool {
	return uuidRegex.MatchString(strings.ToLower(uuid))
}

// SanitizeString removes potentially dangerous characters from user input
func SanitizeString(input string) string {
	// Remove null bytes
	input = strings.ReplaceAll(input, "\x00", "")
	
	// Trim whitespace
	input = strings.TrimSpace(input)
	
	// Remove control characters (except newline and tab for multiline text)
	var result strings.Builder
	for _, r := range input {
		if unicode.IsControl(r) && r != '\n' && r != '\t' {
			continue
		}
		result.WriteRune(r)
	}
	
	return result.String()
}

// IsAlphanumeric checks if string contains only letters and numbers
func IsAlphanumeric(s string) bool {
	for _, r := range s {
		if !unicode.IsLetter(r) && !unicode.IsDigit(r) {
			return false
		}
	}
	return true
}

// TruncateString safely truncates a string to maxLength
func TruncateString(s string, maxLength int) string {
	if len(s) <= maxLength {
		return s
	}
	
	// Truncate at rune boundaries, not byte boundaries
	runes := []rune(s)
	if len(runes) <= maxLength {
		return s
	}
	
	return string(runes[:maxLength])
}

// ValidateJSONKeys checks if JSON object keys match allowed pattern
func ValidateJSONKeys(keys []string, allowedPattern *regexp.Regexp) error {
	for _, key := range keys {
		if !allowedPattern.MatchString(key) {
			return fmt.Errorf("invalid key: %s", key)
		}
	}
	return nil
}

// IsWhitelisted checks if a value exists in a whitelist
func IsWhitelisted(value string, whitelist []string) bool {
	for _, allowed := range whitelist {
		if value == allowed {
			return true
		}
	}
	return false
}

// ValidateUserID ensures user ID format is safe
func ValidateUserID(userID string) error {
	if userID == "" {
		return errors.New("user ID cannot be empty")
	}
	
	if len(userID) > 128 {
		return errors.New("user ID too long (max 128 characters)")
	}
	
	// Allow alphanumeric, hyphen, underscore, and dot
	validPattern := regexp.MustCompile(`^[a-zA-Z0-9._-]+$`)
	if !validPattern.MatchString(userID) {
		return errors.New("user ID contains invalid characters")
	}
	
	return nil
}

// ValidateScope validates OAuth/JWT scope format
func ValidateScope(scope string) error {
	if scope == "" {
		return errors.New("scope cannot be empty")
	}
	
	if len(scope) > 64 {
		return errors.New("scope too long (max 64 characters)")
	}
	
	// Scope format: resource:action (e.g., "phi:read", "payment:write")
	scopePattern := regexp.MustCompile(`^[a-z_]+:[a-z_]+$`)
	if !scopePattern.MatchString(scope) {
		return errors.New("invalid scope format (expected: resource:action)")
	}
	
	return nil
}
