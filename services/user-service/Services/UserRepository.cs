// services/user-service/Services/UserRepository.cs
using Microsoft.EntityFrameworkCore;
using UserService.Data;
using UserService.Models;

namespace UserService.Services;

public interface IUserRepository
{
    Task<User?> GetByExternalIdAsync(string externalId);
    Task<User?> GetByIdAsync(int id);
    Task<User> CreateAsync(User user);
    Task UpdateAsync(User user);
    Task DeleteAsync(int id);
    Task<bool> ExistsByEmailAsync(string email);
    Task<bool> ExistsByUsernameAsync(string username);
    Task<List<User>> GetInactiveUsersAsync(DateTime since);
}

public class UserRepository : IUserRepository
{
    private readonly UserDbContext _context;
    
    public UserRepository(UserDbContext context)
    {
        _context = context;
    }

    public async Task<User?> GetByExternalIdAsync(string externalId)
    {
        return await _context.Users
            .Include(u => u.Profile)
            .Include(u => u.Preferences)
            .Include(u => u.Interactions.OrderByDescending(i => i.Timestamp).Take(100))
            .FirstOrDefaultAsync(u => u.ExternalId == externalId);
    }

    public async Task<User?> GetByIdAsync(int id)
    {
        return await _context.Users
            .Include(u => u.Profile)
            .Include(u => u.Preferences)
            .FirstOrDefaultAsync(u => u.Id == id);
    }

    public async Task<User> CreateAsync(User user)
    {
        _context.Users.Add(user);
        await _context.SaveChangesAsync();
        return user;
    }

    public async Task UpdateAsync(User user)
    {
        user.UpdatedAt = DateTime.UtcNow;
        _context.Users.Update(user);
        await _context.SaveChangesAsync();
    }

    public async Task DeleteAsync(int id)
    {
        var user = await _context.Users.FindAsync(id);
        if (user != null)
        {
            _context.Users.Remove(user);
            await _context.SaveChangesAsync();
        }
    }

    public async Task<bool> ExistsByEmailAsync(string email)
    {
        return await _context.Users.AnyAsync(u => u.Email == email);
    }

    public async Task<bool> ExistsByUsernameAsync(string username)
    {
        return await _context.Users.AnyAsync(u => u.Username == username);
    }

    public async Task<List<User>> GetInactiveUsersAsync(DateTime since)
    {
        return await _context.Users
            .Include(u => u.Interactions)
            .Where(u => !u.Interactions.Any(i => i.Timestamp > since))
            .ToListAsync();
    }
}