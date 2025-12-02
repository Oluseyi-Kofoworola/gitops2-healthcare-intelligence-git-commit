package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"io"

	"golang.org/x/crypto/pbkdf2"
)

// ---
// PHI Encryption Service Demo and Usage Guide
//
// This file demonstrates:
//   1. Live PHI encryption/decryption
//   2. Defensive error handling
//   3. Policy-as-code and compliance automation (see repo tools)
//   4. AI-powered commit metadata and audit trail (see repo tools)
//   5. Forensics and incident response (see repo tools)
//   6. Copilot integration and developer experience
//   7. Extensibility for enterprise teams
//
// See README.md and DEMO_EVALUATION.md for full workflow and business value.
// ---

const (
	// PBKDF2 parameters
	pbkdf2Iterations = 100000
	pbkdf2KeyLen     = 32
	saltSize         = 16
)

var (
	// ErrInvalidKey is returned when encryption key is invalid
	ErrInvalidKey = errors.New("invalid encryption key")
	// ErrInvalidCiphertext is returned when ciphertext is malformed
	ErrInvalidCiphertext = errors.New("invalid ciphertext")
	// ErrDecryptionFailed is returned when decryption fails
	ErrDecryptionFailed = errors.New("decryption failed")
)

// EncryptionService handles PHI encryption/decryption operations
type EncryptionService struct {
	masterKey []byte
}

// NewEncryptionService creates a new encryption service
func NewEncryptionService(masterKey string) (*EncryptionService, error) {
	if len(masterKey) < 16 {
		return nil, ErrInvalidKey
	}

	// Derive key from master key using SHA256
	hash := sha256.Sum256([]byte(masterKey))

	return &EncryptionService{
		masterKey: hash[:],
	}, nil
}

// Encrypt encrypts plaintext using AES-256-GCM
func (es *EncryptionService) Encrypt(plaintext []byte) (string, error) {
	// Generate random salt
	salt := make([]byte, saltSize)
	if _, err := io.ReadFull(rand.Reader, salt); err != nil {
		return "", fmt.Errorf("failed to generate salt: %w", err)
	}

	// Derive encryption key using PBKDF2
	key := pbkdf2.Key(es.masterKey, salt, pbkdf2Iterations, pbkdf2KeyLen, sha256.New)

	// Create AES cipher
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("failed to create cipher: %w", err)
	}

	// Create GCM mode
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("failed to create GCM: %w", err)
	}

	// Generate random nonce
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", fmt.Errorf("failed to generate nonce: %w", err)
	}

	// Encrypt plaintext
	ciphertext := gcm.Seal(nonce, nonce, plaintext, nil)

	// Combine salt + ciphertext and encode as base64
	result := append(salt, ciphertext...)
	encoded := base64.StdEncoding.EncodeToString(result)

	return encoded, nil
}

// Decrypt decrypts ciphertext using AES-256-GCM
func (es *EncryptionService) Decrypt(ciphertext string) ([]byte, error) {
	// Decode base64
	decoded, err := base64.StdEncoding.DecodeString(ciphertext)
	if err != nil {
		return nil, fmt.Errorf("failed to decode base64: %w", err)
	}

	// Extract salt
	if len(decoded) < saltSize {
		return nil, ErrInvalidCiphertext
	}
	salt := decoded[:saltSize]
	encryptedData := decoded[saltSize:]

	// Derive decryption key using PBKDF2
	key := pbkdf2.Key(es.masterKey, salt, pbkdf2Iterations, pbkdf2KeyLen, sha256.New)

	// Create AES cipher
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("failed to create cipher: %w", err)
	}

	// Create GCM mode
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("failed to create GCM: %w", err)
	}

	// Extract nonce
	nonceSize := gcm.NonceSize()
	if len(encryptedData) < nonceSize {
		return nil, ErrInvalidCiphertext
	}

	nonce := encryptedData[:nonceSize]
	ciphertextData := encryptedData[nonceSize:]

	// Decrypt
	plaintext, err := gcm.Open(nil, nonce, ciphertextData, nil)
	if err != nil {
		return nil, ErrDecryptionFailed
	}

	return plaintext, nil
}

