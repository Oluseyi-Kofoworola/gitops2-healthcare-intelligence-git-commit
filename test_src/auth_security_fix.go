// Auth service security patch
package auth

import "time"

// FixSessionTimeout addresses CVE-2025-XXXX
// Previous: No timeout enforcement
// Fixed: 30-minute session timeout
func ValidateSession(sessionID string, createdAt time.Time) bool {
    maxAge := 30 * time.Minute
    if time.Since(createdAt) > maxAge {
        return false
    }
    return true
}
