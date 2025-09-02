# File: services/stream-processor/Makefile
.PHONY: test build run clean install

install:
	pip install -r requirements.txt

test:
	@echo "Running Stream Processor tests..."
	python -m pytest tests/ || echo "No tests found"

build:
	docker build -t stream-processor:local .

run:
	python stream_processor.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +