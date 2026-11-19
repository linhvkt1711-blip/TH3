using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using TH3.Models;

namespace TH3.Controllers
{
    public class TryOn3DController : Controller
    {
        private readonly ApplicationDbContext _context;
        private readonly IHttpClientFactory _httpClientFactory;

        public TryOn3DController(ApplicationDbContext context, IHttpClientFactory httpClientFactory)
        {
            _context = context;
            _httpClientFactory = httpClientFactory;
        }

        // GET: /TryOn3D/Studio?productId=1&deviceSlug=iphone-15-pro
        public async Task<IActionResult> Studio(int? productId, string? deviceSlug)
        {
            Category? caseCategory = null;
            List<Product> allCases = new List<Product>();

            try
            {
                // 1. Tìm danh mục Ốp lưng
                caseCategory = await _context.Categories
                    .FirstOrDefaultAsync(c => c.Name.Contains("Ốp") || c.Name.Contains("Case"));

                int caseCatId = caseCategory?.Id ?? 0;

                // 2. Lấy danh sách TẤT CẢ các mẫu ốp lưng trong hệ thống để hiển thị trên Carousel Dock
                var caseQuery = _context.Products
                    .Include(p => p.Category)
                    .Include(p => p.ProductImages)
                    .Where(p => (caseCatId > 0 && p.CategoryId == caseCatId) || p.Name.Contains("Ốp") || p.Name.Contains("Case"));

                allCases = await caseQuery.OrderByDescending(p => p.Id).ToListAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Cảnh báo DB Studio] Không đọc được sản phẩm từ DB: {ex.Message}. Sử dụng danh sách ốp mẫu.");
            }

            // Dữ liệu mẫu dự phòng khi database chưa cấu hình hoặc tạm ngắt
            if (allCases.Count == 0)
            {
                allCases = new List<Product>
                {
                    new Product
                    {
                        Id = 1,
                        ProductCode = "IPX01",
                        Name = "Ốp Lưng iPhone X Chống Sốc Trong Suốt",
                        Price = 180000,
                        CompatibleDeviceCode = "IPX01",
                        MaterialType = "Silicone"
                    },
                    new Product
                    {
                        Id = 2,
                        ProductCode = "OL01",
                        Name = "Ốp Lưng MagSafe Chống Sốc Titan Tự Nhiên",
                        Price = 250000,
                        CompatibleDeviceCode = "IP01",
                        MaterialType = "Silicone"
                    },
                    new Product
                    {
                        Id = 3,
                        ProductCode = "IP05",
                        Name = "Ốp Lưng iPhone 16 Pro Max Armor Chống Va Đập",
                        Price = 450000,
                        CompatibleDeviceCode = "IP05",
                        MaterialType = "Silicone"
                    }
                };
            }

            Product? activeProduct = null;

            // Nếu người dùng chọn 1 sản phẩm cụ thể
            if (productId.HasValue && productId.Value > 0)
            {
                Product? requestedProduct = null;
                try
                {
                    requestedProduct = await _context.Products
                        .Include(p => p.Category)
                        .Include(p => p.ProductImages)
                        .FirstOrDefaultAsync(p => p.Id == productId.Value);
                }
                catch { }

                if (requestedProduct == null)
                {
                    requestedProduct = allCases.FirstOrDefault(p => p.Id == productId.Value);
                }

                if (requestedProduct != null)
                {
                    int caseCatId = caseCategory?.Id ?? 0;
                    if (requestedProduct.CategoryId == caseCatId || requestedProduct.Name.Contains("Ốp") || requestedProduct.ProductCode.StartsWith("OL") || requestedProduct.ProductCode.StartsWith("IP"))
                    {
                        activeProduct = requestedProduct;
                        if (string.IsNullOrWhiteSpace(deviceSlug))
                        {
                            deviceSlug = GetPhoneSlug(requestedProduct.CompatibleDeviceCode);
                        }
                    }
                    else
                    {
                        if (string.IsNullOrEmpty(deviceSlug))
                        {
                            deviceSlug = GetPhoneSlug(requestedProduct.ProductCode)
                                ?? GetPhoneSlug(requestedProduct.Name);
                        }
                        activeProduct = allCases.FirstOrDefault();
                    }
                }
            }

