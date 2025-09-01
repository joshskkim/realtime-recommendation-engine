// services/user-service/Services/KafkaProducerService.cs
using Confluent.Kafka;
using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace UserService.Services;

public interface IKafkaProducerService
{
    Task ProduceAsync(string topic, string key, object message);
}

public class KafkaProducerService : IKafkaProducerService, IDisposable
{
    private readonly IProducer<string, string> _producer;
    private readonly ILogger<KafkaProducerService> _logger;

    public KafkaProducerService(IProducer<string, string> producer, ILogger<KafkaProducerService> logger)
    {
        _producer = producer;
        _logger = logger;
    }

    public async Task ProduceAsync(string topic, string key, object message)
    {
        try
        {
            var result = await _producer.ProduceAsync(topic, new Message<string, string>
            {
                Key = key,
                Value = JsonSerializer.Serialize(message)
            });

            _logger.LogDebug("Produced message to {Topic} with key {Key} at offset {Offset}", 
                topic, key, result.Offset);
        }
        catch (ProduceException<string, string> ex)
        {
            _logger.LogError(ex, "Error producing message to Kafka topic {Topic}", topic);
            throw;
        }
    }

    public void Dispose()
    {
        _producer?.Dispose();
    }
}