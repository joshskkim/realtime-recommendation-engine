FROM python:3.13.7-alpine3.22 AS builder

WORKDIR /app

# Install build dependencies for compiling packages like numpy
RUN apk update && apk add --no-cache \
    blas-dev \
    build-base \
    gfortran \
    lapack-dev \
    libffi-dev \
    musl-dev \
    openssl-dev \
    postgresql-dev \
    python3-dev \
    && rm -rf /var/cache/apk/*

# Upgrade pip/setuptools/wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
