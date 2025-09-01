FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy all project files
COPY . .

# Restore and build
RUN dotnet restore UserService.csproj
RUN dotnet build UserService.csproj -c Release -o /app/build

# Publish
RUN dotnet publish UserService.csproj -c Release -o /app/publish

# List files to verify DLL exists
RUN ls -la /app/publish/

# Runtime image
FROM mcr.microsoft.com/dotnet/aspnet:8.0

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /app/publish .

# Verify files in final image
RUN ls -la /app/

EXPOSE 5001

# Set environment variable for ASP.NET Core
ENV ASPNETCORE_URLS=http://+:5001
ENV ASPNETCORE_ENVIRONMENT=Development

ENTRYPOINT ["dotnet", "UserService.dll"]