// PHI Service - HIPAA-compliant encryption module
package phi

import (
    "crypto/aes"
    "crypto/cipher"
    "errors"
)

// EncryptData encrypts data using AES-256-GCM
// Implements HIPAA Security Rule 164.312(a)(2)(iv)
func EncryptData(plaintext []byte, key []byte) ([]byte, error) {
    if len(key) != 32 {
        return nil, errors.New("key must be 32 bytes")
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
    ciphertext := gcm.Seal(nonce, nonce, plaintext, nil)
    return ciphertext, nil
}
