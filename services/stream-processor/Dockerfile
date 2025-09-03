FROM python:3.11-slim-bookworm AS build

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM python:3.11-slim-bookworm

WORKDIR /app

COPY --from=build /app /app

RUN apt-get update && apt-get upgrade -y

RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-u", "stream_processor.py"]
