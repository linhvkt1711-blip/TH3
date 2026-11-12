namespace TH3.Models
{
    public class RecommendationResult
    {
        public int ProductId { get; set; }

        public string Name { get; set; } = "";

        public double Score { get; set; }

        public decimal Price { get; set; }

        public string ImageUrl { get; set; }= "";
    }
}   