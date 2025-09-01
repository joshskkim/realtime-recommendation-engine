// services/user-service/Controllers/UsersController.cs
using Microsoft.AspNetCore.Mvc;
using StackExchange.Redis;
using System.Text.Json;
using Prometheus;
using UserService.Services;
using UserService.Models;

namespace UserService.Controllers;

[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    private readonly IUserService _userService;
    private readonly IBusinessRulesEngine _rulesEngine;
    private readonly IKafkaProducerService _kafkaProducer;
    private readonly ILogger<UsersController> _logger;
    private readonly IConnectionMultiplexer _redis;

    private static readonly Counter UserProfileRequests = Metrics
        .CreateCounter("user_profile_requests_total", "Total number of user profile requests");
    
    private static readonly Histogram RequestDuration = Metrics
        .CreateHistogram("user_request_duration_seconds", "Duration of user requests in seconds");

    public UsersController(
        IUserService userService,
        IBusinessRulesEngine rulesEngine,
        IKafkaProducerService kafkaProducer,
        IConnectionMultiplexer redis,
        ILogger<UsersController> logger)
    {
        _userService = userService;
        _rulesEngine = rulesEngine;
        _kafkaProducer = kafkaProducer;
        _redis = redis;
        _logger = logger;
    }

    [HttpGet("{userId}")]
    public async Task<IActionResult> GetUser(string userId)
    {
        using var timer = RequestDuration.NewTimer();
        UserProfileRequests.Inc();

        try
        {
            var db = _redis.GetDatabase();
            var cacheKey = $"user:profile:{userId}";
            
            // Check cache
            var cached = await db.StringGetAsync(cacheKey);
            if (!cached.IsNullOrEmpty)
            {
                _logger.LogInformation("Cache hit for user {UserId}", userId);
                return Ok(JsonSerializer.Deserialize<UserProfileDto>(cached!));
            }

            var user = await _userService.GetUserByExternalIdAsync(userId);
            if (user == null)
            {
                return NotFound(new { error = "User not found" });
            }

            var profile = new UserProfileDto
            {
                UserId = user.ExternalId,
                Username = user.Username,
                Email = user.Email,
                Profile = user.Profile != null ? new ProfileDto
                {
                    Age = user.Profile.Age,
                    Gender = user.Profile.Gender,
                    Location = user.Profile.Location,
                    Interests = user.Profile.Interests?.Split(',').ToList() ?? new List<string>(),
                    Metadata = user.Profile.Metadata
                } : null,
                Preferences = user.Preferences.Select(p => new PreferenceDto
                {
                    Category = p.Category,
                    Weight = p.Weight,
                    Tags = p.Tags
                }).ToList(),
                RecentInteractions = user.Interactions
                    .OrderByDescending(i => i.Timestamp)
                    .Take(10)
                    .Select(i => new InteractionDto
                    {
                        ItemId = i.ItemId,
                        Type = i.InteractionType,
                        Rating = i.Rating,
                        Timestamp = i.Timestamp
                    }).ToList()
            };

            // Cache for 5 minutes
            await db.StringSetAsync(cacheKey, JsonSerializer.Serialize(profile), TimeSpan.FromMinutes(5));

            return Ok(profile);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving user {UserId}", userId);
            return StatusCode(500, new { error = "Internal server error" });
        }
    }

    [HttpPost]
    public async Task<IActionResult> CreateUser([FromBody] CreateUserRequest request)
    {
        try
        {
            // Validate request
            if (!_rulesEngine.ValidateUserCreation(request))
            {
                return BadRequest(new { error = "Invalid user data" });
            }

            var user = await _userService.CreateUserAsync(new User
            {
                ExternalId = Guid.NewGuid().ToString(),
                Username = request.Username,
                Email = request.Email,
                Profile = new UserProfile
                {
                    Age = request.Age,
                    Gender = request.Gender,
                    Location = request.Location,
                    Interests = string.Join(",", request.Interests ?? new List<string>())
                }
            });

            // Send event to Kafka
            await _kafkaProducer.ProduceAsync("user-profiles", user.ExternalId, new
            {
                event_type = "user_created",
                user_id = user.ExternalId,
                timestamp = DateTime.UtcNow,
                profile = new
                {
                    age = request.Age,
                    gender = request.Gender,
                    location = request.Location,
                    interests = request.Interests
                }
            });

            return CreatedAtAction(nameof(GetUser), new { userId = user.ExternalId }, new { userId = user.ExternalId });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating user");
            return StatusCode(500, new { error = "Failed to create user" });
        }
    }

    [HttpPost("{userId}/interactions")]
    public async Task<IActionResult> RecordInteraction(string userId, [FromBody] RecordInteractionRequest request)
    {
        try
        {
            var user = await _userService.GetUserByExternalIdAsync(userId);
            if (user == null)
            {
                return NotFound(new { error = "User not found" });
            }

            // Apply business rules
            var processedInteraction = _rulesEngine.ProcessInteraction(request);

            var interaction = new UserInteraction
            {
                UserId = user.Id,
                ItemId = processedInteraction.ItemId,
                InteractionType = processedInteraction.InteractionType,
                Rating = processedInteraction.Rating,
                Timestamp = DateTime.UtcNow,
                Metadata = processedInteraction.Metadata
            };

            await _userService.AddInteractionAsync(interaction);

            // Update user preferences based on interaction
            await _userService.UpdateUserPreferencesAsync(user.Id, interaction);

            // Invalidate cache
            var db = _redis.GetDatabase();
            await db.KeyDeleteAsync($"user:profile:{userId}");

            // Send to Kafka for real-time processing
            await _kafkaProducer.ProduceAsync("user-interactions", userId, new
            {
                user_id = userId,
                item_id = request.ItemId,
                interaction_type = request.InteractionType,
                rating = request.Rating,
                timestamp = DateTime.UtcNow,
                metadata = request.Metadata
            });

            return Ok(new { message = "Interaction recorded successfully" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error recording interaction for user {UserId}", userId);
            return StatusCode(500, new { error = "Failed to record interaction" });
        }
    }

    [HttpPut("{userId}/preferences")]
    public async Task<IActionResult> UpdatePreferences(string userId, [FromBody] UpdatePreferencesRequest request)
    {
        try
        {
            var user = await _userService.GetUserByExternalIdAsync(userId);
            if (user == null)
            {
                return NotFound(new { error = "User not found" });
            }

            await _userService.UpdatePreferencesAsync(user.Id, request.Preferences);

            // Invalidate cache
            var db = _redis.GetDatabase();
            await db.KeyDeleteAsync($"user:profile:{userId}");

            // Send event
            await _kafkaProducer.ProduceAsync("user-profiles", userId, new
            {
                event_type = "preferences_updated",
                user_id = userId,
                timestamp = DateTime.UtcNow,
                preferences = request.Preferences
            });

            return Ok(new { message = "Preferences updated successfully" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating preferences for user {UserId}", userId);
            return StatusCode(500, new { error = "Failed to update preferences" });
        }
    }

    [HttpGet("{userId}/recommendations/history")]
    public async Task<IActionResult> GetRecommendationHistory(string userId, [FromQuery] int limit = 50)
    {
        try
        {
            var user = await _userService.GetUserByExternalIdAsync(userId);
            if (user == null)
            {
                return NotFound(new { error = "User not found" });
            }

            var history = await _userService.GetRecommendationHistoryAsync(user.Id, limit);
            return Ok(history);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting recommendation history for user {UserId}", userId);
            return StatusCode(500, new { error = "Failed to get recommendation history" });
        }
    }

    [HttpDelete("{userId}")]
    public async Task<IActionResult> DeleteUser(string userId)
    {
        try
        {
            var user = await _userService.GetUserByExternalIdAsync(userId);
            if (user == null)
            {
                return NotFound(new { error = "User not found" });
            }

            await _userService.DeleteUserAsync(user.Id);

            // Clear cache
            var db = _redis.GetDatabase();
            await db.KeyDeleteAsync($"user:profile:{userId}");

            // Send deletion event
            await _kafkaProducer.ProduceAsync("user-profiles", userId, new
            {
                event_type = "user_deleted",
                user_id = userId,
                timestamp = DateTime.UtcNow
            });

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting user {UserId}", userId);
            return StatusCode(500, new { error = "Failed to delete user" });
        }
    }
}