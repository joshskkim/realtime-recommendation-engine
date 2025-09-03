using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Confluent.Kafka;
using StackExchange.Redis;
using Serilog;
using Prometheus;
using UserService.Data;
using UserService.Services;
using UserService.Models;

var builder = WebApplication.CreateBuilder(args);

// Serilog
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .WriteTo.Console()
    .WriteTo.File("logs/user-service-.txt", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

// Services
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Health checks
builder.Services.AddHealthChecks()
    .AddDbContextCheck<UserDbContext>()
    .AddRedis(builder.Configuration.GetConnectionString("Redis") ?? "localhost:6379");

// EF Core
builder.Services.AddDbContext<UserDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("PostgreSQL")));

// Redis
var redisConnectionString = builder.Configuration.GetConnectionString("Redis") ?? "localhost:6379";
builder.Services.AddSingleton<IConnectionMultiplexer>(sp =>
{
    var config = StackExchange.Redis.ConfigurationOptions.Parse(redisConnectionString);
    config.AbortOnConnectFail = false;
    return ConnectionMultiplexer.Connect(config);
});

// Kafka
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

builder.Services.AddHostedService<KafkaProducerCleanupService>();

// Business logic services
builder.Services.AddSingleton<IKafkaProducerService, KafkaProducerService>();
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IUserService, UserService.Services.UserService>();
builder.Services.AddScoped<IBusinessRulesEngine, BusinessRulesEngine>();

// Prometheus metrics (prometheus-net)
builder.Services.AddHttpMetrics();

// CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("https://your-frontend-domain.com")
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

// Middleware
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
app.UseCors();
app.UseRouting();

// Prometheus endpoints
app.UseMetricServer();   //metrics

app.MapControllers();
app.MapHealthChecks("/health");

// Run DB migrations
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<UserDbContext>();
    try
    {
        db.Database.Migrate();
        Log.Information("✅ Database migrated successfully");
    }
    catch (Exception ex)
    {
        Log.Error(ex, "❌ Error migrating database");
    }
}

app.Run();


// Kafka cleanup service
public class KafkaProducerCleanupService : IHostedService
{
    private readonly IProducer<string, string> _producer;

    public KafkaProducerCleanupService(IProducer<string, string> producer) => _producer = producer;

    public Task StartAsync(CancellationToken cancellationToken) => Task.CompletedTask;

    public Task StopAsync(CancellationToken cancellationToken)
    {
        _producer.Flush(TimeSpan.FromSeconds(5));
        _producer.Dispose();
        Log.Information("Kafka producer disposed gracefully");
        return Task.CompletedTask;
    }
}
