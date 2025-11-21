SERVICE_NAME := payment-gateway
IMAGE := gitops2-demo/$(SERVICE_NAME):local

.PHONY: test build run docker-build docker-run

test:
	go test ./...

build:
	go build -o bin/$(SERVICE_NAME) main.go server.go handlers.go config.go payment.go

run:
	PORT=8080 MAX_PROCESSING_MILLIS=200 go run main.go server.go handlers.go config.go payment.go

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm -p 8080:8080 $(IMAGE)
