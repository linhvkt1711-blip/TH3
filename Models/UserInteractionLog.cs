namespace TH3.Models
{
    public class UserInteractionLog
    {
        public int Id { get; set; }
        public string UserId { get; set; } = string.Empty;
        public int ProductId { get; set; }
        public string Action { get; set; } = "View";
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }
}
