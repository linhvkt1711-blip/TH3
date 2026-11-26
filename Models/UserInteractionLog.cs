using System.ComponentModel.DataAnnotations.Schema;

namespace TH3.Models
{
    public class UserInteractionLog
    {
        public int Id { get; set; }
        public string UserId { get; set; } = string.Empty;
        public int ProductId { get; set; }
        public string Action { get; set; } = "View";

        [NotMapped]
        public string InteractionType
        {
            get => Action;
            set => Action = value;
        }
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }
}
