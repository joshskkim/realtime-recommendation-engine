# File: services/user-service/Dockerfile

# Use specific .NET version
FROM mcr.microsoft.com/dotnet/sdk:8.0.101-alpine3.19 AS build

WORKDIR /src

# Copy project file
COPY *.csproj ./
RUN dotnet restore

# Copy source code
COPY . ./

# Build with security optimizations
RUN dotnet build -c Release -o /app/build \
    -p:PublishTrimmed=true \
    -p:PublishSingleFile=true \
    -p:DebugType=None \
    -p:DebugSymbols=false

# Publish
RUN dotnet publish -c Release -o /app/publish \
    -p:PublishTrimmed=true \
    -p:PublishSingleFile=true \
    -p:DebugType=None \
    -p:DebugSymbols=false

# Runtime stage - use distroless for minimal attack surface
FROM mcr.microsoft.com/dotnet/runtime-deps:8.0-alpine3.19

# Install security updates
RUN apk update && \
    apk upgrade && \
    apk add --no-cache curl && \
    rm -rf /var/cache/apk/*

WORKDIR /app

# Copy published app
COPY --from=build /app/publish .

# Create non-root user
RUN addgroup -g 1001 -S dotnet && \
    adduser -S dotnet -u 1001 -G dotnet && \
    chown -R dotnet:dotnet /app

# Switch to non-root user
USER dotnet

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

EXPOSE 5001

ENV ASPNETCORE_URLS=http://+:5001 \
    ASPNETCORE_ENVIRONMENT=Production \
    DOTNET_RUNNING_IN_CONTAINER=true \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

ENTRYPOINT ["./UserService"]