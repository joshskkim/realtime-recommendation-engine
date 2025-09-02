using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Confluent.Kafka;
using StackExchange.Redis;
using Serilog;
using System.Text.Json;
using Prometheus;
using UserService.Data;
using UserService.Services;
using UserService.Models;

var builder = WebApplication.CreateBuilder(args);

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .WriteTo.Console()
    .WriteTo.File("logs/user-service-.txt", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

// Add services
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddHealthChecks()
    .AddDbContextCheck<UserDbContext>()
    .AddRedis(builder.Configuration.GetConnectionString("Redis") ?? "localhost:6379");

// Configure Entity Framework
builder.Services.AddDbContext<UserDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("PostgreSQL")));

// Centralize Redis configuration
var redisConnectionString = builder.Configuration.GetConnectionString("Redis");
if (string.IsNullOrWhiteSpace(redisConnectionString))
{
    Log.Warning("Redis connection string not found. Falling back to localhost:6379");
    redisConnectionString = "localhost:6379";
}

builder.Services.AddSingleton<IConnectionMultiplexer>(sp =>
{
    var configuration = ConfigurationOptions.Parse(redisConnectionString);
    configuration.AbortOnConnectFail = false;
    return ConnectionMultiplexer.Connect(configuration);
});

// Configure Kafka
builder.Services.AddSingleton<IProducer<string, string>>(sp =>
{
    var config = new ProducerConfig
    {
        BootstrapServers = builder.Configuration["Kafka:BootstrapServers"] ?? "localhost:9092",
        ClientId = "user-service",
        Acks = Acks.All
    };
    return new ProducerBuilder<string, string>(config).Build();
});

// Kafka cleanup service for graceful shutdown
builder.Services.AddHostedService<KafkaProducerCleanupService>();

builder.Services.AddSingleton<IKafkaProducerService, KafkaProducerService>();
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IUserService, UserService.Services.UserService>();
builder.Services.AddScoped<IBusinessRulesEngine, BusinessRulesEngine>();

// Add CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("https://your-frontend-domain.com") // Replace with actual domain
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

// Configure middleware
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
    app.UseDeveloperExceptionPage();
}
else
{
    app.UseExceptionHandler("/error");
}

app.UseSerilogRequestLogging();
app.UseHttpMetrics();
app.UseCors();
app.UseRouting();
app.MapControllers();
app.MapHealthChecks("/health");
app.MapMetrics();

// Run database migrations
using (var scope = app.Services.CreateScope())
{
    var dbContext = scope.ServiceProvider.GetRequiredService<UserDbContext>();
    try
    {
        dbContext.Database.Migrate();
        Log.Information("✅ Database migrated successfully");
    }
    catch (Exception ex)
    {
        Log.Error(ex, "❌ Error migrating database");
    }
}

app.Run();


// KafkaProducerCleanupService.cs
public class KafkaProducerCleanupService : IHostedService
{
    private readonly IProducer<string, string> _producer;

    public KafkaProducerCleanupService(IProducer<string, string> producer)
    {
        _producer = producer;
    }

    public Task StartAsync(CancellationToken cancellationToken) => Task.CompletedTask;

    public Task StopAsync(CancellationToken cancellationToken)
    {
        _producer.Flush(TimeSpan.FromSeconds(5));
        _producer.Dispose();
        Log.Information("Kafka producer disposed gracefully");
        return Task.CompletedTask;
    }
}
