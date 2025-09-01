// services/user-service/Models/User.cs
namespace UserService.Models;

public class User
{
    public int Id { get; set; }
    public string ExternalId { get; set; } = string.Empty;
    public string Username { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public UserProfile? Profile { get; set; }
    public List<UserInteraction> Interactions { get; set; } = new();
    public List<UserPreference> Preferences { get; set; } = new();
}

public class UserProfile
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public User User { get; set; } = null!;
    public int? Age { get; set; }
    public string? Gender { get; set; }
    public string? Location { get; set; }
    public string? Interests { get; set; }
    public Dictionary<string, object> Metadata { get; set; } = new();
    public DateTime UpdatedAt { get; set; }
}

public class UserInteraction
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public User User { get; set; } = null!;
    public string ItemId { get; set; } = string.Empty;
    public string InteractionType { get; set; } = string.Empty;
    public double? Rating { get; set; }
    public DateTime Timestamp { get; set; }
    public Dictionary<string, object>? Metadata { get; set; }
}

public class UserPreference
{
    public int Id { get; set; }
    public int UserId { get; set; }
    public User User { get; set; } = null!;
    public string Category { get; set; } = string.Empty;
    public double Weight { get; set; }
    public List<string> Tags { get; set; } = new();
    public DateTime UpdatedAt { get; set; }
}