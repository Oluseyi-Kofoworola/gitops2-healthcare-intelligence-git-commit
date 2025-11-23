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
	saltedData := append(data, salt...)
	hash := sha256.Sum256(saltedData)
	return hex.EncodeToString(hash[:])
}

// GenerateSalt generates a random salt
func GenerateSalt() ([]byte, error) {
	salt := make([]byte, saltSize)
	if _, err := io.ReadFull(rand.Reader, salt); err != nil {
		return nil, fmt.Errorf("failed to generate salt: %w", err)
	}
	return salt, nil
}
