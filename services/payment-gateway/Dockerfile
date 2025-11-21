FROM golang:1.22-alpine AS build

WORKDIR /app
COPY . .

RUN go mod download
RUN CGO_ENABLED=0 GOOS=linux go build -o payment-gateway main.go server.go handlers.go config.go payment.go

FROM gcr.io/distroless/base-debian12

ENV PORT=8080
ENV SERVICE_NAME=payment-gateway
ENV MAX_PROCESSING_MILLIS=200

WORKDIR /
COPY --from=build /app/payment-gateway /payment-gateway

EXPOSE 8080

USER nonroot:nonroot

ENTRYPOINT ["/payment-gateway"]
