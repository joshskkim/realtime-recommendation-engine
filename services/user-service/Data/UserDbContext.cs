// services/user-service/Data/UserDbContext.cs
using Microsoft.EntityFrameworkCore;
using UserService.Models;
using System.Text.Json;

namespace UserService.Data;

public class UserDbContext : DbContext
{
    public UserDbContext(DbContextOptions<UserDbContext> options) : base(options) { }

    public DbSet<User> Users { get; set; } = null!;
    public DbSet<UserProfile> UserProfiles { get; set; } = null!;
    public DbSet<UserInteraction> UserInteractions { get; set; } = null!;
    public DbSet<UserPreference> UserPreferences { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Set default schema
        modelBuilder.HasDefaultSchema("public");
        
        // User entity configuration
        modelBuilder.Entity<User>(entity =>
        {
            entity.ToTable("Users");
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => e.ExternalId).IsUnique();
            entity.HasIndex(e => e.Email).IsUnique();
            entity.Property(e => e.CreatedAt).HasDefaultValueSql("CURRENT_TIMESTAMP");
            entity.Property(e => e.UpdatedAt).HasDefaultValueSql("CURRENT_TIMESTAMP");
        });

        // UserProfile entity configuration
        modelBuilder.Entity<UserProfile>(entity =>
        {
            entity.ToTable("UserProfiles");
            entity.HasKey(e => e.Id);
            entity.HasOne(e => e.User)
                .WithOne(u => u.Profile)
                .HasForeignKey<UserProfile>(e => e.UserId);
            
            // Configure JSON column for Metadata
            entity.Property(e => e.Metadata)
                .HasColumnType("jsonb")
                .HasConversion(
                    v => JsonSerializer.Serialize(v, (JsonSerializerOptions?)null),
                    v => JsonSerializer.Deserialize<Dictionary<string, object>>(v, (JsonSerializerOptions?)null) ?? new Dictionary<string, object>()
                );
        });

        // UserInteraction entity configuration
        modelBuilder.Entity<UserInteraction>(entity =>
        {
            entity.ToTable("UserInteractions");
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => new { e.UserId, e.Timestamp });
            entity.HasIndex(e => e.ItemId);
            entity.HasOne(e => e.User)
                .WithMany(u => u.Interactions)
                .HasForeignKey(e => e.UserId);
            
            // Configure JSON column for Metadata
            entity.Property(e => e.Metadata)
                .HasColumnType("jsonb")
                .HasConversion(
                    v => v == null ? null : JsonSerializer.Serialize(v, (JsonSerializerOptions?)null),
                    v => v == null ? null : JsonSerializer.Deserialize<Dictionary<string, object>>(v, (JsonSerializerOptions?)null)
                );
        });

        // UserPreference entity configuration
        modelBuilder.Entity<UserPreference>(entity =>
        {
            entity.ToTable("UserPreferences");
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => new { e.UserId, e.Category });
            entity.HasOne(e => e.User)
                .WithMany(u => u.Preferences)
                .HasForeignKey(e => e.UserId);
            
            // Configure JSON column for Tags
            entity.Property(e => e.Tags)
                .HasColumnType("jsonb")
                .HasConversion(
                    v => JsonSerializer.Serialize(v, (JsonSerializerOptions?)null),
                    v => JsonSerializer.Deserialize<List<string>>(v, (JsonSerializerOptions?)null) ?? new List<string>()
                );
        });
    }
}