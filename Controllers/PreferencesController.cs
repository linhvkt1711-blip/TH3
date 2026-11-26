using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using TH3.Models;

namespace TH3.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]
    public class PreferencesController : ControllerBase
    {
        private readonly ApplicationDbContext _db;
        private readonly UserManager<ApplicationUser> _userManager;

        public PreferencesController(ApplicationDbContext db, UserManager<ApplicationUser> userManager)
        {
            _db = db;
            _userManager = userManager;
        }

        // GET /api/preferences/me
        [HttpGet("me")]
        public async Task<IActionResult> GetMyPreferences()
        {
            var userId = _userManager.GetUserId(User);
            if (string.IsNullOrEmpty(userId))
                return Unauthorized();

            var pref = await _db.UserPreferences
                .FirstOrDefaultAsync(p => p.UserId == userId);

            if (pref == null)
                return Ok(new { hasPreferences = false });

            return Ok(new
            {
                hasPreferences = true,
                style = pref.PreferredStyle,
                material = pref.PreferredMaterial,
                priceTier = pref.PreferredPriceTier,
                purpose = pref.PreferredPurpose,
                updatedAt = pref.UpdatedAt
            });
        }

        // POST /api/preferences
        [HttpPost]
        public async Task<IActionResult> SavePreferences([FromBody] PreferenceRequest request)
        {
            var userId = _userManager.GetUserId(User);
            if (string.IsNullOrEmpty(userId))
                return Unauthorized();

            var pref = await _db.UserPreferences
                .FirstOrDefaultAsync(p => p.UserId == userId);

            if (pref == null)
            {
                pref = new UserPreference { UserId = userId };
                _db.UserPreferences.Add(pref);
            }

            pref.PreferredStyle    = request.Style ?? pref.PreferredStyle;
            pref.PreferredMaterial = request.Material ?? pref.PreferredMaterial;
            pref.PreferredPriceTier = request.PriceTier ?? pref.PreferredPriceTier;
            pref.PreferredPurpose  = request.Purpose ?? pref.PreferredPurpose;
            pref.UpdatedAt = DateTime.UtcNow;

            await _db.SaveChangesAsync();
            return Ok(new { success = true, message = "Đã lưu sở thích thành công!" });
        }

        // DELETE /api/preferences/me  — reset preferences
        [HttpDelete("me")]
        public async Task<IActionResult> DeletePreferences()
        {
            var userId = _userManager.GetUserId(User);
            if (string.IsNullOrEmpty(userId)) return Unauthorized();

            var pref = await _db.UserPreferences.FirstOrDefaultAsync(p => p.UserId == userId);
            if (pref != null)
            {
                _db.UserPreferences.Remove(pref);
                await _db.SaveChangesAsync();
            }
            return Ok(new { success = true });
        }
    }

    public class PreferenceRequest
    {
        public string? Style    { get; set; }
        public string? Material { get; set; }
        public string? PriceTier { get; set; }
        public string? Purpose  { get; set; }
    }
}
