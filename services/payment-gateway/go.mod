module github.com/ITcredibl/gitops2-enterprise-git-intel-demo/payment-gateway

go 1.22

require (
	github.com/go-chi/chi/v5 v5.2.3
	github.com/prometheus/client_golang v1.17.0
	github.com/rs/zerolog v1.31.0
	go.opentelemetry.io/otel v1.21.0
	go.opentelemetry.io/otel/attribute v1.21.0
	go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc v1.21.0
	go.opentelemetry.io/otel/sdk v1.21.0
	go.opentelemetry.io/otel/trace v1.21.0
	google.golang.org/grpc v1.60.0
)

