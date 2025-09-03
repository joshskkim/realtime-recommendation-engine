FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy solution and projects for caching
COPY *.csproj ./
RUN dotnet restore

# Copy source code
COPY . .

# Build
RUN dotnet build -c Release -o /app/build

# Publish
FROM build AS publish
RUN dotnet publish -c Release -o /app/publish

# Runtime
FROM mcr.microsoft.com/dotnet/aspnet:8.0.20230927-bookworm-slim AS final
WORKDIR /app

# Optional minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN useradd -m -u 1001 appuser
USER appuser

# Copy published output with correct ownership
COPY --from=publish --chown=appuser:appuser /app/publish .

EXPOSE 5001
ENV ASPNETCORE_URLS=http://+:5001
ENV ASPNETCORE_ENVIRONMENT=Production

ENTRYPOINT ["dotnet", "UserService.dll"]
