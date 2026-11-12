using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using TH3.Models;
 
namespace TH3.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ChatController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
 
        public ChatController(ApplicationDbContext context)
        {
            _context = context;
        }
 
        /// <summary>
        /// AI search endpoint - tìm sản phẩm dựa theo mô tả
        /// </summary>
        [HttpPost("search")]
        public async Task<IActionResult> SearchProducts([FromBody] ChatSearchRequest request)
        {
            if (string.IsNullOrWhiteSpace(request.Query))
                return BadRequest(new { message = "Vui lòng nhập từ khóa tìm kiếm." });
 
            var query = request.Query.ToLower().Trim();
 
            // Lấy tất cả sản phẩm
            var products = await _context.Products
                .Include(p => p.Category)
                .ToListAsync();
 
            // Thuật toán tìm kiếm thông minh dựa theo keyword
            var scored = products
                .Select(p => new
                {
                    Product = p,
                    Score = CalculateRelevanceScore(p, query)
                })
                .Where(x => x.Score > 0)
                .OrderByDescending(x => x.Score)
                .Take(5)
                .ToList();
 
            if (!scored.Any())
            {
                // Fallback: tìm theo tên hoặc mô tả
                var fallback = products
                    .Where(p =>
                        (p.Name != null && p.Name.ToLower().Contains(query)) ||
                        (p.Description != null && p.Description.ToLower().Contains(query)))
                    .Take(3)
                    .ToList();
 
                if (!fallback.Any())
                {
                    return Ok(new ChatSearchResponse
                    {
                        Found = false,
                        Message = $"Xin lỗi, tôi không tìm thấy sản phẩm phù hợp với yêu cầu \"{request.Query}\". Bạn có thể:\n• Thử mô tả chi tiết hơn (vd: điện thoại pin trâu dưới 10 triệu)\n• Gõ **chat admin** để được tư vấn trực tiếp",
                        Products = new List<ProductResult>()
                    });
                }
 
                scored = fallback.Select(p => new { Product = p, Score = 1 }).ToList();
            }
 
            var results = scored.Select(x => new ProductResult
            {
                Id = x.Product.Id,
                Name = x.Product.Name ?? "",
                Price = x.Product.Price,
                Description = x.Product.Description ?? "",
                ImageUrl = x.Product.ImageUrl ?? "",
                CategoryName = x.Product.Category?.Name ?? "",
                Url = $"/Product/Display/{x.Product.Id}"
            }).ToList();
 
            var responseMsg = GenerateAIResponse(query, results);
 
            return Ok(new ChatSearchResponse
            {
                Found = true,
                Message = responseMsg,
                Products = results
            });
        }
 
        private int CalculateRelevanceScore(Product product, string query)
        {
            int score = 0;
            var name = (product.Name ?? "").ToLower();
            var desc = (product.Description ?? "").ToLower();
            var catName = (product.Category?.Name ?? "").ToLower();
 
            // Tách từ khóa
            var keywords = query.Split(' ', StringSplitOptions.RemoveEmptyEntries);
 
            foreach (var kw in keywords)
            {
                if (name.Contains(kw)) score += 10;
                if (desc.Contains(kw)) score += 5;
                if (catName.Contains(kw)) score += 8;
            }
 
            // Tìm theo giá
            if (query.Contains("rẻ") || query.Contains("giá rẻ") || query.Contains("tiết kiệm"))
            {
                if (product.Price < 5000000) score += 15;
            }
            if (query.Contains("cao cấp") || query.Contains("xịn") || query.Contains("flagship"))
            {
                if (product.Price > 15000000) score += 15;
            }
            if (query.Contains("tầm trung"))
            {
                if (product.Price >= 5000000 && product.Price <= 15000000) score += 15;
            }
 
            // Xử lý khoảng giá "dưới X triệu"
            var duoiMatch = System.Text.RegularExpressions.Regex.Match(query, @"dưới\s*(\d+)\s*triệu");
            if (duoiMatch.Success && int.TryParse(duoiMatch.Groups[1].Value, out int maxTrieu))
            {
                if (product.Price <= maxTrieu * 1000000) score += 20;
            }
 
            // Brand detection
            var brands = new[] { "samsung", "apple", "iphone", "xiaomi", "oppo", "vivo", "realme", "nokia", "sony" };
            foreach (var brand in brands)
            {
                if (query.Contains(brand) && (name.Contains(brand) || desc.Contains(brand)))
                    score += 25;
            }
 
            return score;
        }
 
        private string GenerateAIResponse(string query, List<ProductResult> results)
        {
            if (results.Count == 0)
                return "Tôi không tìm thấy sản phẩm phù hợp.";
 
            var responses = new List<string>
            {
                $"Tôi tìm thấy {results.Count} sản phẩm phù hợp với yêu cầu của bạn:",
                $"Dựa trên mô tả \"{query}\", đây là những gợi ý tốt nhất cho bạn:",
                $"Tuyệt vời! Tôi có {results.Count} sản phẩm có thể đáp ứng nhu cầu của bạn:"
            };
 
            var rnd = new Random();
            return responses[rnd.Next(responses.Count)];
        }
    }
 
    public class ChatSearchRequest
    {
        public string Query { get; set; } = "";
    }
 
    public class ChatSearchResponse
    {
        public bool Found { get; set; }
        public string Message { get; set; } = "";
        public List<ProductResult> Products { get; set; } = new();
    }
 
    public class ProductResult
    {
        public int Id { get; set; }
        public string Name { get; set; } = "";
        public decimal Price { get; set; }
        public string Description { get; set; } = "";
        public string ImageUrl { get; set; } = "";
        public string CategoryName { get; set; } = "";
        public string Url { get; set; } = "";
    }
}