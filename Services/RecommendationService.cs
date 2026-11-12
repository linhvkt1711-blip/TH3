using Microsoft.EntityFrameworkCore;
using TH3.Models;

namespace TH3.Services
{
    public class RecommendationResult
    {
        public int ProductId { get; set; }

        public string Name { get; set; } = "";

        public decimal Price { get; set; }

        public string ImageUrl { get; set; } = "";

        public double Score { get; set; }
    }

    public class RecommendationService
    {
        private readonly ApplicationDbContext _context;

        public RecommendationService(ApplicationDbContext context)
        {
            _context = context;
        }

        public async Task<List<RecommendationResult>> GetRecommendations(string userId)
        {
            var products = await _context.Products.Include(p => p.Category).ToListAsync();
            var logs = await _context.UserInteractionLogs
                .Where(x => x.UserId == userId)
                .ToListAsync();

            var user = await _context.Users.FirstOrDefaultAsync(u => u.Id == userId);
            
            var historyList = new List<object>();
            foreach (var log in logs)
            {
                var p = products.FirstOrDefault(p => p.Id == log.ProductId);
                if (p != null)
                {
                    historyList.Add(new {
                        product_id = p.Id,
                        category = p.Category?.Name ?? "",
                        brand = p.Name
                    });
                }
            }

            var productList = products.Select(p => new {
                product_id = p.Id,
                name = p.Name,
                category = p.Category?.Name ?? "",
                price = p.Price,
                image = p.ImageUrl ?? ""
            }).ToList();

            var payload = new {
                user = new {
                    user_id = userId,
                    age = user?.Age ?? "0"
                },
                products = productList,
                history = historyList
            };

            var json = System.Text.Json.JsonSerializer.Serialize(payload);
            var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

            try
            {
                using var client = new HttpClient();
                var response = await client.PostAsync("http://localhost:5000/recommend", content);
                
                if (response.IsSuccessStatusCode)
                {
                    var responseString = await response.Content.ReadAsStringAsync();
                    var results = System.Text.Json.JsonSerializer.Deserialize<List<RecommendationResult>>(
                        responseString, 
                        new System.Text.Json.JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );
                    if (results != null && results.Count > 0)
                    {
                        return results;
                    }
                }
            }
            catch (Exception)
            {
                // Fallback to basic random if API is down
            }

            // Fallback
            return products.OrderBy(x => Guid.NewGuid()).Take(5).Select(p => new RecommendationResult {
                ProductId = p.Id,
                Name = p.Name,
                Price = p.Price,
                ImageUrl = p.ImageUrl ?? "",
                Score = 0
            }).ToList();
        }
    }
}