// services/user-service/Services/UserService.cs
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using UserService.Data;
using UserService.Models;

namespace UserService.Services;

public interface IUserService
{
    Task<User?> GetUserByExternalIdAsync(string externalId);
    Task<User> CreateUserAsync(User user);
    Task AddInteractionAsync(UserInteraction interaction);
    Task UpdateUserPreferencesAsync(int userId, UserInteraction interaction);
    Task UpdatePreferencesAsync(int userId, List<PreferenceDto> preferences);
    Task<List<RecommendationHistoryItem>> GetRecommendationHistoryAsync(int userId, int limit);
    Task DeleteUserAsync(int userId);
}

public class UserService : IUserService
{
    private readonly UserDbContext _context;
    private readonly ILogger<UserService> _logger;

    public UserService(UserDbContext context, ILogger<UserService> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<User?> GetUserByExternalIdAsync(string externalId)
    {
        return await _context.Users
            .Include(u => u.Profile)
            .Include(u => u.Preferences)
            .Include(u => u.Interactions.OrderByDescending(i => i.Timestamp).Take(100))
            .FirstOrDefaultAsync(u => u.ExternalId == externalId);
    }

    public async Task<User> CreateUserAsync(User user)
    {
        user.CreatedAt = DateTime.UtcNow;
        user.UpdatedAt = DateTime.UtcNow;
        
        _context.Users.Add(user);
        await _context.SaveChangesAsync();
        
        _logger.LogInformation("Created new user with ID {UserId}", user.ExternalId);
        return user;
    }

    public async Task AddInteractionAsync(UserInteraction interaction)
    {
        _context.UserInteractions.Add(interaction);
        await _context.SaveChangesAsync();
    }

    public async Task UpdateUserPreferencesAsync(int userId, UserInteraction interaction)
    {
        // Update preferences based on interaction
        var existingPrefs = await _context.UserPreferences
            .Where(p => p.UserId == userId)
            .ToListAsync();

        // Simple preference update logic - can be made more sophisticated
        if (interaction.Rating.HasValue && interaction.Rating.Value >= 4)
        {
            // User liked this item - boost related categories
            var category = await DetermineItemCategory(interaction.ItemId);
            
            var pref = existingPrefs.FirstOrDefault(p => p.Category == category);
            if (pref != null)
            {
                pref.Weight = Math.Min(1.0, pref.Weight + 0.1);
                pref.UpdatedAt = DateTime.UtcNow;
            }
            else
            {
                _context.UserPreferences.Add(new UserPreference
                {
                    UserId = userId,
                    Category = category,
                    Weight = 0.6,
                    UpdatedAt = DateTime.UtcNow
                });
            }
        }
        else if (interaction.Rating.HasValue && interaction.Rating.Value <= 2)
        {
            // User disliked this item - reduce category weight
            var category = await DetermineItemCategory(interaction.ItemId);
            
            var pref = existingPrefs.FirstOrDefault(p => p.Category == category);
            if (pref != null)
            {
                pref.Weight = Math.Max(0.0, pref.Weight - 0.1);
                pref.UpdatedAt = DateTime.UtcNow;
            }
        }

        await _context.SaveChangesAsync();
    }

    public async Task UpdatePreferencesAsync(int userId, List<PreferenceDto> preferences)
    {
        // Remove existing preferences
        var existing = await _context.UserPreferences
            .Where(p => p.UserId == userId)
            .ToListAsync();
        
        _context.UserPreferences.RemoveRange(existing);

        // Add new preferences
        foreach (var pref in preferences)
        {
            _context.UserPreferences.Add(new UserPreference
            {
                UserId = userId,
                Category = pref.Category,
                Weight = pref.Weight,
                Tags = pref.Tags,
                UpdatedAt = DateTime.UtcNow
            });
        }

        await _context.SaveChangesAsync();
    }

    public async Task<List<RecommendationHistoryItem>> GetRecommendationHistoryAsync(int userId, int limit)
    {
        // This would typically query a separate recommendations history table
        // For now, returning mock data based on interactions
        var interactions = await _context.UserInteractions
            .Where(i => i.UserId == userId)
            .OrderByDescending(i => i.Timestamp)
            .Take(limit)
            .Select(i => new RecommendationHistoryItem
            {
                RecommendationId = Guid.NewGuid().ToString(),
                ItemIds = new List<string> { i.ItemId },
                Strategy = "interaction-based",
                Timestamp = i.Timestamp
            })
            .ToListAsync();

        return interactions;
    }

    public async Task DeleteUserAsync(int userId)
    {
        var user = await _context.Users.FindAsync(userId);
        if (user != null)
        {
            _context.Users.Remove(user);
            await _context.SaveChangesAsync();
            _logger.LogInformation("Deleted user with ID {UserId}", user.ExternalId);
        }
    }

    private async Task<string> DetermineItemCategory(string itemId)
    {
        // This would typically call an external service or database
        // to get the actual category of the item
        // For demo purposes, using a simple hash-based assignment
        var categories = new[] { "electronics", "books", "clothing", "food", "sports", "home", "toys" };
        var hash = itemId.GetHashCode();
        var index = Math.Abs(hash) % categories.Length;
        return await Task.FromResult(categories[index]);
    }
}