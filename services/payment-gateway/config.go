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
}

// LoadConfig loads configuration from environment variables
func LoadConfig() Config {
	maxProcessingMillis, _ := strconv.Atoi(getEnv("MAX_PROCESSING_MILLIS", "100"))
	
	return Config{
		ServiceName:         getEnv("SERVICE_NAME", "payment-gateway"),
		Port:                getEnv("PORT", "8083"),
		MaxProcessingMillis: maxProcessingMillis,
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
