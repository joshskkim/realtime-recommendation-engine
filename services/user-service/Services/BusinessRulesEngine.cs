// services/user-service/Services/BusinessRulesEngine.cs
using UserService.Models;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace UserService.Services;

public interface IBusinessRulesEngine
{
    bool ValidateUserCreation(CreateUserRequest request);
    RecordInteractionRequest ProcessInteraction(RecordInteractionRequest request);
    RecommendationRequest ApplyUserSegmentRules(string userId, RecommendationRequest request);
}

public class BusinessRulesEngine : IBusinessRulesEngine
{
    private readonly ILogger<BusinessRulesEngine> _logger;
    private readonly IConfiguration _configuration;

    public BusinessRulesEngine(ILogger<BusinessRulesEngine> logger, IConfiguration configuration)
    {
        _logger = logger;
        _configuration = configuration;
    }

    public bool ValidateUserCreation(CreateUserRequest request)
    {
        // Apply business rules for user creation
        if (string.IsNullOrWhiteSpace(request.Username) || request.Username.Length < 3)
        {
            _logger.LogWarning("User creation failed: Invalid username");
            return false;
        }

        if (!IsValidEmail(request.Email))
        {
            _logger.LogWarning("User creation failed: Invalid email");
            return false;
        }

        if (request.Age.HasValue && (request.Age < 13 || request.Age > 120))
        {
            _logger.LogWarning("User creation failed: Invalid age");
            return false;
        }

        // Check for prohibited usernames
        var prohibitedUsernames = _configuration.GetSection("BusinessRules:ProhibitedUsernames").Get<string[]>() 
            ?? new[] { "admin", "root", "system" };
        
        if (prohibitedUsernames.Contains(request.Username.ToLower()))
        {
            _logger.LogWarning("User creation failed: Prohibited username");
            return false;
        }

        return true;
    }

    public RecordInteractionRequest ProcessInteraction(RecordInteractionRequest request)
    {
        // Apply business rules to interactions
        
        // Normalize ratings to 0-5 scale
        if (request.Rating.HasValue)
        {
            request.Rating = Math.Max(0, Math.Min(5, request.Rating.Value));
        }

        // Add metadata based on interaction type
        request.Metadata ??= new Dictionary<string, object>();
        
        switch (request.InteractionType.ToLower())
        {
            case "purchase":
                request.Metadata["weight"] = 5.0;
                request.Metadata["confidence"] = 1.0;
                break;
            case "add_to_cart":
                request.Metadata["weight"] = 3.0;
                request.Metadata["confidence"] = 0.7;
                break;
            case "view":
                request.Metadata["weight"] = 1.0;
                request.Metadata["confidence"] = 0.3;
                // Track view duration if provided
                if (request.Metadata.ContainsKey("duration_seconds"))
                {
                    var duration = Convert.ToDouble(request.Metadata["duration_seconds"]);
                    // Increase weight for longer views
                    if (duration > 30)
                    {
                        request.Metadata["weight"] = 1.5;
                        request.Metadata["confidence"] = 0.5;
                    }
                }
                break;
            case "like":
                request.Metadata["weight"] = 2.0;
                request.Metadata["confidence"] = 0.8;
                break;
            case "share":
                request.Metadata["weight"] = 2.5;
                request.Metadata["confidence"] = 0.9;
                break;
            case "dislike":
                request.Metadata["weight"] = 2.0;
                request.Metadata["confidence"] = 0.8;
                request.Metadata["negative"] = true;
                break;
        }

        // Add timestamp if not present
        if (!request.Metadata.ContainsKey("processed_at"))
        {
            request.Metadata["processed_at"] = DateTime.UtcNow;
        }

        // Add client info if available
        if (!request.Metadata.ContainsKey("client_type"))
        {
            request.Metadata["client_type"] = "web"; // Default to web
        }

        return request;
    }

    public RecommendationRequest ApplyUserSegmentRules(string userId, RecommendationRequest request)
    {
        // Apply business rules based on user segmentation
        
        // Example: New users get more popular items
        if (IsNewUser(userId))
        {
            request.BoostPopular = true;
            request.PopularityWeight = 0.7;
            request.DiversityFactor = 0.3; // Less diversity for new users
        }

        // Example: Premium users get more personalized recommendations
        if (IsPremiumUser(userId))
        {
            request.PersonalizationWeight = 0.9;
            request.MaxResults = Math.Max(request.MaxResults, 20);
            request.DiversityFactor = 0.7; // More diversity for premium users
        }

        // Example: Inactive users get re-engagement recommendations
        if (IsInactiveUser(userId))
        {
            request.BoostTrending = true;
            request.IncludeExplanations = true;
        }

        return request;
    }

    private bool IsValidEmail(string email)
    {
        try
        {
            var addr = new System.Net.Mail.MailAddress(email);
            return addr.Address == email;
        }
        catch
        {
            return false;
        }
    }

    private bool IsNewUser(string userId)
    {
        // Check if user is new (created within last 7 days)
        // This would typically check the database
        // For demo purposes, returning based on userId pattern
        return userId.Contains("new", StringComparison.OrdinalIgnoreCase);
    }

    private bool IsPremiumUser(string userId)
    {
        // Check if user has premium subscription
        // This would typically check the database or external service
        // For demo purposes, returning based on configuration
        var premiumUsers = _configuration.GetSection("BusinessRules:PremiumUsers").Get<string[]>() ?? Array.Empty<string>();
        return premiumUsers.Contains(userId);
    }

    private bool IsInactiveUser(string userId)
    {
        // Check if user has been inactive for 30+ days
        // This would typically check last interaction date
        return false; // Placeholder
    }
}