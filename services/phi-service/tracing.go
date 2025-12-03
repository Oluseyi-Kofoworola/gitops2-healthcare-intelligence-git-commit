package main

import "context"

// InitTracerProvider initializes tracing (stub for lightweight deployment)
func InitTracerProvider(serviceName string) error {
	// Tracing disabled for lightweight deployment
	return nil
}

// ShutdownTracer shuts down the tracer (stub for lightweight deployment)
func ShutdownTracer(ctx context.Context) error {
	// Tracing disabled for lightweight deployment
	return nil
}

// GetTracer returns a no-op tracer
func GetTracer() noopTracer {
	return noopTracer{}
}

type noopTracer struct{}

func (noopTracer) Start(ctx context.Context, spanName string, opts ...interface{}) (context.Context, noopSpan) {
	return ctx, noopSpan{}
}

type noopSpan struct{}

func (noopSpan) End()                        {}
func (noopSpan) RecordError(err error)       {}
func (noopSpan) SetAttributes(kv ...interface{}) {}
func (noopSpan) SetStatus(code interface{}, description string) {}