            // Nếu chưa có sản phẩm ốp nào được chọn, lấy mẫu ốp đầu tiên
            if (activeProduct == null)
            {
                activeProduct = allCases.FirstOrDefault();
            }

            // Trường hợp dự phòng nếu database chưa có ốp lưng
            if (activeProduct == null)
            {
                activeProduct = new Product
                {
                    Id = 9999,
                    Name = "Ốp Lưng iPhone 15 Pro MagSafe Trong Suốt Chống Ố (OL01)",
                    Price = 350000,
                    Description = "Mã: OL01 | Tương thích: iPhone 15 Pro (IP01). Khung viền TPU trong suốt 100%, bảo vệ cụm camera, tích hợp nam châm MagSafe hít cực mạnh.",
                    ImageUrl = "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500"
                };
            }

            // Mặc định nạp iPhone X nếu người dùng truy cập trực tiếp Studio
            var targetSlug = string.IsNullOrWhiteSpace(deviceSlug) ? "iphone-x" : deviceSlug;
            var phone = PhoneModel.DefaultPhones.FirstOrDefault(p => p.Slug.Equals(targetSlug, StringComparison.OrdinalIgnoreCase));

            // 4. Chỉ hiển thị các mẫu ốp CHUẨN XÁC của dòng máy đang chọn (Tuyệt đối không hiện ốp của máy khác)
            var compatibleCases = phone != null
                ? allCases.Where(p => IsCaseMatchingPhone(p, phone)).ToList()
                : allCases;

            // Nếu ốp đang chọn không tương thích, tự chuyển sang mẫu tương thích đầu tiên.
            if (activeProduct.Id != 9999
                && phone != null
                && !string.IsNullOrWhiteSpace(activeProduct.CompatibleDeviceCode)
                && !activeProduct.CompatibleDeviceCode.Equals(phone.DeviceCode, StringComparison.OrdinalIgnoreCase))
            {
                activeProduct = compatibleCases.FirstOrDefault() ?? new Product
                {
                    Id = 9999,
                    ProductCode = "OL01",
                    Name = $"Ốp lưng mẫu tương thích {phone.Name}",
                    Price = 0,
                    CompatibleDeviceCode = phone.DeviceCode,
                    MaterialType = "Silicone"
                };
            }
            else if (activeProduct.Id == 9999 && compatibleCases.Count > 0)
            {
                activeProduct = compatibleCases[0];
            }

            var relatedCases = compatibleCases.Where(p => p.Id != activeProduct.Id).ToList();

            ViewBag.CurrentProduct = activeProduct;
            ViewBag.PhoneModel = phone;
            ViewBag.RelatedCases = relatedCases;
            ViewBag.AllCases = compatibleCases;

            return View();
        }

