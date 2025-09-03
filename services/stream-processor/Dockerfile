FROM python:3.13.7-slim AS builder

WORKDIR /app

# Install build dependencies for compiling packages like numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    gfortran \
    libffi-dev \
    libopenblas-dev \
    libpq-dev \
    && pip install --upgrade pip \
    && pip install scipy \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip/setuptools/wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
