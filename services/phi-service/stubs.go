package main

import (
"context"
"go.opentelemetry.io/otel/sdk/trace"
oteltrace "go.opentelemetry.io/otel/trace"
)

// Stub functions for removed observability code

func InitTracerProvider(ctx context.Context, serviceName, endpoint string) (*trace.TracerProvider, error) {
	return nil, nil
}

func ShutdownTracer(ctx context.Context, tp *trace.TracerProvider) error {
	return nil
}

func RecordEncryptionOp(op, status string, duration float64, dataSize int) {
}

func GetTracer() oteltrace.Tracer {
	return oteltrace.NewNoopTracerProvider().Tracer("noop")
}

func IncActiveRequests() {
}

func DecActiveRequests() {
}

func RecordHTTPRequest(method, path, status string, duration float64) {
}