// Hash creates a SHA256 hash of data (for data masking/anonymization)
func (es *EncryptionService) Hash(data []byte) string {
	hash := sha256.Sum256(data)
	return hex.EncodeToString(hash[:])
}

// HashWithSalt creates a salted SHA256 hash
func (es *EncryptionService) HashWithSalt(data []byte, salt []byte) string {
	if len(salt) != saltSize {
		// Defensive: ensure salt is correct size for security
		panic("invalid salt size for HashWithSalt")
	}
	saltedData := append(data, salt...)
	hash := sha256.Sum256(saltedData)
	return hex.EncodeToString(hash[:])
}

// GenerateSalt generates a cryptographically secure random salt for PHI encryption
func GenerateSalt() ([]byte, error) {
	salt := make([]byte, saltSize)
	if _, err := io.ReadFull(rand.Reader, salt); err != nil {
		return nil, fmt.Errorf("failed to generate salt: %w", err)
	}
	return salt, nil
}

// Demo helper: Validate encryption and decryption round-trip for demo experience
func DemoPHIEncryptionRoundTrip(es *EncryptionService, plaintext string) error {
	encrypted, err := es.Encrypt([]byte(plaintext))
	if err != nil {
		return fmt.Errorf("encryption failed: %w", err)
	}
	decrypted, err := es.Decrypt(encrypted)
	if err != nil {
		return fmt.Errorf("decryption failed: %w", err)
	}
	if string(decrypted) != plaintext {
		return fmt.Errorf("round-trip failed: got '%s', want '%s'", string(decrypted), plaintext)
	}
	fmt.Println("[DEMO] PHI encryption round-trip successful:")
	fmt.Printf("  Plaintext: %s\n  Encrypted: %s\n  Decrypted: %s\n", plaintext, encrypted, string(decrypted))
	return nil
}

// Defensive error handling demo
func demoErrorHandling() {
	fmt.Println("[DEMO] Error handling demo:")
	_, err := NewEncryptionService("short")
	if err != nil {
		fmt.Printf("  [EXPECTED] Invalid key error: %v\n", err)
	}
	defer func() {
		recoverMsg := recover()
		if recoverMsg != nil {
			fmt.Printf("  [EXPECTED] Panic on bad salt: %v\n", recoverMsg)
		}
	}()
	es, _ := NewEncryptionService("SuperSecretMasterKey123!")
	es.HashWithSalt([]byte("data"), []byte("bad")) // triggers panic
}

func main() {
	// 1. Live PHI encryption/decryption demo
	masterKey := "SuperSecretMasterKey123!" // For demo only; use secure key management in production
	phi := "Sensitive PHI Data for Demo"

	es, err := NewEncryptionService(masterKey)
	if err != nil {
		fmt.Printf("[DEMO] Failed to create EncryptionService: %v\n", err)
		return
	}
	if err := DemoPHIEncryptionRoundTrip(es, phi); err != nil {
		fmt.Printf("[DEMO] Encryption round-trip failed: %v\n", err)
	} else {
		fmt.Println("[DEMO] Encryption round-trip test passed.")
	}

	// 2. Defensive error handling demo
	demoErrorHandling()

	// 3. Policy-as-code, compliance, audit, forensics, Copilot, extensibility:
	fmt.Println("\n[INFO] For compliance, audit, and forensics, use:")
	fmt.Println("  $ python3 tools/healthcare_commit_generator.py --type feat --scope phi --description 'improve PHI encryption' --files services/phi-service/encryption.go")
	fmt.Println("  $ python3 tools/ai_compliance_framework.py analyze-commit HEAD")
	fmt.Println("  $ python3 tools/git_intel/risk_scorer.py --max-commits 1")
	fmt.Println("  $ python3 tools/intelligent_bisect.py --file services/phi-service/encryption.go")
	fmt.Println("  $ scripts/demo.sh  # for guided scenario")
	fmt.Println("\n[INFO] See README.md and DEMO_EVALUATION.md for full workflow and business value.")
}
