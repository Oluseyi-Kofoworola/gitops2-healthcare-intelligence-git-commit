package main

import (
    "log"
    "os"
    "strconv"
    "time"
)

type Config struct {
    Port                string
    ServiceName         string
    MaxProcessingMillis int
}

func LoadConfig() Config {
    port := getenv("PORT", "8080")
    name := getenv("SERVICE_NAME", "payment-gateway")
    maxMillis := getenvInt("MAX_PROCESSING_MILLIS", 200)

    return Config{
        Port:                port,
        ServiceName:         name,
        MaxProcessingMillis: maxMillis,
    }
}

func getenv(key, def string) string {
    val := os.Getenv(key)
    if val == "" {
        return def
    }
    return val
}

func getenvInt(key string, def int) int {
    val := os.Getenv(key)
    if val == "" {
        return def
    }
    i, err := strconv.Atoi(val)
    if err != nil {
        log.Printf("invalid int for %s, using default %d: %v", key, def, err)
        return def
    }
    return i
}

func processingTimeout(maxMillis int) time.Duration {
    return time.Duration(maxMillis) * time.Millisecond
}
