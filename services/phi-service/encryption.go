package main

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "errors"
    "io"
)

// EncryptPatientData encrypts patient data using AES-256-GCM
// Compliance: HIPAA Security Rule §164.312(a)(2)(iv)
func EncryptPatientData(plaintext []byte, key []byte) ([]byte, error) {
    if len(key) != 32 {
        return nil, errors.New("key must be 32 bytes for AES-256")
    }

    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }

    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }

    nonce := make([]byte, gcm.NonceSize())
    if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
        return nil, err
    }

    return gcm.Seal(nonce, nonce, plaintext, nil), nil
}

// DecryptPatientData decrypts AES-256-GCM encrypted data
func DecryptPatientData(ciphertext []byte, key []byte) ([]byte, error) {
    if len(key) != 32 {
        return nil, errors.New("key must be 32 bytes for AES-256")
    }

    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }

    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }

    nonceSize := gcm.NonceSize()
    if len(ciphertext) < nonceSize {
        return nil, errors.New("ciphertext too short")
    }

    nonce, ciphertext := ciphertext[:nonceSize], ciphertext[nonceSize:]
    return gcm.Open(nil, nonce, ciphertext, nil)
}
