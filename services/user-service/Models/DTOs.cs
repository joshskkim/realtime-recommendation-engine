// services/user-service/Models/DTOs.cs
namespace UserService.Models;

public class UserProfileDto
{
    public string UserId { get; set; } = string.Empty;
    public string Username { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public ProfileDto? Profile { get; set; }
    public List<PreferenceDto> Preferences { get; set; } = new();
    public List<InteractionDto> RecentInteractions { get; set; } = new();
}

public class ProfileDto
{
    public int? Age { get; set; }
    public string? Gender { get; set; }
    public string? Location { get; set; }
    public List<string> Interests { get; set; } = new();
    public Dictionary<string, object> Metadata { get; set; } = new();
}

public class PreferenceDto
{
    public string Category { get; set; } = string.Empty;
    public double Weight { get; set; }
    public List<string> Tags { get; set; } = new();
}

public class InteractionDto
{
    public string ItemId { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public double? Rating { get; set; }
    public DateTime Timestamp { get; set; }
}

public class CreateUserRequest
{
    public string Username { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public int? Age { get; set; }
    public string? Gender { get; set; }
    public string? Location { get; set; }
    public List<string>? Interests { get; set; }
}

public class RecordInteractionRequest
{
    public string ItemId { get; set; } = string.Empty;
    public string InteractionType { get; set; } = string.Empty;
    public double? Rating { get; set; }
    public Dictionary<string, object>? Metadata { get; set; }
}

public class UpdatePreferencesRequest
{
    public List<PreferenceDto> Preferences { get; set; } = new();
}

public class RecommendationRequest
{
    public int MaxResults { get; set; } = 10;
    public bool BoostPopular { get; set; }
    public bool BoostTrending { get; set; }
    public double PopularityWeight { get; set; } = 0.3;
    public double PersonalizationWeight { get; set; } = 0.7;
    public double DiversityFactor { get; set; } = 0.5;
    public bool IncludeExplanations { get; set; }
}

public class RecommendationHistoryItem
{
    public string RecommendationId { get; set; } = string.Empty;
    public List<string> ItemIds { get; set; } = new();
    public string Strategy { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; }
}