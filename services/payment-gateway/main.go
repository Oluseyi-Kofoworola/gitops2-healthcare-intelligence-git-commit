package main

import (
    "log"
)

func main() {
    cfg := LoadConfig()
    server := NewServer(cfg)

    if err := server.ListenAndServe(); err != nil {
        log.Fatalf("server failed: %v", err)
    }
}
