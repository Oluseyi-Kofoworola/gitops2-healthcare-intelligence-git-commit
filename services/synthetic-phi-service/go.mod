module github.com/ITcredibl/gitops2-enterprise-git-intel-demo/synthetic-phi-service

go 1.22

// Synthetic PHI service for healthcare compliance testing
// Enhanced with OpenTelemetry, structured logging, and metrics

require (
	github.com/rs/zerolog v1.31.0
	go.opentelemetry.io/otel v1.21.0
	go.opentelemetry.io/otel/exporters/otlp/otlptrace v1.21.0
	go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc v1.21.0
	go.opentelemetry.io/otel/sdk v1.21.0
	go.opentelemetry.io/otel/trace v1.21.0
	github.com/prometheus/client_golang v1.17.0
)

require (
	github.com/mattn/go-colorable v0.1.13 // indirect
	github.com/mattn/go-isatty v0.0.20 // indirect
	golang.org/x/sys v0.15.0 // indirect
)
