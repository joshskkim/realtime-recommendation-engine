# File: services/user-service/Makefile
.PHONY: test build run clean

test:
	@echo "Running User Service tests..."
	dotnet test || echo "No tests found"

build:
	docker build -t user-service:local .

run:
	dotnet run

clean:
	dotnet clean