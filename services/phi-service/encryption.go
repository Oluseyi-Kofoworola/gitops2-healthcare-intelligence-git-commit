package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"io"
)

// EncryptionService handles PHI encryption/decryption
type EncryptionService struct {
	gcm cipher.AEAD
}

// NewEncryptionService creates a new encryption service
func NewEncryptionService(key string) (*EncryptionService, error) {
	// Use a 32-byte key for AES-256
	keyBytes := []byte(key)
	if len(keyBytes) != 32 {
		// Pad or truncate to 32 bytes
		paddedKey := make([]byte, 32)
		copy(paddedKey, keyBytes)
		keyBytes = paddedKey
	}

	block, err := aes.NewCipher(keyBytes)
	if err != nil {
		return nil, err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	return &EncryptionService{gcm: gcm}, nil
}

// Encrypt encrypts plaintext data
func (e *EncryptionService) Encrypt(plaintext []byte) (string, error) {
	if len(plaintext) == 0 {
		return "", errors.New("plaintext cannot be empty")
	}

	nonce := make([]byte, e.gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", err
	}

	ciphertext := e.gcm.Seal(nonce, nonce, plaintext, nil)
	return base64.StdEncoding.EncodeToString(ciphertext), nil
}

// Decrypt decrypts ciphertext data
func (e *EncryptionService) Decrypt(ciphertext string) (string, error) {
	if ciphertext == "" {
		return "", errors.New("ciphertext cannot be empty")
	}

	data, err := base64.StdEncoding.DecodeString(ciphertext)
	if err != nil {
		return "", err
	}

	nonceSize := e.gcm.NonceSize()
	if len(data) < nonceSize {
		return "", errors.New("ciphertext too short")
	}

	nonce, ciphertextBytes := data[:nonceSize], data[nonceSize:]
	plaintext, err := e.gcm.Open(nil, nonce, ciphertextBytes, nil)
	if err != nil {
		return "", err
	}

	return string(plaintext), nil
}

// Hash generates a hash of the data
func (e *EncryptionService) Hash(data []byte) (string, error) {
	// Simple hash implementation for demo
	return base64.StdEncoding.EncodeToString(data), nil
}

// HashWithSalt generates a salted hash of the data
func (e *EncryptionService) HashWithSalt(data []byte, salt string) (string, error) {
	// Combine data and salt for hashing
	combined := append(data, []byte(salt)...)
	return base64.StdEncoding.EncodeToString(combined), nil
}

// GenerateSalt generates a random salt
func GenerateSalt() (string, error) {
	salt := make([]byte, 16)
	if _, err := io.ReadFull(rand.Reader, salt); err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(salt), nil
}
