package main

import (
	"os"
	"strconv"
	"time"
)

// Config holds the service configuration
type Config struct {
	ServiceName         string
	Port                string
	MaxProcessingMillis int
	// CVE-2025-12345 mitigation - token sanitization
	EnableTokenSanitization bool
	TokenMaskPattern       string
}

// LoadConfig loads configuration from environment variables
func LoadConfig() Config {
	maxProcessingMillis, _ := strconv.Atoi(getEnv("MAX_PROCESSING_MILLIS", "100"))
	enableSanitization, _ := strconv.ParseBool(getEnv("ENABLE_TOKEN_SANITIZATION", "true"))
	
	return Config{
		ServiceName:         getEnv("SERVICE_NAME", "payment-gateway"),
		Port:                getEnv("PORT", "8083"),
		MaxProcessingMillis: maxProcessingMillis,
		EnableTokenSanitization: enableSanitization,
		TokenMaskPattern:       getEnv("TOKEN_MASK_PATTERN", "****"),
	}
}

// processingTimeout converts milliseconds to time.Duration
func processingTimeout(millis int) time.Duration {
	return time.Duration(millis) * time.Millisecond
}

// getEnv retrieves environment variable with default value
func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}