        // Kiểm tra xem một sản phẩm ốp lưng có thật sự dành riêng cho dòng điện thoại này không
        private static bool IsCaseMatchingPhone(Product product, PhoneModel phone)
        {
            if (product == null || phone == null) return false;

            // 1. Nếu có gán mã thiết bị tương thích cụ thể
            if (!string.IsNullOrWhiteSpace(product.CompatibleDeviceCode))
            {
                return product.CompatibleDeviceCode.Equals(phone.DeviceCode, StringComparison.OrdinalIgnoreCase);
            }

            // 2. Dự phòng: phân tích theo tên sản phẩm để tránh trường hợp sót mã
            var productName = (product.Name ?? string.Empty).ToLower();
            var phoneCode = (phone.DeviceCode ?? string.Empty).ToUpper();

            if (phoneCode == "IPX01") // iPhone X / Xs / 10
                return productName.Contains("iphone x") || productName.Contains("iphone 10") || productName.Contains("ipx");

            if (phoneCode == "IPXR") // iPhone XR
                return productName.Contains("iphone xr") || productName.Contains("ipxr");

            if (phoneCode == "IP11") // iPhone 11 (thường)
                return productName.Contains("iphone 11") && !productName.Contains("pro") && !productName.Contains("prm");

            if (phoneCode == "IP11PM") // iPhone 11 Pro Max
                return productName.Contains("11 pro max") || productName.Contains("11 prm");

            if (phoneCode == "IP12") // iPhone 12 / 12 Pro
                return (productName.Contains("iphone 12") || productName.Contains("ip12")) && !productName.Contains("mini") && !productName.Contains("max");

            if (phoneCode == "IP12PM")
                return productName.Contains("12 pro max") || productName.Contains("12 prm");

            if (phoneCode == "IP13") // iPhone 13
                return (productName.Contains("iphone 13") || productName.Contains("ip13")) && !productName.Contains("pro") && !productName.Contains("max");

            if (phoneCode == "IP13PM") // iPhone 13 Pro Max
                return productName.Contains("13 pro max") || productName.Contains("13 prm");

            if (phoneCode == "IP14PM") // iPhone 14 Pro Max
                return productName.Contains("14 pro max") || productName.Contains("14 prm");

            if (phoneCode == "IP01") // iPhone 15 Pro
                return productName.Contains("15 pro") && !productName.Contains("max") && !productName.Contains("prm");

            if (phoneCode == "IP05") // iPhone 16 Pro Max
                return productName.Contains("16 pro max") || productName.Contains("16 prm");

            if (phoneCode == "IP17PM")
                return productName.Contains("17 pro max") || productName.Contains("17 prm");

            if (phoneCode == "IP18PM")
                return productName.Contains("18 pro max") || productName.Contains("18 prm");

            return false;
        }

