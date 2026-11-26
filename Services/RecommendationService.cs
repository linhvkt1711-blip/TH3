using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
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

        public string Category { get; set; } = "Ốp lưng";

        public string DeviceCode { get; set; } = "";

        public double Score { get; set; }
    }

    public class RecommendationService
    {
        private readonly ApplicationDbContext _context;

        public RecommendationService(ApplicationDbContext context)
        {
            _context = context;
        }

        public async Task<List<RecommendationResult>> GetRecommendations(string userId, string? targetDeviceCode = null)
        {
            var products = await _context.Products.Include(p => p.Category).ToListAsync();
            var logs = await _context.UserInteractionLogs
                .Where(x => x.UserId == userId)
                .ToListAsync();

            var user = await _context.Users.FirstOrDefaultAsync(u => u.Id == userId);
            var userPref = await _context.UserPreferences.FirstOrDefaultAsync(p => p.UserId == userId);

            var historyList = new List<object>();
            foreach (var log in logs)
            {
                var p = products.FirstOrDefault(p => p.Id == log.ProductId);
                if (p != null)
                {
                    historyList.Add(new {
                        product_id = p.Id,
                        category = p.Category?.Name ?? "Ốp lưng",
                        brand = p.Name,
                        device_code = p.CompatibleDeviceCode ?? "",
                        action = log.InteractionType ?? "view"
                    });
                }
            }

            var productList = products.Select(p => new {
                product_id = p.Id,
                name = p.Name,
                category = p.Category?.Name ?? "Ốp lưng",
                price = p.Price,
                image = p.ImageUrl ?? "",
                compatible_device_code = p.CompatibleDeviceCode ?? "",
                material = p.MaterialType ?? "Silicone",
                description = p.Description ?? ""
            }).ToList();

            var explicitPrefs = userPref != null ? new {
                style = userPref.PreferredStyle,
                material = userPref.PreferredMaterial,
                price_tier = userPref.PreferredPriceTier,
                purpose = userPref.PreferredPurpose
            } : null;

            var payload = new {
                user = new {
                    user_id = userId,
                    age = user?.Age ?? "0",
                    device_code = targetDeviceCode ?? ""
                },
                products = productList,
                history = historyList,
                target_device_code = targetDeviceCode ?? "",
                explicit_preferences = explicitPrefs
            };

            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            // 1. Thử gọi qua Python AI Service (FastAPI port 5001)
            try
            {
                using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(3) };
                var response = await client.PostAsync("http://localhost:5001/recommend", content);
                
                if (response.IsSuccessStatusCode)
                {
                    var responseString = await response.Content.ReadAsStringAsync();
                    var results = JsonSerializer.Deserialize<List<RecommendationResult>>(
                        responseString, 
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );
                    if (results != null && results.Count > 0)
                    {
                        return results;
                    }
                }
            }
            catch (Exception)
            {
                // Fallback tính toán nội bộ C# nếu AI service đang offline
            }

            // 2. Fallback: Thuật toán Hybrid Cosine Similarity (60% Implicit + 40% Explicit) viết trực tiếp bằng C#
            return ComputeInternalCosineRecommendations(products, logs, targetDeviceCode, userPref);
        }

        private List<RecommendationResult> ComputeInternalCosineRecommendations(
            List<Product> products, 
            List<UserInteractionLog> logs, 
            string? targetDeviceCode,
            UserPreference? userPref = null)
        {
            if (products.Count == 0) return new List<RecommendationResult>();

            // Lọc cứng theo thiết bị nếu có chỉ định
            var normalizedDevice = (targetDeviceCode ?? "").Trim().ToUpper();
            var candidates = products.ToList();
            if (!string.IsNullOrEmpty(normalizedDevice))
            {
                var compatible = products.Where(p => 
                    (p.CompatibleDeviceCode ?? "").Trim().ToUpper() == normalizedDevice
                ).ToList();
                if (compatible.Count > 0)
                {
                    candidates = compatible;
                }
            }

            // Vector từ vựng đặc trưng: [silicone, da, tpu, trong suot, chong soc, magsafe, gia re, gia trung, cao cap]
            var userVector = new double[9];
            double totalWeight = 0.0;

            foreach (var log in logs)
            {
                var p = products.FirstOrDefault(x => x.Id == log.ProductId);
                if (p != null)
                {
                    var pVec = VectorizeProduct(p);
                    double weight = log.InteractionType?.ToLower() switch {
                        "purchase" or "buy" => 10.0,
                        "addtocart" or "cart" => 5.0,
                        "tryon3d" or "tryon" => 3.0,
                        _ => 1.0
                    };
                    for (int i = 0; i < 9; i++) userVector[i] += pVec[i] * weight;
                    totalWeight += weight;
                }
            }

            if (totalWeight > 0)
            {
                for (int i = 0; i < 9; i++) userVector[i] /= totalWeight;
            }
            else
            {
                // Mặc định cho khách mới (trong suốt, chống sốc, giá tầm trung)
                userVector[3] = 1.0; // trong suốt
                userVector[4] = 1.0; // chống sốc
                userVector[0] = 1.0; // silicone
                userVector[7] = 1.0; // giá trung bình
            }

            var explicitVec = BuildExplicitPreferenceVector(userPref);
            bool hasExplicit = explicitVec.Any(v => v > 0.0);

            var scored = new List<RecommendationResult>();
            foreach (var p in candidates)
            {
                var pVec = VectorizeProduct(p);
                double implicitScore = CalculateCosine(userVector, pVec);
                double score = hasExplicit
                    ? 0.60 * implicitScore + 0.40 * CalculateCosine(explicitVec, pVec)
                    : implicitScore;

                // Thưởng điểm tương thích dòng máy
                if (!string.IsNullOrEmpty(normalizedDevice) && 
                    (p.CompatibleDeviceCode ?? "").Trim().ToUpper() == normalizedDevice)
                {
                    score = Math.Min(1.0, score * 1.15 + 0.10);
                }

                scored.Add(new RecommendationResult {
                    ProductId = p.Id,
                    Name = p.Name,
                    Price = p.Price,
                    ImageUrl = p.ImageUrl ?? "",
                    Category = p.Category?.Name ?? "Ốp lưng",
                    DeviceCode = p.CompatibleDeviceCode ?? "",
                    Score = Math.Round(score, 4)
                });
            }

            return scored.OrderByDescending(x => x.Score).Take(5).ToList();
        }

        private static double[] BuildExplicitPreferenceVector(UserPreference? pref)
        {
            var vec = new double[9];
            if (pref == null) return vec;

            var style = (pref.PreferredStyle ?? "").Trim().ToLower();
            if (style == "sporty") { vec[4] = Math.Max(vec[4], 1.0); vec[2] = Math.Max(vec[2], 0.5); }
            else if (style == "luxury") { vec[1] = Math.Max(vec[1], 1.0); vec[8] = Math.Max(vec[8], 0.9); }
            else if (style == "minimalist") { vec[3] = Math.Max(vec[3], 0.8); vec[7] = Math.Max(vec[7], 0.5); }
            else if (style == "cute") { vec[6] = Math.Max(vec[6], 0.6); }

            var mat = (pref.PreferredMaterial ?? "").Trim().ToLower();
            if (mat == "silicone") vec[0] = Math.Max(vec[0], 1.0);
            else if (mat == "leather") vec[1] = Math.Max(vec[1], 1.0);
            else if (mat == "tpu") vec[2] = Math.Max(vec[2], 1.0);
            else if (mat == "clear") { vec[3] = Math.Max(vec[3], 1.0); vec[0] = Math.Max(vec[0], 0.5); }

            var price = (pref.PreferredPriceTier ?? "").Trim().ToLower();
            if (price == "budget") vec[6] = Math.Max(vec[6], 1.0);
            else if (price == "mid") vec[7] = Math.Max(vec[7], 1.0);
            else if (price == "premium") vec[8] = Math.Max(vec[8], 1.0);

            var purpose = (pref.PreferredPurpose ?? "").Trim().ToLower();
            if (purpose == "protection") { vec[4] = Math.Max(vec[4], 1.0); vec[2] = Math.Max(vec[2], 0.5); }
            else if (purpose == "aesthetic") { vec[1] = Math.Max(vec[1], 0.5); }
            else if (purpose == "rugged") { vec[4] = Math.Max(vec[4], 1.0); vec[2] = Math.Max(vec[2], 0.8); }

            return vec;
        }

        private static double[] VectorizeProduct(Product p)
        {
            var text = $"{p.Name} {p.Description} {p.MaterialType} {p.Category?.Name}".ToLower();
            var vec = new double[9];
            vec[0] = text.Contains("silicone") || text.Contains("dẻo") ? 1.0 : 0.0;
            vec[1] = text.Contains("da") || text.Contains("leather") ? 1.0 : 0.0;
            vec[2] = text.Contains("tpu") || text.Contains("nhựa") ? 1.0 : 0.0;
            vec[3] = text.Contains("trong suốt") || text.Contains("clear") || text.Contains("chống ố") ? 1.0 : 0.0;
            vec[4] = text.Contains("chống sốc") || text.Contains("armor") || text.Contains("quân đội") ? 1.0 : 0.0;
            vec[5] = text.Contains("magsafe") || text.Contains("nam châm") ? 1.0 : 0.0;
            vec[6] = p.Price < 150000 ? 1.0 : 0.0;
            vec[7] = p.Price >= 150000 && p.Price <= 350000 ? 1.0 : 0.0;
            vec[8] = p.Price > 350000 ? 1.0 : 0.0;
            return vec;
        }

        private static double CalculateCosine(double[] v1, double[] v2)
        {
            double dot = 0, n1 = 0, n2 = 0;
            for (int i = 0; i < v1.Length; i++)
            {
                dot += v1[i] * v2[i];
                n1 += v1[i] * v1[i];
                n2 += v2[i] * v2[i];
            }
            if (n1 == 0 || n2 == 0) return 0.0;
            return dot / (Math.Sqrt(n1) * Math.Sqrt(n2));
        }
    }
}
