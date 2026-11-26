using System.ComponentModel.DataAnnotations;

namespace TH3.Models
{
    public class UserPreference
    {
        public int Id { get; set; }

        [Required]
        public string UserId { get; set; } = string.Empty;

        // Phong cách: "minimalist", "luxury", "sporty", "cute"
        [MaxLength(50)]
        public string PreferredStyle { get; set; } = "";

        // Chất liệu: "silicone", "leather", "tpu", "clear"
        [MaxLength(50)]
        public string PreferredMaterial { get; set; } = "";

        // Khoảng giá: "budget", "mid", "premium"
        [MaxLength(20)]
        public string PreferredPriceTier { get; set; } = "";

        // Mục đích: "protection", "aesthetic", "slim", "rugged"
        [MaxLength(50)]
        public string PreferredPurpose { get; set; } = "";

        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    }
}