        private static string? GetPhoneSlug(string? value)
        {
            if (string.IsNullOrWhiteSpace(value)) return null;

            var codeOrName = value.Trim();
            if (codeOrName.Equals("IPX01", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("iPhone X", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("iPhone 10", StringComparison.OrdinalIgnoreCase))
                return "iphone-x";
            if (codeOrName.Equals("IPXR", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("iPhone XR", StringComparison.OrdinalIgnoreCase))
                return "iphone-xr";
            if (codeOrName.Equals("IP11PM", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("11 Pro Max", StringComparison.OrdinalIgnoreCase))
                return "iphone-11-prm";
            if (codeOrName.Equals("IP11", StringComparison.OrdinalIgnoreCase) || codeOrName.Equals("IP1101", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("iPhone 11", StringComparison.OrdinalIgnoreCase))
                return "iphone-11";
            if (codeOrName.Equals("IP12PM", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("12 Pro Max", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("12 PRM", StringComparison.OrdinalIgnoreCase))
                return "iphone-12-prm";
            if (codeOrName.Equals("IP12", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("iPhone 12", StringComparison.OrdinalIgnoreCase))
                return "iphone-12";
            if (codeOrName.Equals("IP13PM", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("13 Pro Max", StringComparison.OrdinalIgnoreCase))
                return "iphone-13-prm";
            if (codeOrName.Equals("IP13", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("iPhone 13", StringComparison.OrdinalIgnoreCase))
                return "iphone-13";
            if (codeOrName.Equals("IP14PM", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("14 Pro Max", StringComparison.OrdinalIgnoreCase))
                return "iphone-14-prm";
            if (codeOrName.Equals("IP01", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("15 Pro", StringComparison.OrdinalIgnoreCase))
                return "iphone-15-pro";
            if (codeOrName.Equals("IP17PM", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("17 Pro Max", StringComparison.OrdinalIgnoreCase))
                return "iphone-17-prm";
            if (codeOrName.Equals("IP18PM", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("18 Pro Max", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("18 PRM", StringComparison.OrdinalIgnoreCase))
                return "iphone-18-prm";
            if (codeOrName.Equals("IP05", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("iPhone 16 Pro Max", StringComparison.OrdinalIgnoreCase))
                return "iphone-16-pro-max";
            if (codeOrName.Equals("IP01", StringComparison.OrdinalIgnoreCase) || codeOrName.Contains("iPhone 15 Pro", StringComparison.OrdinalIgnoreCase))
                return "iphone-15-pro";

            return null;
        }

        [HttpGet]
        public async Task<IActionResult> GetCompatibleCases(string deviceCode)
        {
            var phone = PhoneModel.DefaultPhones.FirstOrDefault(p =>
                p.DeviceCode.Equals(deviceCode, StringComparison.OrdinalIgnoreCase));
            if (phone == null)
            {
                return BadRequest(new { message = "Mã thiết bị không được hỗ trợ." });
            }

            var allCandidateCases = new List<Product>();
            try
            {
                var caseCategory = await _context.Categories
                    .FirstOrDefaultAsync(c => c.Name.Contains("Ốp") || c.Name.Contains("Case"));
                var caseCatId = caseCategory?.Id ?? 0;
                allCandidateCases = await _context.Products
                    .Include(p => p.Category)
                    .Where(p => (caseCatId > 0 && p.CategoryId == caseCatId)
                        || p.Name.Contains("Ốp")
                        || p.Name.Contains("Case"))
                    .OrderByDescending(p => p.Id)
                    .ToListAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[Cảnh báo DB] GetCompatibleCases fallback: {ex.Message}");
            }

            if (allCandidateCases.Count == 0)
            {
                allCandidateCases = new List<Product>
                {
                    new Product
                    {
                        Id = 1,
                        ProductCode = "IPX01",
                        Name = "Ốp Lưng iPhone X Chống Sốc Trong Suốt",
                        Price = 180000,
                        CompatibleDeviceCode = "IPX01",
                        MaterialType = "Silicone"
                    },
                    new Product
                    {
                        Id = 2,
                        ProductCode = "OL01",
                        Name = "Ốp Lưng MagSafe Chống Sốc Titan",
                        Price = 250000,
                        CompatibleDeviceCode = "IP01",
                        MaterialType = "Silicone"
                    },
                    new Product
                    {
                        Id = 3,
                        ProductCode = "IP05",
                        Name = "Ốp Lưng iPhone 16 Pro Max Armor",
                        Price = 450000,
                        CompatibleDeviceCode = "IP05",
                        MaterialType = "Silicone"
                    }
                };
            }

            // Chỉ lấy các ốp khớp chính xác với dòng điện thoại này
            var products = allCandidateCases
                .Where(p => IsCaseMatchingPhone(p, phone))
                .Select(p => new
                {
                    id = p.Id,
                    code = p.ProductCode,
                    title = p.Name,
                    price = p.Price,
                    textureUrl = p.CaseTexturePath ?? p.ImageUrl ?? string.Empty,
                    materialType = p.MaterialType,
                    modelUrl = p.Case3DModelPath ?? string.Empty,
                    compatibleDeviceCode = p.CompatibleDeviceCode ?? phone.DeviceCode
                })
                .ToList();

            return Json(products);
        }

        // POST: /TryOn3D/DetectPhoneModel
        [HttpPost]
        public async Task<IActionResult> DetectPhoneModel(IFormFile file, string source = "camera")
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest(new { success = false, message = "Vui lòng chọn hoặc chụp ảnh mặt lưng điện thoại." });
            }

            try
            {
                // Gọi sang Python AI Microservice (YOLO + ROCA 6DoF)
                var client = _httpClientFactory.CreateClient();
                client.Timeout = TimeSpan.FromSeconds(20);

                using var formContent = new MultipartFormDataContent();
                using var stream = file.OpenReadStream();
                formContent.Add(new StreamContent(stream), "file", file.FileName);
                var detectionSource = string.Equals(source, "upload", StringComparison.OrdinalIgnoreCase) ? "upload" : "camera";
                formContent.Add(new StringContent(detectionSource), "source");

                var response = await client.PostAsync("http://localhost:5001/api/detect-phone-model", formContent);
                var jsonStr = await response.Content.ReadAsStringAsync();

                if (!response.IsSuccessStatusCode)
                {
                    return StatusCode(StatusCodes.Status503ServiceUnavailable, new
                    {
                        success = false,
                        message = "AI Service chưa sẵn sàng hoặc không xử lý được ảnh. Hãy kiểm tra cửa sổ AI_Service."
                    });
                }

                var aiResult = JsonSerializer.Deserialize<AiDetectionResponse>(jsonStr, new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });
                if (aiResult == null)
                {
                    return StatusCode(StatusCodes.Status502BadGateway, new
                    {
                        success = false,
                        message = "AI Service trả về dữ liệu không hợp lệ."
                    });
                }

                if (aiResult.Success && aiResult.ModelRecognized)
                {
                    HttpContext.Session.SetString("UserPhoneModelSlug", aiResult.PhoneModelId);
                    HttpContext.Session.SetString("UserPhoneModelName", aiResult.PhoneModelName);
                }

                return Json(aiResult);
            }
            catch (HttpRequestException)
            {
                return StatusCode(StatusCodes.Status503ServiceUnavailable, new
                {
                    success = false,
                    message = "Không kết nối được AI Service ở cổng 5001. Hãy chạy AI_Service trước khi quét."
                });
            }
            catch (TaskCanceledException)
            {
                return StatusCode(StatusCodes.Status504GatewayTimeout, new
                {
                    success = false,
                    message = "AI xử lý ảnh quá thời gian chờ. Hãy thử ảnh nhỏ hơn hoặc kiểm tra AI Service."
                });
            }
            catch (JsonException)
            {
                return StatusCode(StatusCodes.Status502BadGateway, new
                {
                    success = false,
                    message = "AI Service trả về JSON không đọc được."
                });
            }
        }

        // POST: /TryOn3D/SaveSessionDevice
        [HttpPost]
        public IActionResult SaveSessionDevice([FromBody] SaveDeviceDto dto)
        {
            if (dto == null || string.IsNullOrEmpty(dto.PhoneModelSlug))
            {
                return BadRequest();
            }

            HttpContext.Session.SetString("UserPhoneModelSlug", dto.PhoneModelSlug);
            if (!string.IsNullOrEmpty(dto.PhoneModelName))
            {
                HttpContext.Session.SetString("UserPhoneModelName", dto.PhoneModelName);
            }

            return Json(new { success = true });
        }
    }

    public class SaveDeviceDto
    {
        public string PhoneModelSlug { get; set; } = string.Empty;
        public string? PhoneModelName { get; set; }
    }

    public class AiDetectionResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("phone_model_id")]
        public string PhoneModelId { get; set; } = string.Empty;

        [JsonPropertyName("phone_model_name")]
        public string PhoneModelName { get; set; } = string.Empty;

        [JsonPropertyName("model_recognized")]
        public bool ModelRecognized { get; set; }

        [JsonPropertyName("device_code")]
        public string DeviceCode { get; set; } = string.Empty;

        [JsonPropertyName("case_model_url")]
        public string CaseModelUrl { get; set; } = string.Empty;

        [JsonPropertyName("confidence")]
        public double Confidence { get; set; }

        [JsonPropertyName("bbox")]
        public int[]? Bbox { get; set; }

        [JsonPropertyName("pose_6dof")]
        public JsonElement? Pose6Dof { get; set; }

        [JsonPropertyName("message")]
        public string? Message { get; set; }
    }
}
