// Package config provides common configuration utilities for all services
package config

import (
	"os"
	"strconv"
)

// GetEnv retrieves an environment variable with a default fallback value.
// This is the canonical implementation used across all services.
func GetEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

// GetEnvInt retrieves an environment variable as an integer with a default fallback.
// Returns defaultValue if the environment variable is not set or cannot be parsed.
func GetEnvInt(key string, defaultValue int) int {
	valueStr := os.Getenv(key)
	if valueStr == "" {
		return defaultValue
	}
	
	value, err := strconv.Atoi(valueStr)
	if err != nil {
		return defaultValue
	}
	return value
}

// GetEnvBool retrieves an environment variable as a boolean with a default fallback.
// Returns defaultValue if the environment variable is not set or cannot be parsed.
func GetEnvBool(key string, defaultValue bool) bool {
	valueStr := os.Getenv(key)
	if valueStr == "" {
		return defaultValue
	}
	
	value, err := strconv.ParseBool(valueStr)
	if err != nil {
		return defaultValue
	}
	return value
}
