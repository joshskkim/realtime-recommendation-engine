FROM mcr.microsoft.com/dotnet/aspnet:8.0-bookworm-slim AS build
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

FROM mcr.microsoft.com/dotnet/aspnet:8.0-bookworm-slim AS final
WORKDIR /app

# Upgrade glibc and zlib to patched versions
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libc6=2.36-9+deb12u11 \
        zlib1g=1:1.2.13.dfsg-2 \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1001 appuser
USER appuser

# Copy published output
COPY --from=publish --chown=appuser:appuser /app/publish .

EXPOSE 5001
ENV ASPNETCORE_URLS=http://+:5001
ENV ASPNETCORE_ENVIRONMENT=Production

ENTRYPOINT ["dotnet", "UserService.dll"]
