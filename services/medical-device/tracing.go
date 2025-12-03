package main

import "context"

// InitTracerProvider is a stub for OpenTelemetry tracing
func InitTracerProvider(serviceName string) error {
	// Tracing disabled for lightweight deployment
	return nil
}

// ShutdownTracer is a stub for OpenTelemetry tracing shutdown
func ShutdownTracer(ctx context.Context) error {
	// Tracing disabled for lightweight deployment
	return nil
}
