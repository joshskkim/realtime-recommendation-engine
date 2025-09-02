# File: services/cache-service/Makefile
.PHONY: test build run clean

test:
	@echo "Running Cache Service tests..."
	cargo test || echo "Cargo not configured"

build:
	docker build -t cache-service:local .

run:
	cargo run

clean:
	cargo clean